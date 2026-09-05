"""Thin discovery boundary for the pinned Herdr runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from shutil import which
import time
from typing import Callable

from .adapter_contract import AdapterIdentity, HealthEnvelope
from .herdr_transport import (
    HerdrProtocolError,
    HerdrRequestError,
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
    terminal_id: str
    state: str
    revision: int


@dataclass(frozen=True)
class HerdrTaskOutput:
    task_id: str
    run_id: str
    pane_id: str
    text: str
    truncated: bool


@dataclass(frozen=True)
class HerdrProcessInfo:
    pane_id: str
    shell_pid: int
    foreground_process_ids: tuple[int, ...]


@dataclass(frozen=True)
class HerdrCancellationClaim:
    revision: int
    terminal_id: str
    foreground_process_ids: tuple[int, ...]


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
        self._cancellation_claims_by_run_id: dict[str, HerdrCancellationClaim] = {}

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
        self,
        *,
        cwd: str | None = None,
        label: str | None = None,
        env: dict[str, str] | None = None,
    ) -> HerdrWorkspace:
        params: dict[str, object] = {}
        if cwd is not None:
            params["cwd"] = cwd
        if label is not None:
            params["label"] = label
        if env is not None:
            params["env"] = dict(env)
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
        env: dict[str, str] | None = None,
    ) -> HerdrPane:
        params: dict[str, object] = {"direction": direction}
        if target_pane_id is not None:
            params["target_pane_id"] = target_pane_id
        if cwd is not None:
            params["cwd"] = cwd
        if env is not None:
            params["env"] = dict(env)
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

    def spawn_task(
        self,
        *,
        task_id: str,
        correlation_id: str,
        agent_name: str,
        agent_kind: str,
        pane_id: str,
        startup_timeout_ms: int = 30_000,
    ) -> HerdrTask:
        deadline = time.monotonic() + min(startup_timeout_ms / 1000, 3.0)
        while True:
            try:
                response = self._send(
                    "agent.start",
                    {"name": agent_name, "kind": agent_kind, "pane_id": pane_id,
                     "timeout_ms": startup_timeout_ms},
                )
                break
            except HerdrRequestError as exc:
                # workspace.open can return before its shell is available. Only an
                # explicit pre-launch rejection is retryable; never replay timeouts.
                if exc.code != "agent_pane_busy" or time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)
        if response["type"] != "agent_started":
            raise ValueError("unexpected Herdr agent.start response")
        agent = response.get("agent")
        if not isinstance(agent, dict):
            raise ValueError("Herdr agent.start response is missing agent data")
        if agent.get("launch_pending"):
            detected = self._send(
                "events.wait",
                {
                    "match_event": {
                        "event": "pane_agent_status_changed",
                        "pane_id": pane_id,
                        "agent_status": "idle",
                    },
                    "timeout_ms": startup_timeout_ms,
                },
            )
            if detected.get("type") != "wait_matched":
                raise ValueError("unexpected Herdr agent detection wait response")
            refreshed = self._send("agent.get", {"target": pane_id})
            if refreshed.get("type") != "agent_info":
                raise ValueError("unexpected Herdr agent.get response after detection")
            agent = refreshed.get("agent")
        if not isinstance(agent, dict) or agent.get("launch_pending"):
            raise ValueError("Herdr agent.start did not detect a ready agent")
        run_id = f"herdr:{task_id}:{pane_id}"
        task = self._task_from_agent(
            task_id=task_id,
            run_id=run_id,
            agent=agent,
        )
        self._task_ids_by_run_id[task.run_id] = task.task_id
        self._pane_ids_by_run_id[task.run_id] = task.pane_id
        self._tasks_by_run_id[task.run_id] = task
        _ = correlation_id
        return task

    def reclaim_task(self, *, task: HerdrTask) -> HerdrTask:
        snapshot = self.snapshot()
        panes = [item for item in snapshot.panes if item.pane_id == task.pane_id]
        agents = [item for item in snapshot.agents if item.pane_id == task.pane_id]
        if len(panes) != 1 or len(agents) != 1:
            raise ValueError("Herdr task is missing or duplicated during reclamation")
        pane = panes[0]
        agent = agents[0]
        if (
            pane.workspace_id != task.workspace_id
            or pane.terminal_id != task.terminal_id
            or pane.revision != task.revision
            or self._task_state(pane.agent_status) != task.state
            or agent.workspace_id != task.workspace_id
            or agent.terminal_id != task.terminal_id
            or agent.revision != task.revision
            or self._task_state(agent.agent_status) != task.state
        ):
            raise ValueError("Herdr task identity changed during reclamation")
        response = self._send("agent.get", {"target": task.pane_id})
        if response.get("type") != "agent_info":
            raise ValueError("unexpected Herdr agent.get response")
        current = self._task_from_agent(
            task_id=task.task_id,
            run_id=task.run_id,
            agent=response.get("agent"),
        )
        if current != task:
            raise ValueError("Herdr task identity changed during reclamation")
        self._task_ids_by_run_id[task.run_id] = task.task_id
        self._pane_ids_by_run_id[task.run_id] = task.pane_id
        self._tasks_by_run_id[task.run_id] = task
        return task

    def prompt_task(
        self,
        *,
        run_id: str,
        text: str,
        timeout_ms: int | None = None,
    ) -> HerdrTask:
        if not text.strip() or "\x00" in text:
            raise ValueError("Herdr task prompt is invalid")
        task = self._claimed_task(run_id)
        params: dict[str, object] = {"target": task.pane_id, "text": text}
        if timeout_ms is not None:
            if timeout_ms <= 0:
                raise ValueError("Herdr task prompt timeout must be positive")
            params["wait"] = {
                "until": ["working", "blocked", "idle"],
                "timeout_ms": timeout_ms,
            }
        response = self._send("agent.prompt", params)
        if response.get("type") != "agent_prompted":
            raise ValueError("unexpected Herdr agent.prompt response")
        prompted = self._task_from_agent(
            task_id=task.task_id,
            run_id=run_id,
            agent=response.get("agent"),
        )
        if (
            prompted.workspace_id != task.workspace_id
            or prompted.pane_id != task.pane_id
            or prompted.terminal_id != task.terminal_id
            or prompted.revision < task.revision
        ):
            raise ValueError("Herdr task identity changed while prompting")
        self._tasks_by_run_id[run_id] = prompted
        return prompted

    def start_fresh_task(
        self,
        *,
        previous_task: HerdrTask,
        correlation_id: str,
        agent_name: str,
        agent_kind: str,
        pane_id: str,
        startup_timeout_ms: int = 30_000,
    ) -> HerdrTask:
        if pane_id == previous_task.pane_id:
            raise ValueError("Herdr fresh run requires a different pane")
        task = self.spawn_task(
            task_id=previous_task.task_id,
            correlation_id=correlation_id,
            agent_name=agent_name,
            agent_kind=agent_kind,
            pane_id=pane_id,
            startup_timeout_ms=startup_timeout_ms,
        )
        if (
            task.run_id == previous_task.run_id
            or task.pane_id == previous_task.pane_id
            or task.terminal_id == previous_task.terminal_id
        ):
            self._tasks_by_run_id.pop(task.run_id, None)
            self._task_ids_by_run_id.pop(task.run_id, None)
            self._pane_ids_by_run_id.pop(task.run_id, None)
            raise ValueError("Herdr fresh run did not create a new terminal identity")
        return task

    def task_status(self, run_id: str) -> HerdrTask:
        task = self._get_task(run_id)
        self._tasks_by_run_id[run_id] = task
        return task

    def wait_for_task(
        self,
        *,
        run_id: str,
        until: tuple[str, ...],
        timeout_ms: int | None,
    ) -> HerdrTask:
        task = self._claimed_task(run_id)
        response = self._send(
            "agent.wait",
            {
                "target": task.pane_id,
                "until": list(until),
                "timeout_ms": timeout_ms,
            },
        )
        if response.get("type") != "agent_info":
            raise ValueError("unexpected Herdr agent.wait response")
        waited = self._task_from_agent(
            task_id=task.task_id,
            run_id=run_id,
            agent=response.get("agent"),
        )
        if waited.pane_id != task.pane_id or waited.terminal_id != task.terminal_id:
            raise ValueError("Herdr task identity changed while waiting")
        self._tasks_by_run_id[run_id] = waited
        return waited

    def read_task_output(
        self,
        *,
        run_id: str,
        source: str,
        lines: int,
    ) -> HerdrTaskOutput:
        if not 1 <= lines <= 200:
            raise ValueError("Herdr task output lines must be between 1 and 200")
        task = self._claimed_task(run_id)
        response = self._send(
            "agent.read",
            {
                "target": task.pane_id,
                "source": source,
                "lines": lines,
                "format": "text",
                "strip_ansi": True,
            },
        )
        if response.get("type") != "pane_read":
            raise ValueError("unexpected Herdr agent.read response")
        read = response.get("read")
        if not isinstance(read, dict):
            raise ValueError("Herdr agent.read response is missing read data")
        if read.get("pane_id") != task.pane_id:
            raise ValueError("Herdr agent.read returned a different pane")
        text = read.get("text")
        truncated = read.get("truncated")
        if not isinstance(text, str) or not isinstance(truncated, bool):
            raise ValueError("Herdr agent.read response has invalid output data")
        return HerdrTaskOutput(
            task_id=task.task_id,
            run_id=run_id,
            pane_id=task.pane_id,
            text=text,
            truncated=truncated,
        )

    def task_process_info(self, *, run_id: str) -> HerdrProcessInfo:
        task = self._claimed_task(run_id)
        return self._process_info(task.pane_id)

    def cancel_task(
        self,
        *,
        run_id: str,
        correlation_id: str,
        expected_revision: int,
    ) -> HerdrLifecycleResult:
        task, process_info = self._reconcile_task(
            run_id=run_id,
            expected_revision=expected_revision,
        )
        response = self._send(
            "pane.send_keys",
            {"pane_id": task.pane_id, "keys": ["ctrl+c"]},
        )
        if response.get("type") != "ok":
            raise ValueError("unexpected Herdr pane.send_keys response")
        self._tasks_by_run_id[run_id] = task
        self._cancellation_claims_by_run_id[run_id] = HerdrCancellationClaim(
            revision=expected_revision,
            terminal_id=task.terminal_id,
            foreground_process_ids=process_info.foreground_process_ids,
        )
        _ = correlation_id
        return HerdrLifecycleResult(
            task_id=task.task_id,
            run_id=run_id,
            action="graceful_interrupt",
            state="cancel_requested",
            revision=expected_revision,
        )

    def force_cancel_task(
        self,
        *,
        run_id: str,
        correlation_id: str,
        expected_revision: int,
        force_confirmed: bool,
    ) -> HerdrLifecycleResult:
        if not force_confirmed:
            raise ValueError("Herdr force cancellation requires explicit confirmation")
        claim = self._cancellation_claims_by_run_id.get(run_id)
        if claim is None or claim.revision != expected_revision:
            raise ValueError("Herdr force cancellation requires a matching graceful claim")
        task, process_info = self._reconcile_task(
            run_id=run_id,
            expected_revision=expected_revision,
        )
        if (
            task.terminal_id != claim.terminal_id
            or process_info.foreground_process_ids != claim.foreground_process_ids
        ):
            raise ValueError("Herdr task identity changed before force cancellation")
        response = self._send("pane.close", {"pane_id": task.pane_id})
        if response.get("type") != "ok":
            raise ValueError("unexpected Herdr pane.close response")
        try:
            self._send("agent.get", {"target": task.pane_id})
        except HerdrRequestError as exc:
            if exc.code != "agent_not_found":
                raise
        else:
            raise ValueError("Herdr pane still contains an agent after force cancellation")
        self._cancellation_claims_by_run_id.pop(run_id, None)
        self._tasks_by_run_id.pop(run_id, None)
        self._task_ids_by_run_id.pop(run_id, None)
        self._pane_ids_by_run_id.pop(run_id, None)
        _ = correlation_id
        return HerdrLifecycleResult(
            task_id=task.task_id,
            run_id=run_id,
            action="force_close",
            state="force_closed",
            revision=expected_revision,
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

    def _claimed_task(self, run_id: str) -> HerdrTask:
        task = self._tasks_by_run_id.get(run_id)
        if task is None:
            raise ValueError("Herdr task is not claimed")
        return task

    def _get_task(self, run_id: str) -> HerdrTask:
        known = self._claimed_task(run_id)
        response = self._send("agent.get", {"target": known.pane_id})
        if response.get("type") != "agent_info":
            raise ValueError("unexpected Herdr agent.get response")
        current = self._task_from_agent(
            task_id=known.task_id,
            run_id=run_id,
            agent=response.get("agent"),
        )
        if (
            current.workspace_id != known.workspace_id
            or current.pane_id != known.pane_id
            or current.terminal_id != known.terminal_id
        ):
            raise ValueError("Herdr task identity changed")
        return current

    def _process_info(self, pane_id: str) -> HerdrProcessInfo:
        response = self._send("pane.process_info", {"pane_id": pane_id})
        if response.get("type") != "pane_process_info":
            raise ValueError("unexpected Herdr pane.process_info response")
        process_info = response.get("process_info")
        if not isinstance(process_info, dict):
            raise ValueError("Herdr pane.process_info response is missing process data")
        if process_info.get("pane_id") != pane_id:
            raise ValueError("Herdr pane.process_info returned a different pane")
        shell_pid = process_info.get("shell_pid")
        processes = process_info.get("foreground_processes")
        if type(shell_pid) is not int or not isinstance(processes, list):
            raise ValueError("Herdr pane.process_info response has invalid process data")
        process_ids: list[int] = []
        for process in processes:
            if not isinstance(process, dict) or type(process.get("pid")) is not int:
                raise ValueError("Herdr pane.process_info response has invalid process data")
            process_ids.append(process["pid"])
        return HerdrProcessInfo(
            pane_id=pane_id,
            shell_pid=shell_pid,
            foreground_process_ids=tuple(sorted(process_ids)),
        )

    def _reconcile_task(
        self,
        *,
        run_id: str,
        expected_revision: int,
    ) -> tuple[HerdrTask, HerdrProcessInfo]:
        claimed = self._claimed_task(run_id)
        if claimed.revision != expected_revision:
            raise ValueError("Herdr task revision changed before cancel")
        current = self._get_task(run_id)
        if (
            current.pane_id != claimed.pane_id
            or current.terminal_id != claimed.terminal_id
            or current.revision != expected_revision
        ):
            raise ValueError("Herdr task identity changed before cancel")
        process_info = self._process_info(current.pane_id)
        if not process_info.foreground_process_ids:
            raise ValueError("Herdr task has no foreground process to cancel")
        return current, process_info

    def _send(
        self, method: str, params: dict[str, object]
    ) -> dict[str, object]:
        if self._request is None:
            raise RuntimeError("Herdr request transport is not configured")
        return self._request(method, params)

    @staticmethod
    def _task_state(agent_status: str) -> str:
        return {
            "unknown": "starting",
            "working": "running",
            "idle": "running",
            "blocked": "blocked",
            "done": "succeeded",
        }.get(agent_status, "unknown")

    @staticmethod
    def _task_from_agent(
        *, task_id: str, run_id: str, agent: object
    ) -> HerdrTask:
        if not isinstance(agent, dict):
            raise ValueError("Herdr response is missing agent data")
        state = HerdrAdapter._task_state(str(agent["agent_status"]))
        return HerdrTask(
            task_id=task_id,
            run_id=run_id,
            workspace_id=str(agent["workspace_id"]),
            pane_id=str(agent["pane_id"]),
            terminal_id=str(agent["terminal_id"]),
            state=state,
            revision=int(agent["revision"]),
        )
