from __future__ import annotations

from cit.cli import main


def test_main_help_shows_branding_examples_and_descriptions(runner):
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "___ ___ _____" in result.output
    assert "Git-style account switching for Claude Code." in result.output
    assert "Quick start" in result.output
    assert "cit checkout office" in result.output
    assert "branch    Save, list, and remove named account profiles." in result.output


def test_branch_help_shows_clear_summary(runner):
    result = runner.invoke(main, ["branch", "--help"])

    assert result.exit_code == 0
    assert "Save, list, and remove named account profiles." in result.output
    assert "Include Claude settings and MCP files" in result.output
