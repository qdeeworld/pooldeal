from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from eth_account import Account
from eth_account.messages import encode_defunct
from flask import Flask, jsonify, render_template, request
from web3 import Web3

from .identity import tenant_for_members
from .obligation import obligation_digest, sign_record

BASE_SEPOLIA_CHAIN_ID = 84532
BASE_SEPOLIA_RPC = "https://sepolia.base.org"
BASE_SEPOLIA_EXPLORER = "https://sepolia.basescan.org"
POOLROUND_ADDRESS = "0xC998f3a0439b7365D3839A415168fF7A4FFAcd62"
USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
MERCHANT_ADDRESS = "0xbB568962CF24d4CeBBf5d48308aCdAE873B93202"

USDC_ABI = [
    {
        "type": "function",
        "name": "balanceOf",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "approve",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "type": "function",
        "name": "transfer",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
]

POOL_ABI = [
    {
        "type": "function",
        "name": "nextRoundId",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "createRound",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "obligationDigest", "type": "bytes32"},
            {"name": "merchant", "type": "address"},
            {"name": "amountA", "type": "uint96"},
            {"name": "amountB", "type": "uint96"},
            {"name": "deadline", "type": "uint64"},
        ],
        "outputs": [{"name": "roundId", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "approveRound",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "roundId", "type": "uint256"}],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "contribute",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "roundId", "type": "uint256"}],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "settle",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "roundId", "type": "uint256"}],
        "outputs": [],
    },
]


def _session_signature(private_key: str, session_id: str) -> str:
    return Account.sign_message(
        encode_defunct(text=f"PoolDeal session\n{session_id}"), private_key=private_key
    ).signature.hex()


class PreparedWallets:
    def __init__(self, member_a_key: str, member_b_key: str) -> None:
        self.a = Account.from_key(member_a_key)
        self.b = Account.from_key(member_b_key)
        self.members = [self.a.address.lower(), self.b.address.lower()]


class CliMemoryBridge:
    def __init__(self, db_path: Path, wallets: PreparedWallets) -> None:
        self.db_path = db_path
        self.wallets = wallets

    def _run(
        self,
        command: str,
        *,
        obligation_id: str,
        wallet: Any,
        extras: list[str] | None = None,
        db_path: Path | None = None,
        expect: int = 0,
    ) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        args = [
            sys.executable,
            "-m",
            "pooldeal.cli",
            command,
            "--db",
            str(db_path or self.db_path),
            "--members",
            *self.wallets.members,
            "--wallet",
            wallet.address,
            "--session-id",
            session_id,
            "--session-signature",
            _session_signature(wallet.key.hex(), session_id),
            "--obligation-id",
            obligation_id,
            *(extras or []),
        ]
        completed = subprocess.run(args, capture_output=True, text=True, check=False)
        if completed.returncode != expect:
            detail = completed.stdout.strip() or completed.stderr.strip()
            raise RuntimeError(detail or f"memory command exited {completed.returncode}")
        return json.loads(completed.stdout)

    def write(self, record: dict[str, Any]) -> dict[str, Any]:
        return self._run(
            "write",
            obligation_id=record["obligation_id"],
            wallet=self.wallets.a,
            extras=["--record", json.dumps(record, separators=(",", ":"))],
        )

    def recall(self, obligation_id: str) -> dict[str, Any]:
        return self._run("recall", obligation_id=obligation_id, wallet=self.wallets.b)

    def ablate(self, obligation_id: str) -> dict[str, Any]:
        empty_db = self.db_path.parent / f"ablation-{uuid.uuid4()}.db"
        return self._run(
            "recall",
            obligation_id=obligation_id,
            wallet=self.wallets.b,
            db_path=empty_db,
            expect=2,
        )

    def consume(self, obligation_id: str, settlement_tx: str) -> dict[str, Any]:
        return self._run(
            "consume",
            obligation_id=obligation_id,
            wallet=self.wallets.a,
            extras=["--settlement-tx", settlement_tx],
        )


class BaseSettler:
    def __init__(self, wallets: PreparedWallets, rpc_url: str = BASE_SEPOLIA_RPC) -> None:
        self.wallets = wallets
        self.web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
        self.usdc = self.web3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS), abi=USDC_ABI
        )
        self.pool = self.web3.eth.contract(
            address=Web3.to_checksum_address(POOLROUND_ADDRESS), abi=POOL_ABI
        )

    def _send(self, function: Any, account: Any) -> str:
        nonce = self.web3.eth.get_transaction_count(account.address, "pending")
        gas_price = self.web3.eth.gas_price
        base = {
            "from": account.address,
            "nonce": nonce,
            "chainId": BASE_SEPOLIA_CHAIN_ID,
            "gasPrice": gas_price,
        }
        gas = function.estimate_gas(base)
        transaction = function.build_transaction({**base, "gas": int(gas * 1.25)})
        signed = account.sign_transaction(transaction)
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=45)
        if receipt.status != 1:
            raise RuntimeError(f"Base transaction reverted: {tx_hash.hex()}")
        return tx_hash.hex()

    def settle(self, digest: str) -> dict[str, Any]:
        if self.web3.eth.chain_id != BASE_SEPOLIA_CHAIN_ID:
            raise RuntimeError("Base Sepolia RPC chain mismatch")
        receipts: list[dict[str, str]] = []
        needed_b = 750_000
        balance_b = self.usdc.functions.balanceOf(self.wallets.b.address).call()
        if balance_b < needed_b:
            tx_hash = self._send(
                self.usdc.functions.transfer(self.wallets.b.address, needed_b - balance_b),
                self.wallets.a,
            )
            receipts.append({"label": "Fund member B", "tx": tx_hash})

        round_id = self.pool.functions.nextRoundId().call()
        deadline = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        steps = [
            (
                "Create exact round",
                self.pool.functions.createRound(
                    bytes.fromhex(digest.removeprefix("0x")),
                    Web3.to_checksum_address(MERCHANT_ADDRESS),
                    250_000,
                    750_000,
                    deadline,
                ),
                self.wallets.a,
            ),
            ("Member A approves", self.pool.functions.approveRound(round_id), self.wallets.a),
            ("Member B approves", self.pool.functions.approveRound(round_id), self.wallets.b),
            (
                "Member A token approval",
                self.usdc.functions.approve(POOLROUND_ADDRESS, 250_000),
                self.wallets.a,
            ),
            (
                "Member B token approval",
                self.usdc.functions.approve(POOLROUND_ADDRESS, 750_000),
                self.wallets.b,
            ),
            ("Member A contributes 0.25", self.pool.functions.contribute(round_id), self.wallets.a),
            ("Member B contributes 0.75", self.pool.functions.contribute(round_id), self.wallets.b),
            ("Settle 1.00 USDC", self.pool.functions.settle(round_id), self.wallets.a),
        ]
        for label, function, account in steps:
            receipts.append({"label": label, "tx": self._send(function, account)})
        return {"round_id": round_id, "receipts": receipts, "settlement_tx": receipts[-1]["tx"]}


