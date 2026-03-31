from __future__ import annotations

import click

from cit import __version__
from cit.commands.branch import branch
from cit.commands.checkout import checkout
from cit.commands.config import config
from cit.commands.log import log_command
from cit.commands.stash import stash
from cit.commands.status import status
from cit.core.lock import cit_lock
from cit.core.wal import recover_if_needed


ASCII_BANNER = r"""
░█████╗░██╗████████╗
██╔══██╗██║╚══██╔══╝
██║░░╚═╝██║░░░██║░░░
██║░░██╗██║░░░██║░░░
╚█████╔╝██║░░░██║░░░
░╚════╝░╚═╝░░░╚═╝░░░
""".strip("\n")

HELP_SUMMARY = "Git-style account switching for Claude Code."
HELP_DETAILS = (
    "Save reusable profiles, switch accounts cleanly, and confirm the active "
    "setup without digging through local files."
)
QUICK_START = (
    "Quick start:\n"
    "  cit status                     Inspect the active account and profile.\n"
    "  cit branch work --with-config  Save the current account as a reusable profile.\n"
    "  cit checkout office            Switch to a saved work profile.\n"
    "  cit log --today --stats        Review today's session usage and cost."
)


class CitHelpGroup(click.Group):
    def get_help(self, ctx: click.Context) -> str:
        base_help = super().get_help(ctx).strip()
        return "\n\n".join(
            [ASCII_BANNER, HELP_SUMMARY, HELP_DETAILS, base_help, QUICK_START]
        )


@click.group(
    cls=CitHelpGroup,
    name="cit",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version__, prog_name="cit")
def main() -> None:
    with cit_lock():
        recover_if_needed()


main.add_command(branch)
main.add_command(checkout)
main.add_command(status)
main.add_command(config)
main.add_command(stash)
main.add_command(log_command)


if __name__ == "__main__":
    main()
