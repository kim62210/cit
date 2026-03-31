from __future__ import annotations

import click

from cit.commands.branch import branch
from cit.commands.checkout import checkout
from cit.commands.config import config
from cit.commands.log import log_command
from cit.commands.stash import stash
from cit.commands.status import status
from cit.core.lock import cit_lock
from cit.core.wal import recover_if_needed


@click.group()
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