def create_app(
    *,
    db_path: str | Path | None = None,
    member_a_key: str | None = None,
    member_b_key: str | None = None,
) -> Flask:
    app = Flask(__name__)
    data_path = Path(db_path or os.environ.get("POOLDEAL_DB", ".data/pooldeal.db"))
    data_path.parent.mkdir(parents=True, exist_ok=True)
    key_a = member_a_key or os.environ.get("POOLDEAL_MEMBER_A_KEY")
    key_b = member_b_key or os.environ.get("POOLDEAL_MEMBER_B_KEY")
    wallets = PreparedWallets(key_a, key_b) if key_a and key_b else None
    bridge = CliMemoryBridge(data_path, wallets) if wallets else None
    lock = threading.Lock()
    state: dict[str, Any] = {"settlements": 0}

    def require_bridge() -> CliMemoryBridge:
        if not bridge or not wallets:
            raise RuntimeError("prepared validation wallets are unavailable")
        return bridge

    @app.errorhandler(Exception)
    def handle_error(error: Exception):
        return jsonify({"error": str(error)}), 400

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/status")
    def status():
        return jsonify(
            {
                "ready": wallets is not None,
                "server_pid": os.getpid(),
                "commit": os.environ.get("POOLDEAL_COMMIT", "local"),
                "network": "Base Sepolia",
                "contract": POOLROUND_ADDRESS,
                "members": wallets.members if wallets else [],
                "prepared_wallets": wallets is not None,
            }
        )

    @app.post("/api/write")
    def write_memory():
        memory = require_bridge()
        now = datetime.now(timezone.utc)
        obligation_id = f"web-credit-{uuid.uuid4()}"
        record: dict[str, Any] = {
            "schema_version": 1,
            "obligation_id": obligation_id,
            "group_id": tenant_for_members(wallets.members),
            "version": 1,
            "creditor_address": wallets.a.address.lower(),
            "debtor_address": wallets.b.address.lower(),
            "credit_minor": 25,
            "currency": "USDC",
            "reason_code": "prior_purchase_overpayment",
            "status": "active",
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(days=2)).isoformat(),
            "supersedes": None,
            "note": "Member A covered an extra $0.25 in the previous purchase.",
        }
        record["signatures"] = {
            wallets.a.address.lower(): sign_record(record, wallets.a.key.hex()),
            wallets.b.address.lower(): sign_record(record, wallets.b.key.hex()),
        }
        written = memory.write(record)
        state[obligation_id] = {"record": record, "write": written}
        return jsonify(
            {
                "obligation_id": obligation_id,
                "write": written,
                "meaning": record["note"],
                "signed_by": wallets.members,
            }
        )

    @app.post("/api/recall")
    def recall_memory():
        obligation_id = str((request.get_json(silent=True) or {}).get("obligation_id", ""))
        if obligation_id not in state:
            raise RuntimeError("unknown validation obligation")
        recalled = require_bridge().recall(obligation_id)
        state[obligation_id]["recall"] = recalled
        return jsonify(recalled)

    @app.post("/api/ablate")
    def ablate_memory():
        obligation_id = str((request.get_json(silent=True) or {}).get("obligation_id", ""))
        if obligation_id not in state:
            raise RuntimeError("unknown validation obligation")
        return jsonify(require_bridge().ablate(obligation_id))

    @app.post("/api/settle")
    def settle_round():
        obligation_id = str((request.get_json(silent=True) or {}).get("obligation_id", ""))
        entry = state.get(obligation_id)
        if not entry or "recall" not in entry:
            raise RuntimeError("recall the signed obligation before settlement")
        with lock:
            if state["settlements"] >= int(os.environ.get("POOLDEAL_MAX_SETTLEMENTS", "1")):
                raise RuntimeError("public validation settlement limit reached")
            digest = obligation_digest(entry["record"])
            result = BaseSettler(wallets).settle(digest)
            state["settlements"] += 1
            consumed = require_bridge().consume(obligation_id, result["settlement_tx"])
            return jsonify({**result, "consumed": consumed, "explorer": BASE_SEPOLIA_EXPLORER})

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8787")), debug=False)


if __name__ == "__main__":
    main()
