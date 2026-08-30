"""Recoverable process ownership for product-managed local services."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence


class RuntimeManagerError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ProcessRecord:
    role: str
    pid: int
    executable: str
    command_sha256: str
    process_started_at: str
    log_path: str


@dataclass(frozen=True)
class RuntimeRecord:
    schema_version: int
    phase: str
    correlation_id: str
    omlx: ProcessRecord | None
    broker: ProcessRecord | None
    memory: ProcessRecord | None
    error: dict[str, str] | None
    revision: int
    created_at: str
    updated_at: str


class ProcessController(Protocol):
    def spawn(
        self,
        *,
        role: str,
        executable: Path,
        arguments: Sequence[str],
        environment: Mapping[str, str],
        working_directory: Path,
        log_path: Path,
    ) -> ProcessRecord: ...

    def matches(self, record: ProcessRecord) -> bool: ...
    def adopt(self, *, role: str, pid: int, command_prefix: str, log_path: Path) -> ProcessRecord: ...
    def terminate(self, record: ProcessRecord, timeout: float) -> None: ...


Probe = Callable[[], bool]


class SubprocessController:
    """Spawn detached process groups and verify identity before signalling them."""

    def spawn(
        self,
        *,
        role: str,
        executable: Path,
        arguments: Sequence[str],
        environment: Mapping[str, str],
        working_directory: Path,
        log_path: Path,
    ) -> ProcessRecord:
        if not executable.is_absolute() or not executable.is_file():
            raise RuntimeManagerError("EXECUTABLE_INVALID", str(executable))
        working_directory.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(log_path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        command = [str(executable), *arguments]
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                env=dict(environment),
                stdin=subprocess.DEVNULL,
                stdout=descriptor,
                stderr=subprocess.STDOUT,
                close_fds=True,
                start_new_session=True,
            )
        finally:
            os.close(descriptor)
        started = self._process_started_at(process.pid)
        observed_command = self._process_command(process.pid)
        if not started or not observed_command:
            raise RuntimeManagerError("PROCESS_IDENTITY_UNAVAILABLE", role)
        digest = hashlib.sha256(observed_command.encode("utf-8")).hexdigest()
        return ProcessRecord(role, process.pid, str(executable), digest, started, str(log_path))

    def matches(self, record: ProcessRecord) -> bool:
        started = self._process_started_at(record.pid)
        command = self._process_command(record.pid)
        return (
            bool(started)
            and started == record.process_started_at
            and bool(command)
            and hashlib.sha256(command.encode("utf-8")).hexdigest() == record.command_sha256
        )

    def adopt(self, *, role: str, pid: int, command_prefix: str, log_path: Path) -> ProcessRecord:
        started = self._process_started_at(pid)
        command = self._process_command(pid)
        if not started or not command.startswith(command_prefix):
            raise RuntimeManagerError("PROCESS_IDENTITY_MISMATCH", role)
        digest = hashlib.sha256(command.encode("utf-8")).hexdigest()
        return ProcessRecord(role, pid, command_prefix, digest, started, str(log_path))

    def terminate(self, record: ProcessRecord, timeout: float) -> None:
        if not self.matches(record):
            raise RuntimeManagerError("PID_IDENTITY_MISMATCH", record.role)
        try:
            os.killpg(record.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not self.matches(record):
                return
            time.sleep(0.05)
        if self.matches(record):
            os.killpg(record.pid, signal.SIGKILL)

    @staticmethod
    def _process_started_at(pid: int) -> str:
        result = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    @staticmethod
    def _process_command(pid: int) -> str:
        result = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""


class RuntimeManager:
    def __init__(
        self,
        root: Path,
        *,
        controller: ProcessController | None = None,
        wait_interval: float = 0.1,
    ):
        self.root = root
        self.state_path = root / "state/runtime/services.json"
        self.controller = controller or SubprocessController()
        self.wait_interval = wait_interval

    def load_optional(self) -> RuntimeRecord | None:
        if not self.state_path.exists():
            return None
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            data.setdefault("memory", None)
            for name in ("omlx", "broker", "memory"):
                if data.get(name):
                    data[name] = ProcessRecord(**data[name])
            return RuntimeRecord(**data)
        except (OSError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeManagerError("RUNTIME_STATE_INVALID", str(exc)) from exc

    def status(self) -> dict[str, object]:
        record = self.load_optional()
        if record is None:
            return {
                "phase": "stopped", "record": None, "omlx_alive": False,
                "broker_alive": False, "memory_alive": False,
            }
        omlx_alive = bool(record.omlx and self.controller.matches(record.omlx))
        broker_alive = bool(record.broker and self.controller.matches(record.broker))
        memory_alive = bool(record.memory and self.controller.matches(record.memory))
        effective = record.phase
        if record.phase == "running" and not (omlx_alive and broker_alive and memory_alive):
            effective = "degraded"
        return {
            "phase": effective,
            "record": asdict(record),
            "omlx_alive": omlx_alive,
            "broker_alive": broker_alive,
            "memory_alive": memory_alive,
        }

    def start(
        self,
        *,
        correlation_id: str,
        omlx: dict[str, object],
        broker: dict[str, object],
        omlx_probe: Probe,
        broker_probe: Probe,
        memory: dict[str, object],
        memory_probe: Probe,
        omlx_adopt: Callable[[], ProcessRecord] | None = None,
        timeout: float = 60.0,
    ) -> RuntimeRecord:
        existing = self.load_optional()
        if existing and existing.phase == "running":
            if (
                existing.omlx and existing.broker and existing.memory
                and self.controller.matches(existing.omlx)
                and self.controller.matches(existing.broker)
                and self.controller.matches(existing.memory)
            ):
                return existing
            raise RuntimeManagerError("RUNTIME_RECOVERY_REQUIRED", "recorded runtime is degraded")
        if existing and any(
            process and self.controller.matches(process)
            for process in (existing.memory, existing.broker, existing.omlx)
        ):
            raise RuntimeManagerError("RUNTIME_RECOVERY_REQUIRED", "managed process remains active")

        created = utc_now()
        record = RuntimeRecord(1, "starting", correlation_id, None, None, None, None, 1, created, created)
        self._persist(record)
        omlx_launcher: ProcessRecord | None = None
        omlx_record: ProcessRecord | None = None
        broker_record: ProcessRecord | None = None
        memory_record: ProcessRecord | None = None
        try:
            omlx_launcher = self._spawn_from_config("omlx", omlx)
            omlx_record = omlx_launcher
            record = self._advance(record, omlx=omlx_launcher)
            self._wait(omlx_probe, timeout, "OMLX_START_TIMEOUT")
            if omlx_adopt is not None:
                omlx_record = omlx_adopt()
                record = self._advance(record, omlx=omlx_record)
            broker_record = self._spawn_from_config("broker", broker)
            record = self._advance(record, broker=broker_record)
            self._wait(broker_probe, timeout, "BROKER_START_TIMEOUT")
            memory_record = self._spawn_from_config("memory", memory)
            record = self._advance(record, memory=memory_record)
            self._wait(memory_probe, timeout, "MEMORY_START_TIMEOUT")
            record = self._advance(record, phase="running")
            return record
        except Exception as exc:
            cleanup_error = None
            seen: set[int] = set()
            for process in (memory_record, broker_record, omlx_record, omlx_launcher):
                if process and process.pid in seen:
                    continue
                if process:
                    seen.add(process.pid)
                if process and self.controller.matches(process):
                    try:
                        self.controller.terminate(process, 5.0)
                    except Exception as cleanup:
                        cleanup_error = str(cleanup)
            code = exc.code if isinstance(exc, RuntimeManagerError) else "RUNTIME_START_FAILED"
            message = str(exc)
            if cleanup_error:
                message = f"{message}; cleanup: {cleanup_error}"
            self._persist(self._next(record, phase="failed", error={"code": code, "message": message}))
            raise

    def stop(self, timeout: float = 10.0) -> RuntimeRecord:
        record = self.load_optional()
        if record is None:
            now = utc_now()
            stopped = RuntimeRecord(1, "stopped", "none", None, None, None, None, 1, now, now)
            self._persist(stopped)
            return stopped
        for process in (record.memory, record.broker, record.omlx):
            if process and self.controller.matches(process):
                self.controller.terminate(process, timeout)
        stopped = self._next(record, phase="stopped", omlx=None, broker=None, memory=None, error=None)
        self._persist(stopped)
        return stopped

    def _spawn_from_config(self, role: str, config: dict[str, object]) -> ProcessRecord:
        return self.controller.spawn(
            role=role,
            executable=Path(str(config["executable"])),
            arguments=tuple(str(item) for item in config.get("arguments", ())),
            environment={str(key): str(value) for key, value in dict(config["environment"]).items()},
            working_directory=Path(str(config["working_directory"])),
            log_path=Path(str(config["log_path"])),
        )

    def _wait(self, probe: Probe, timeout: float, code: str) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if probe():
                return
            time.sleep(self.wait_interval)
        raise RuntimeManagerError(code, "service did not become ready before timeout")

    def _next(self, record: RuntimeRecord, **updates: object) -> RuntimeRecord:
        data = asdict(record)
        data.update(updates)
        for name in ("omlx", "broker", "memory"):
            value = data.get(name)
            if isinstance(value, dict):
                data[name] = ProcessRecord(**value)
        data["revision"] = record.revision + 1
        data["updated_at"] = utc_now()
        return RuntimeRecord(**data)

    def _advance(self, record: RuntimeRecord, **updates: object) -> RuntimeRecord:
        advanced = self._next(record, **updates)
        self._persist(advanced)
        return advanced

    def _persist(self, record: RuntimeRecord) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix=".runtime-", dir=self.state_path.parent)
        os.fchmod(descriptor, 0o600)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(asdict(record), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
