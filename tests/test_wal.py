from __future__ import annotations

from cit.core.wal import clear_wal, read_wal, update_wal_step, write_wal


def test_wal_step_updates(env_paths):
    write_wal({"op": "checkout", "step": 0, "backup": {}})

    update_wal_step(2)

    assert read_wal()["step"] == 2
    clear_wal()
    assert read_wal() is None
