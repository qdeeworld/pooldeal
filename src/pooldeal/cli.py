from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any

from .allocation import allocate_with_obligation
from .errors import ObligationRefused
from .identity import canonical_members, verify_member_session
from .memory import ObligationMemory


def _json_arg(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("expected a JSON object")
    return parsed


def _authenticate(args: argparse.Namespace) -> list[str]:
    members = list(canonical_members(args.members))
    if args.wallet.lower() not in members:
        raise ObligationRefused("requesting wallet is not a group member")
    verify_member_session(
        wallet_address=args.wallet,
        session_id=args.session_id,
        signature=args.session_signature,
    )
    return members


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pooldeal")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("write", "recall", "consume", "delete"):
        command = sub.add_parser(name)
        command.add_argument("--db", required=True)
        command.add_argument("--members", nargs=2, required=True)
        command.add_argument("--wallet", required=True)
        command.add_argument("--session-id", required=True)
        command.add_argument("--session-signature", required=True)
        command.add_argument("--obligation-id", required=True)
        if name == "write":
            command.add_argument("--record", type=_json_arg, required=True)
        if name == "recall":
            command.add_argument("--total-minor", type=int, default=100)
        if name == "consume":
            command.add_argument("--settlement-tx", required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        members = _authenticate(args)
        memory = ObligationMemory(args.db, members)
        if args.command == "write":
            memory.write(args.record)
            result = {"result": "written"}
        elif args.command == "recall":
            record = memory.recall(args.obligation_id)
            result = allocate_with_obligation(
                total_minor=args.total_minor, record=record, member_addresses=members
            )
        elif args.command == "consume":
            memory.consume(args.obligation_id, settlement_tx=args.settlement_tx)
            result = {"result": "consumed"}
        else:
            result = {"result": "deleted", "deleted": memory.delete(args.obligation_id)}
        result.update(
            {
                "pid": os.getpid(),
                "session_id": args.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        print(json.dumps(result, sort_keys=True))
    except ObligationRefused as exc:
        print(
            json.dumps(
                {
                    "decision": "refuse",
                    "reason": str(exc),
                    "pid": os.getpid(),
                    "session_id": args.session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                sort_keys=True,
            )
        )
        raise SystemExit(2)


if __name__ == "__main__":
    main()

