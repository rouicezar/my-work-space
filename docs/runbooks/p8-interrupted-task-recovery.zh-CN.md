# P8 中断任务恢复 — 手动验收 Runbook

Status: 与 P8-T06 配套；自动化部分已由 `scripts/record_task_recovery_evidence.py` 验证。

## 前置条件

- 已安装 product root，且 `state/task-metadata/` 中至少有一条任务元数据
- 本地 runtime 与 Herdr 可启停
- 使用 **原生工作台**（非 `--daily-workbench-preview`）

## 场景：中断的 blocked 任务

模拟：任务在 Herdr 报告 `blocked` 时中断（应用退出或 Herdr detach），重开后不得虚假标记为已完成。

### 步骤 A — 准备持久化元数据（开发者 / supervisor）

若尚无测试数据，可先写入一条 blocked 任务元数据（或通过 prior 任务流产生）。

### 步骤 B — 应用重开

1. 完全退出 Forma AI 原生工作台
2. 重新启动（DEBUG 默认 `ManifestOverview`）
3. 打开 **History** 侧栏

**预期：** 持久化任务出现在列表中（`readsPersistedHistory: true` 产品路径）。

### 步骤 C — Herdr detach（fail-closed）

1. 在 Settings → Local runtime **停止 runtime**（或确保 Herdr 不在线）
2. 在 History 点击 **Refresh reconcile**

**预期：** 所有任务 `runtime_state` / `display_outcome` 为 `unknown`；**Reclaim** 禁用；不得显示“已完成”。

### 步骤 D — Herdr reconnect（恢复真相）

1. **启动 runtime**，确认 Herdr 在线
2. 再次 **Refresh reconcile**

**预期：** 与 Herdr 一致的 blocked/recoverable 状态；`may_resume` 为 true 时 **Reclaim session** 可点。

### 步骤 E — 执行 reclaim

1. 点击 **Reclaim session**
2. 确认无报错；再次 refresh 后状态仍与 Herdr 一致

**预期：** 审计写入 `logs/audit/task-history-recovery.jsonl`（reclaim 事件）。

### 步骤 F — 记录证据

```bash
python3 scripts/record_task_recovery_evidence.py --root /absolute/product/root
```

在生成的 `evidence/recovery/recovery-YYYY-MM-DD.md` 中勾选 manual checklist 并填写 operator sign-off。

## 禁止项

- Preview UI 不得作为本场景验收依据
- metadata  alone 不得推断 completed / resumable
- revision 不匹配时不得允许 cancel/reclaim
