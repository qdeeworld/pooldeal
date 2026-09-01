from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from sibyl_memory_client import MemoryClient
from sibyl_memory_client.exceptions import NotFoundError

from .errors import ObligationRefused
from .identity import tenant_for_members
from .obligation import validate_record


class ObligationMemory:
    CATEGORY = "contribution_obligation"

    def __init__(self, db_path: str | Path, member_addresses: list[str]) -> None:
        self.members = member_addresses
        self.client = MemoryClient.local(
            db_path, tenant_id=tenant_for_members(member_addresses)
        )

    def write(self, record: dict[str, Any]) -> dict[str, Any]:
        validated = validate_record(record, member_addresses=self.members)
        return self.client.set_entity(
            self.CATEGORY, validated["obligation_id"], deepcopy(validated), status="active"
        )

    def recall(self, obligation_id: str) -> dict[str, Any]:
        try:
            entity = self.client.get_entity(self.CATEGORY, obligation_id)
        except NotFoundError as exc:
            raise ObligationRefused("required Sibyl memory is missing") from exc
        body = entity.get("body")
        if not isinstance(body, dict):
            raise ObligationRefused("remembered obligation is corrupted")
        return validate_record(body, member_addresses=self.members)

    def consume(self, obligation_id: str, *, settlement_tx: str) -> dict[str, Any]:
        record = self.recall(obligation_id)
        consumed = deepcopy(record)
        consumed["status"] = "consumed"
        consumed["settlement_tx"] = settlement_tx
        consumed["signatures"] = {}
        return self.client.set_entity(
            self.CATEGORY, obligation_id, consumed, status="consumed"
        )

    def delete(self, obligation_id: str) -> bool:
        return self.client.delete_entity(self.CATEGORY, obligation_id)

