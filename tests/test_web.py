from pathlib import Path

from eth_account import Account

from pooldeal.web import create_app


def test_web_memory_journey_uses_fresh_processes(tmp_path: Path):
    a = Account.create()
    b = Account.create()
    app = create_app(
        db_path=tmp_path / "memory.db",
        member_a_key=a.key.hex(),
        member_b_key=b.key.hex(),
    )
    client = app.test_client()

    written = client.post("/api/write", json={})
    assert written.status_code == 200
    write_body = written.get_json()

    recalled = client.post(
        "/api/recall", json={"obligation_id": write_body["obligation_id"]}
    )
    assert recalled.status_code == 200
    recall_body = recalled.get_json()
    assert write_body["write"]["pid"] != recall_body["pid"]
    assert write_body["write"]["session_id"] != recall_body["session_id"]
    assert sorted(recall_body["flat_split"].values()) == [50, 50]
    assert sorted(recall_body["proposed_split"].values()) == [25, 75]

    ablated = client.post(
        "/api/ablate", json={"obligation_id": write_body["obligation_id"]}
    )
    assert ablated.status_code == 200
    assert ablated.get_json()["decision"] == "refuse"

