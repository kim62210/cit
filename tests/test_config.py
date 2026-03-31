from __future__ import annotations

from cit.cli import main
from cit.core.state import set_active_profile


def test_config_sets_and_gets_profile_values(runner, env_paths):
    set_active_profile("work", None)

    set_result = runner.invoke(main, ["config", "model", "opus[1m]"])
    get_result = runner.invoke(main, ["config", "model"])

    assert set_result.exit_code == 0
    assert get_result.exit_code == 0
    assert "opus[1m]" in get_result.output
