from __future__ import annotations

from typing import Any

from .errors import ObligationRefused
from .obligation import obligation_digest, validate_record


def flat_split(total_minor: int) -> tuple[int, int]:
    if total_minor <= 0 or total_minor % 2:
        raise ObligationRefused("validation scenario requires a positive even total")
    return total_minor // 2, total_minor // 2


def allocate_with_obligation(
    *, total_minor: int, record: dict[str, Any], member_addresses: list[str]
) -> dict[str, Any]:
    validated = validate_record(record, member_addresses=member_addresses)
    flat_a, flat_b = flat_split(total_minor)
    members = tuple(sorted(address.lower() for address in member_addresses))
    credit = validated["credit_minor"]
    if credit > flat_a:
        raise ObligationRefused("credit exceeds safe allocation bound")
    shares = {members[0]: flat_a, members[1]: flat_b}
    creditor = validated["creditor_address"].lower()
    debtor = validated["debtor_address"].lower()
    shares[creditor] -= credit
    shares[debtor] += credit
    if min(shares.values()) < 0 or sum(shares.values()) != total_minor:
        raise ObligationRefused("allocation invariant failed")
    return {
        "decision": "history_aware_split",
        "total_minor": total_minor,
        "flat_split": {members[0]: flat_a, members[1]: flat_b},
        "proposed_split": shares,
        "obligation_digest": obligation_digest(validated),
    }

