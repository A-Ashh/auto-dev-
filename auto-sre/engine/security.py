"""Security layer: command whitelisting and timeout enforcement."""

from __future__ import annotations

import asyncio
import functools
import signal
from typing import Any, Callable

# ── Whitelisted commands ────────────────────────────────────────────
ALLOWED_COMMANDS: set[str] = {
    "ls",
    "cat",
    "grep",
    "head",
    "tail",
    "echo",
    "pwd",
    "cd",
    "mv",
    "cp",
    "rm",
    "mkdir",
    "touch",
    "find",
    "ps",
    "kill",
    "systemctl",
    "npm",
    "pip",
    "write_file",
    "read_file",
    "netstat",
    "lsof",
    "node",
    "df",
    "du",
    "free",
    "top",
    "ss",
}

STEP_TIMEOUT_SECONDS: int = 5


class CommandNotAllowedError(Exception):
    """Raised when an agent submits a command outside the whitelist."""

    pass


class StepTimeoutError(Exception):
    """Raised when a step exceeds the allowed timeout."""

    pass


def validate_command(raw_command: str) -> str:
    """
    Extract the base command and verify it is whitelisted.

    Returns the raw command unchanged if valid.
    Raises CommandNotAllowedError if the base command is not allowed.
    """
    stripped = raw_command.strip()
    if not stripped:
        raise CommandNotAllowedError("Empty command is not allowed.")

    base = stripped.split()[0]
    # Strip path prefixes (e.g., /usr/bin/ls → ls)
    base = base.rsplit("/", maxsplit=1)[-1]

    if base not in ALLOWED_COMMANDS:
        raise CommandNotAllowedError(
            f"Command '{base}' is not in the allowed command set."
        )
    return stripped


def with_timeout(timeout: int = STEP_TIMEOUT_SECONDS):
    """Decorator that enforces a max execution time on sync functions."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import threading

            result: list[Any] = []
            error: list[Exception] = []

            def target() -> None:
                try:
                    result.append(fn(*args, **kwargs))
                except Exception as e:
                    error.append(e)

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=timeout)

            if thread.is_alive():
                raise StepTimeoutError(
                    f"Step execution timed out after {timeout} seconds."
                )
            if error:
                raise error[0]
            return result[0] if result else None

        return wrapper

    return decorator
