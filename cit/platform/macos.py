from __future__ import annotations

import json
import subprocess
from typing import Any

from cit.platform.base import CredentialStore


SERVICE_NAME = "Claude Code-credentials"
ACCOUNT_NAME = "whoami"


class MacOSKeychainStore(CredentialStore):
    def _run(
        self, *args: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["security", *args],
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

    def read(self) -> dict[str, Any]:
        result = self._run(
            "find-generic-password",
            "-s",
            SERVICE_NAME,
            "-a",
            ACCOUNT_NAME,
            "-w",
        )
        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip() or "Unable to read Keychain credentials"
            )
        return json.loads(result.stdout)

    def write(self, payload: dict[str, Any]) -> None:
        delete_result = self._run(
            "delete-generic-password",
            "-s",
            SERVICE_NAME,
            "-a",
            ACCOUNT_NAME,
        )
        if delete_result.returncode not in {0, 44}:
            raise RuntimeError(
                delete_result.stderr.strip() or "Unable to delete Keychain entry"
            )
        add_result = self._run(
            "add-generic-password",
            "-s",
            SERVICE_NAME,
            "-a",
            ACCOUNT_NAME,
            "-w",
            json.dumps(payload),
        )
        if add_result.returncode != 0:
            raise RuntimeError(
                add_result.stderr.strip() or "Unable to write Keychain entry"
            )

    def delete(self) -> None:
        result = self._run(
            "delete-generic-password",
            "-s",
            SERVICE_NAME,
            "-a",
            ACCOUNT_NAME,
        )
        if result.returncode not in {0, 44}:
            raise RuntimeError(
                result.stderr.strip() or "Unable to delete Keychain entry"
            )

    def validate_access(self) -> None:
        result = self._run(
            "find-generic-password",
            "-s",
            SERVICE_NAME,
            "-a",
            ACCOUNT_NAME,
        )
        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip() or "Keychain access is unavailable"
            )
