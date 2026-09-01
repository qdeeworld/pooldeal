from __future__ import annotations

import uuid

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import is_address

from .errors import ObligationRefused


def canonical_members(member_addresses: list[str]) -> tuple[str, str]:
    members = tuple(sorted(address.lower() for address in member_addresses))
    if len(members) != 2 or len(set(members)) != 2:
        raise ObligationRefused("exactly two distinct members are required")
    for address in members:
        if not is_address(address):
            raise ObligationRefused("invalid wallet address")
    return members


def tenant_for_members(member_addresses: list[str]) -> str:
    members = canonical_members(member_addresses)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "pooldeal:v1:" + ":".join(members)))


def verify_member_session(*, wallet_address: str, session_id: str, signature: str) -> None:
    message = encode_defunct(text=f"PoolDeal session\n{session_id}")
    try:
        recovered = Account.recover_message(message, signature=signature).lower()
    except Exception as exc:
        raise ObligationRefused("invalid session signature") from exc
    if recovered != wallet_address.lower():
        raise ObligationRefused("session signer does not match requesting wallet")
