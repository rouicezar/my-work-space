"""Product-owned process specifications for managed upstream components."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class ProcessPolicyError(ValueError):
    """Raised when a component process would violate product policy."""


@dataclass(frozen=True)
class ProcessSpec:
    executable: Path
    arguments: tuple[str, ...]
    environment: Mapping[str, str]
    secret_environment_names: tuple[str, ...]
    working_directory: Path
    inherit_parent_environment: bool = False

    def redacted(self) -> dict[str, object]:
        """Return an audit-safe representation that never contains secret values."""
        return {
            "executable": str(self.executable),
            "arguments": list(self.arguments),
            "environment": dict(self.environment),
            "secret_environment_names": list(self.secret_environment_names),
            "working_directory": str(self.working_directory),
            "inherit_parent_environment": self.inherit_parent_environment,
        }


def omlx_process_spec(
    *,
    executable: Path,
    app_support: Path,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> ProcessSpec:
    """Build a fail-closed oMLX launch contract.

    The caller must resolve ``OMLX_API_KEY`` from Keychain only when spawning the
    process. The value is deliberately absent from this serializable contract.
    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ProcessPolicyError("oMLX host must be a literal loopback address") from exc
    if not address.is_loopback:
        raise ProcessPolicyError("oMLX may only bind to a loopback address")
    if not 1024 <= port <= 65535:
        raise ProcessPolicyError("oMLX port must be between 1024 and 65535")
    if not executable.is_absolute() or not app_support.is_absolute():
        raise ProcessPolicyError("oMLX executable and app-support paths must be absolute")

    root = app_support / "components" / "omlx"
    isolated_home = root / "home"
    base_path = root / "data"
    model_path = root / "models"
    cache_path = root / "cache"
    runtime_path = root / "runtime"

    return ProcessSpec(
        executable=executable,
        arguments=(
            "serve",
            "--base-path",
            str(base_path),
            "--model-dir",
            str(model_path),
            "--host",
            host,
            "--port",
            str(port),
            "--no-hf-cache",
            "--no-cache",
            "--memory-guard",
            "safe",
        ),
        environment={
            "HOME": str(isolated_home),
            "XDG_CACHE_HOME": str(cache_path / "xdg"),
            "HF_HOME": str(cache_path / "huggingface"),
            "TMPDIR": str(runtime_path / "tmp"),
            "NO_PROXY": "127.0.0.1,localhost,::1",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        },
        secret_environment_names=("OMLX_API_KEY",),
        working_directory=runtime_path,
    )
