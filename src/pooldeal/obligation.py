from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from eth_account import Account
from eth_account.messages import encode_defunct

from .errors import ObligationRefused
from .identity import canonical_members, tenant_for_members

SIGNED_FIELDS = (
    "schema_version",
    "obligation_id",
    "group_id",
    "version",
    "creditor_address",
    "debtor_address",
    "credit_minor",
    "currency",
    "reason_code",
    "status",
    "issued_at",
    "expires_at",
    "supersedes",
)


def signed_payload(record: dict[str, Any]) -> dict[str, Any]:
    try:
        return {key: record[key] for key in SIGNED_FIELDS}
    except KeyError as exc:
        raise ObligationRefused(f"missing signed field: {exc.args[0]}") from exc


def canonical_message(record: dict[str, Any]) -> str:
    return json.dumps(signed_payload(record), sort_keys=True, separators=(",", ":"))


def obligation_digest(record: dict[str, Any]) -> str:
    return "0x" + hashlib.sha256(canonical_message(record).encode()).hexdigest()


def sign_record(record: dict[str, Any], private_key: str) -> str:
    return Account.sign_message(
        encode_defunct(text=canonical_message(record)), private_key=private_key
    ).signature.hex()


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObligationRefused("invalid obligation timestamp") from exc
    if parsed.tzinfo is None:
        raise ObligationRefused("obligation timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def validate_record(
    record: dict[str, Any], *, member_addresses: list[str], now: datetime | None = None
) -> dict[str, Any]:
    payload = signed_payload(record)
    members = canonical_members(member_addresses)
    creditor = str(payload["creditor_address"]).lower()
    debtor = str(payload["debtor_address"]).lower()
    if tuple(sorted((creditor, debtor))) != members:
        raise ObligationRefused("obligation members do not match authenticated group")
    if payload["group_id"] != tenant_for_members(list(members)):
        raise ObligationRefused("obligation group identifier does not match authenticated group")
    if payload["schema_version"] != 1 or payload["version"] < 1:
        raise ObligationRefused("unsupported obligation version")
    if payload["currency"] != "USDC" or payload["reason_code"] != "prior_purchase_overpayment":
        raise ObligationRefused("unsupported obligation semantics")
    if payload["status"] != "active":
        raise ObligationRefused("obligation is not active")
    credit = payload["credit_minor"]
    if isinstance(credit, bool) or not isinstance(credit, int) or credit <= 0:
        raise ObligationRefused("credit must be a positive integer")
    issued = _parse_time(payload["issued_at"])
    expires = _parse_time(payload["expires_at"])
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if issued > current + timedelta(minutes=5):
        raise ObligationRefused("obligation issue time is in the future")
    if expires <= issued or current > expires:
        raise ObligationRefused("obligation is stale")

    signatures = record.get("signatures")
    if not isinstance(signatures, dict):
        raise ObligationRefused("both member signatures are required")
    message = encode_defunct(text=canonical_message(record))
    for member in members:
        signature = signatures.get(member)
        if not signature:
            raise ObligationRefused("both member signatures are required")
        try:
            recovered = Account.recover_message(message, signature=signature).lower()
        except Exception as exc:
            raise ObligationRefused("invalid obligation signature") from exc
        if recovered != member:
            raise ObligationRefused("obligation signature does not match member")
    return record
