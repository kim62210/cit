from __future__ import annotations

import fcntl
import time
from contextlib import contextmanager
from typing import Iterator

from cit.core.paths import get_cit_home
from cit.core.state import ensure_cit_dirs


class LockAcquisitionError(RuntimeError):
    pass


class LockTimeoutError(LockAcquisitionError):
    pass


DEFAULT_TIMEOUT = 5.0
POLL_INTERVAL = 0.1


@contextmanager
def cit_lock(timeout: float = DEFAULT_TIMEOUT) -> Iterator[None]:
    ensure_cit_dirs()
    lock_path = get_cit_home() / ".lock"
    with lock_path.open("w") as lock_file:
        fd = lock_file.fileno()
        start = time.monotonic()
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                elapsed = time.monotonic() - start
                if timeout == 0 or elapsed >= timeout:
                    raise LockTimeoutError(
                        f"Could not acquire lock within {timeout:.1f}s. "
                        "Another cit process may be running. "
                        "Use 'cit doctor' to check lock status."
                    )
                time.sleep(POLL_INTERVAL)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)


def is_lock_held() -> bool:
    ensure_cit_dirs()
    lock_path = get_cit_home() / ".lock"
    if not lock_path.exists():
        return False
    try:
        with lock_path.open("w") as lock_file:
            fd = lock_file.fileno()
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            return False
    except BlockingIOError:
        return True
