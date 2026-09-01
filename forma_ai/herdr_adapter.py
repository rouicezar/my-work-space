"""Thin discovery boundary for the pinned Herdr runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from shutil import which
from typing import Callable

from .adapter_contract import AdapterIdentity, HealthEnvelope
from .herdr_transport import (
    HerdrProtocolError,
    HerdrTransportError,
    validate_pong,
)


ExecutableFinder = Callable[[str], str | None]
Clock = Callable[[], str]
Request = Callable[[str, dict[str, object]], dict[str, object]]
Probe = Callable[[], dict[str, object]]


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


@dataclass(frozen=True)
class HerdrLifecycleResult:
    task_id: str
    run_id: str
    action: str
    state: str
    revision: int


@dataclass(frozen=True)
class HerdrWorkspace:
    workspace_id: str
    root_pane_id: str


@dataclass(frozen=True)
class HerdrPane:
    pane_id: str
    workspace_id: str


@dataclass(frozen=True)
class HerdrSessionWorkspace:
    workspace_id: str
    number: int
    label: str
    focused: bool
    pane_count: int
    tab_count: int
    active_tab_id: str
    agent_status: str


@dataclass(frozen=True)
class HerdrSessionTab:
    tab_id: str
    workspace_id: str
    number: int
    label: str
    focused: bool
    pane_count: int
    agent_status: str


@dataclass(frozen=True)
class HerdrSessionPane:
    pane_id: str
    terminal_id: str
    workspace_id: str
    tab_id: str
    focused: bool
    agent_status: str
    revision: int


@dataclass(frozen=True)
class HerdrSessionAgent:
    terminal_id: str
    agent_status: str
    workspace_id: str
    tab_id: str
    pane_id: str
    focused: bool
    revision: int


@dataclass(frozen=True)
class HerdrSessionSnapshot:
    version: str
    protocol: int
    workspaces: tuple[HerdrSessionWorkspace, ...]
    tabs: tuple[HerdrSessionTab, ...]
    panes: tuple[HerdrSessionPane, ...]
    agents: tuple[HerdrSessionAgent, ...]
    layouts: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class HerdrSessionEvent:
    kind: str
    data: dict[str, object]


class HerdrAdapter:
    """Discover Herdr without mistaking executable presence for health."""

    def __init__(
        self,
        *,
        executable_finder: ExecutableFinder = which,
        clock: Clock = _utc_now,
        request: Request | None = None,
        probe: Probe | None = None,
    ) -> None:
        self._executable_finder = executable_finder
        self._clock = clock
        self._request = request
        self._probe = probe
        self._task_ids_by_run_id: dict[str, str] = {}
        self._pane_ids_by_run_id: dict[str, str] = {}
        self._tasks_by_run_id: dict[str, HerdrTask] = {}

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
        if self._probe is None:
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
        else:
            health = self._probe_health()
        return HerdrAvailability(
            identity=identity,
            installed=installed,
            executable_path=executable_path,
            health=health,
        )

    def _probe_health(self) -> HealthEnvelope:
        try:
            pong = self._probe()
            validate_pong(pong)
        except HerdrProtocolError:
            return HealthEnvelope(
                schema_version=1,
                status="incompatible",
                reachable=True,
                ready=False,
                proof="protocol_mismatch",
                checked_at=self._clock(),
                reason_code="HERDR_PROTOCOL_INCOMPATIBLE",
            )
        except (HerdrTransportError, OSError):
            return HealthEnvelope(
                schema_version=1,
                status="unreachable",
                reachable=False,
                ready=False,
                proof="socket_unreachable",
                checked_at=self._clock(),
                reason_code="HERDR_SOCKET_UNREACHABLE",
            )
        return HealthEnvelope(
            schema_version=1,
            status="ready",
            reachable=True,
            ready=True,
            proof="ping_pong_verified",
            checked_at=self._clock(),
            reason_code="",
        )

    def open_workspace(
        self, *, cwd: str | None = None, label: str | None = None
    ) -> HerdrWorkspace:
        params: dict[str, object] = {}
        if cwd is not None:
            params["cwd"] = cwd
        if label is not None:
            params["label"] = label
        response = self._send("workspace.create", params)
        if response["type"] != "workspace_created":
            raise ValueError("unexpected Herdr workspace.create response")
        workspace = response["workspace"]
        root_pane = response["root_pane"]
        if not isinstance(workspace, dict) or not isinstance(root_pane, dict):
            raise ValueError("Herdr response is missing workspace or root pane data")
        return HerdrWorkspace(
            workspace_id=str(workspace["workspace_id"]),
            root_pane_id=str(root_pane["pane_id"]),
        )

    def open_pane(
        self,
        *,
        direction: str,
        target_pane_id: str | None = None,
        cwd: str | None = None,
    ) -> HerdrPane:
        params: dict[str, object] = {"direction": direction}
        if target_pane_id is not None:
            params["target_pane_id"] = target_pane_id
        if cwd is not None:
            params["cwd"] = cwd
        response = self._send("pane.split", params)
        if response["type"] != "pane_info":
            raise ValueError("unexpected Herdr pane.split response")
        pane = response["pane"]
        if not isinstance(pane, dict):
            raise ValueError("Herdr response is missing pane data")
        return HerdrPane(
            pane_id=str(pane["pane_id"]),
            workspace_id=str(pane["workspace_id"]),
        )

    def spawn_reported_task(
        self,
        *,
        task_id: str,
        correlation_id: str,
        agent_name: str,
        pane_id: str,
        command: str,
    ) -> HerdrTask:
        sent = self._send("pane.send_text", {"pane_id": pane_id, "text": command})
        if sent["type"] != "ok":
            raise ValueError("unexpected Herdr pane.send_text response")
        reported = self._send(
            "pane.report_agent",
            {
                "pane_id": pane_id,
                "source": "forma-fixture",
                "agent": agent_name,
                "state": "working",
            },
        )
        if reported["type"] != "ok":
            raise ValueError("unexpected Herdr pane.report_agent response")
        response = self._send("agent.get", {"target": pane_id})
        if response["type"] != "agent_info":
            raise ValueError("unexpected Herdr agent.get response")
        run_id = f"herdr:{task_id}:{pane_id}"
        task = self._task_from_agent(
            task_id=task_id,
            run_id=run_id,
            agent=response["agent"],
        )
        self._task_ids_by_run_id[task.run_id] = task.task_id
        self._pane_ids_by_run_id[task.run_id] = task.pane_id
        self._tasks_by_run_id[task.run_id] = task
        _ = correlation_id
        return task

    def spawn_task(
        self,
        *,
        task_id: str,
        correlation_id: str,
        agent_name: str,
        agent_kind: str,
        pane_id: str,
    ) -> HerdrTask:
        response = self._send(
            "agent.start",
            {
                "name": agent_name,
                "kind": agent_kind,
                "pane_id": pane_id,
            },
        )
        if response["type"] != "agent_started":
            raise ValueError("unexpected Herdr agent.start response")
        run_id = f"herdr:{task_id}:{pane_id}"
        task = self._task_from_agent(
            task_id=task_id,
            run_id=run_id,
            agent=response["agent"],
        )
        self._task_ids_by_run_id[task.run_id] = task.task_id
        self._pane_ids_by_run_id[task.run_id] = task.pane_id
        self._tasks_by_run_id[task.run_id] = task
        _ = correlation_id
        return task

    def task_status(self, run_id: str) -> HerdrTask:
        task_id = self._task_ids_by_run_id[run_id]
        pane_id = self._pane_ids_by_run_id[run_id]
        response = self._send("agent.get", {"target": pane_id})
        if response["type"] != "agent_info":
            raise ValueError("unexpected Herdr agent.get response")
        task = self._task_from_agent(
            task_id=task_id,
            run_id=run_id,
            agent=response["agent"],
        )
        self._tasks_by_run_id[run_id] = task
        return task

    def cancel_task(
        self,
        *,
        run_id: str,
        correlation_id: str,
        expected_revision: int,
    ) -> HerdrLifecycleResult:
        task = self._tasks_by_run_id[run_id]
        if task.revision != expected_revision:
            raise ValueError("Herdr task revision changed before cancel")
        response = self._send(
            "pane.send_keys",
            {"pane_id": task.pane_id, "keys": ["ctrl+c"]},
        )
        if response["type"] != "ok":
            raise ValueError("unexpected Herdr pane.send_keys response")
        _ = correlation_id
        return HerdrLifecycleResult(
            task_id=task.task_id,
            run_id=run_id,
            action="graceful_interrupt",
            state="cancel_requested",
            revision=expected_revision,
        )

    def resume_task(
        self,
        *,
        run_id: str,
        correlation_id: str,
        expected_revision: int,
        native_session_ref: dict[str, str],
        agent_name: str,
        agent_kind: str,
    ) -> HerdrLifecycleResult:
        task_id = self._task_ids_by_run_id[run_id]
        pane_id = self._pane_ids_by_run_id[run_id]
        current = self._send("agent.get", {"target": pane_id})
        if current["type"] != "agent_info":
            raise ValueError("unexpected Herdr agent.get response")
        current_agent = current["agent"]
        if not isinstance(current_agent, dict):
            raise ValueError("Herdr response is missing agent data")
        if int(current_agent["revision"]) != expected_revision:
            raise ValueError("Herdr task revision changed before resume")
        if current_agent.get("agent_session") != native_session_ref:
            raise ValueError("Herdr native session reference changed before resume")

        restarted = self._send(
            "agent.start",
            {"name": agent_name, "kind": agent_kind, "pane_id": pane_id},
        )
        if restarted["type"] != "agent_started":
            raise ValueError("unexpected Herdr agent.start response")
        task = self._task_from_agent(
            task_id=task_id,
            run_id=run_id,
            agent=restarted["agent"],
        )
        self._tasks_by_run_id[run_id] = task
        _ = correlation_id
        return HerdrLifecycleResult(
            task_id=task_id,
            run_id=run_id,
            action="native_resume",
            state=task.state,
            revision=task.revision,
        )

    def snapshot(self) -> HerdrSessionSnapshot:
        response = self._send("session.snapshot", {})
        if response.get("type") != "session_snapshot":
            raise ValueError("unexpected Herdr session.snapshot response")
        raw = response.get("snapshot")
        if not isinstance(raw, dict):
            raise ValueError("Herdr response is missing snapshot data")
        return HerdrSessionSnapshot(
            version=str(raw["version"]),
            protocol=int(raw["protocol"]),
            workspaces=tuple(
                HerdrSessionWorkspace(
                    workspace_id=str(item["workspace_id"]),
                    number=int(item["number"]),
                    label=str(item["label"]),
                    focused=bool(item["focused"]),
                    pane_count=int(item["pane_count"]),
                    tab_count=int(item["tab_count"]),
                    active_tab_id=str(item["active_tab_id"]),
                    agent_status=str(item["agent_status"]),
                )
                for item in raw["workspaces"]
            ),
            tabs=tuple(
                HerdrSessionTab(
                    tab_id=str(item["tab_id"]),
                    workspace_id=str(item["workspace_id"]),
                    number=int(item["number"]),
                    label=str(item["label"]),
                    focused=bool(item["focused"]),
                    pane_count=int(item["pane_count"]),
                    agent_status=str(item["agent_status"]),
                )
                for item in raw["tabs"]
            ),
            panes=tuple(
                HerdrSessionPane(
                    pane_id=str(item["pane_id"]),
                    terminal_id=str(item["terminal_id"]),
                    workspace_id=str(item["workspace_id"]),
                    tab_id=str(item["tab_id"]),
                    focused=bool(item["focused"]),
                    agent_status=str(item["agent_status"]),
                    revision=int(item["revision"]),
                )
                for item in raw["panes"]
            ),
            agents=tuple(
                HerdrSessionAgent(
                    terminal_id=str(item["terminal_id"]),
                    agent_status=str(item["agent_status"]),
                    workspace_id=str(item["workspace_id"]),
                    tab_id=str(item["tab_id"]),
                    pane_id=str(item["pane_id"]),
                    focused=bool(item["focused"]),
                    revision=int(item["revision"]),
                )
                for item in raw["agents"]
            ),
            layouts=tuple(
                item for item in raw["layouts"] if isinstance(item, dict)
            ),
        )

    def wait_for_event(
        self,
        *,
        match_event: dict[str, object],
        timeout_ms: int | None,
    ) -> HerdrSessionEvent:
        response = self._send(
            "events.wait",
            {"match_event": match_event, "timeout_ms": timeout_ms},
        )
        if response.get("type") != "wait_matched":
            raise ValueError("unexpected Herdr events.wait response")
        event = response.get("event")
        if not isinstance(event, dict):
            raise ValueError("Herdr response is missing waited event data")
        data = event.get("data")
        if not isinstance(data, dict):
            raise ValueError("Herdr waited event is missing event data")
        return HerdrSessionEvent(kind=str(event["event"]), data=dict(data))

    def _send(
        self, method: str, params: dict[str, object]
    ) -> dict[str, object]:
        if self._request is None:
            raise RuntimeError("Herdr request transport is not configured")
        return self._request(method, params)

    @staticmethod
    def _task_from_agent(
        *, task_id: str, run_id: str, agent: object
    ) -> HerdrTask:
        if not isinstance(agent, dict):
            raise ValueError("Herdr response is missing agent data")
        state = {
            "unknown": "starting",
            "working": "running",
            "idle": "running",
            "blocked": "blocked",
            "done": "succeeded",
        }.get(str(agent["agent_status"]), "unknown")
        return HerdrTask(
            task_id=task_id,
            run_id=run_id,
            workspace_id=str(agent["workspace_id"]),
            pane_id=str(agent["pane_id"]),
            state=state,
            revision=int(agent["revision"]),
        )
