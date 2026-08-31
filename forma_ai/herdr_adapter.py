"""Thin discovery boundary for the pinned Herdr runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from shutil import which
from typing import Callable

from .adapter_contract import AdapterIdentity, HealthEnvelope


ExecutableFinder = Callable[[str], str | None]
Clock = Callable[[], str]
Request = Callable[[str, dict[str, object]], dict[str, object]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class HerdrAvailability:
    identity: AdapterIdentity
    installed: bool
    executable_path: str | None
    health: HealthEnvelope


@dataclass(frozen=True)
class HerdrTask:
    task_id: str
    run_id: str
    workspace_id: str
    pane_id: str
    state: str
    revision: int


class HerdrAdapter:
    """Discover Herdr without mistaking executable presence for health."""

    def __init__(
        self,
        *,
        executable_finder: ExecutableFinder = which,
        clock: Clock = _utc_now,
        request: Request | None = None,
    ) -> None:
        self._executable_finder = executable_finder
        self._clock = clock
        self._request = request
        self._task_ids_by_run_id: dict[str, str] = {}

    def availability(self) -> HerdrAvailability:
        executable_path = self._executable_finder("herdr")
        installed = executable_path is not None

        identity = AdapterIdentity(
            adapter_id="forma.herdr",
            adapter_version="0.1.0",
            protocol_version="1",
            upstream_id="herdr",
            upstream_version="0.8.2",
        )
        health = HealthEnvelope(
            schema_version=1,
            status="unknown" if installed else "unavailable",
            reachable=False,
            ready=False,
            proof="binary_discovered_only" if installed else "binary_not_found",
            checked_at=self._clock(),
            reason_code=(
                "HERDR_HEALTH_NOT_PROBED" if installed else "HERDR_BINARY_NOT_FOUND"
            ),
        )
        return HerdrAvailability(
            identity=identity,
            installed=installed,
            executable_path=executable_path,
            health=health,
        )

    def spawn_task(
        self,
        *,
        task_id: str,
        correlation_id: str,
        agent_kind: str,
        working_directory: str,
    ) -> HerdrTask:
        response = self._send(
            "agent.start",
            {
                "task_id": task_id,
                "correlation_id": correlation_id,
                "agent_kind": agent_kind,
                "working_directory": working_directory,
            },
        )
        task = self._task_from_response(task_id=task_id, response=response)
        self._task_ids_by_run_id[task.run_id] = task.task_id
        return task

    def task_status(self, run_id: str) -> HerdrTask:
        task_id = self._task_ids_by_run_id[run_id]
        response = self._send("agent.get", {"run_id": run_id})
        return self._task_from_response(task_id=task_id, response=response)

    def _send(
        self, method: str, params: dict[str, object]
    ) -> dict[str, object]:
        if self._request is None:
            raise RuntimeError("Herdr request transport is not configured")
        return self._request(method, params)

    @staticmethod
    def _task_from_response(
        *, task_id: str, response: dict[str, object]
    ) -> HerdrTask:
        return HerdrTask(
            task_id=task_id,
            run_id=str(response["run_id"]),
            workspace_id=str(response["workspace_id"]),
            pane_id=str(response["pane_id"]),
            state=str(response["state"]),
            revision=int(response["revision"]),
        )
