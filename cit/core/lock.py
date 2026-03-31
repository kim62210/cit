from __future__ import annotations

import fcntl
from contextlib import contextmanager
from typing import Iterator

from cit.core.paths import get_cit_home
from cit.core.state import ensure_cit_dirs


@contextmanager
def cit_lock() -> Iterator[None]:
    ensure_cit_dirs()
    lock_path = get_cit_home() / ".lock"
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
