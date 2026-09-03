"""End-to-end workbook tool task runner for governed merge + HTML report proofs."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from forma_ai.herdr_tool_bridge import HerdrToolBridge
from forma_ai.tool_registry import ToolRegistry


WORKBOOK_PACKAGE_ID = "fixture-workbook-mcp"
FIXTURE_SHEETS = ("sheet_a.csv", "sheet_b.csv")


@dataclass(frozen=True)
class ToolE2EResult:
    correlation_id: str
    workspace_dir: Path
    sheet_a_path: Path
    sheet_b_path: Path
    merged_csv_path: Path
    report_html_path: Path
    audit_log_path: Path

    def to_dict(self) -> dict[str, object]:
        return {
            "correlation_id": self.correlation_id,
            "workspace_dir": str(self.workspace_dir),
            "sheet_a_path": str(self.sheet_a_path),
            "sheet_b_path": str(self.sheet_b_path),
            "merged_csv_path": str(self.merged_csv_path),
            "report_html_path": str(self.report_html_path),
            "audit_log_path": str(self.audit_log_path),
        }


class ToolE2ERunner:
    """Run a governed workbook merge and HTML report through ToolRouter."""

    def run_workbook_report(
        self,
        product_root: Path,
        workspace_dir: Path,
        correlation_id: str,
        repository_root: Path,
        *,
        catalog_path: Path | None = None,
        now: datetime | None = None,
    ) -> ToolE2EResult:
        _validate_roots(product_root, workspace_dir, repository_root)
        routing_catalog = catalog_path or (repository_root / "config/tool-routing.json")
        if not routing_catalog.is_absolute() or not routing_catalog.is_file():
            raise ValueError("tool routing catalog must be an existing absolute file")

        registry = ToolRegistry(
            product_root,
            catalog_path=repository_root / "config/tool-packages.json",
            repository_root=repository_root,
        )
        registry.install(WORKBOOK_PACKAGE_ID)

        fixture_dir = repository_root / "tests/fixtures/workbooks"
        sheet_a = workspace_dir / "sheet_a.csv"
        sheet_b = workspace_dir / "sheet_b.csv"
        merged_csv = workspace_dir / "merged.csv"
        report_html = workspace_dir / "report.html"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        for name, destination in zip(FIXTURE_SHEETS, (sheet_a, sheet_b), strict=True):
            source = fixture_dir / name
            if not source.is_file():
                raise FileNotFoundError(f"workbook fixture missing: {source}")
            shutil.copy2(source, destination)

        bridge = HerdrToolBridge(repository_root=repository_root)
        moment = now or datetime.now(timezone.utc)

        merge_artifact = bridge.call(
            product_root=product_root,
            correlation_id=correlation_id,
            capability_id="spreadsheet.merge",
            operation="merge_workbook",
            arguments={
                "input_a": str(sheet_a),
                "input_b": str(sheet_b),
                "output_path": str(merged_csv),
            },
            data_classes=frozenset({"tool_result"}),
            catalog_path=routing_catalog,
            workspace_dir=workspace_dir,
            now=moment,
        )
        if merge_artifact.is_error:
            raise RuntimeError(f"merge_workbook failed: {merge_artifact.text}")

        render_artifact = bridge.call(
            product_root=product_root,
            correlation_id=correlation_id,
            capability_id="report.render",
            operation="render_html",
            arguments={
                "input_path": str(merged_csv),
                "output_path": str(report_html),
                "title": "Workbook Report",
            },
            data_classes=frozenset({"tool_result"}),
            catalog_path=routing_catalog,
            workspace_dir=workspace_dir,
            now=moment,
        )
        if render_artifact.is_error:
            raise RuntimeError(f"render_html failed: {render_artifact.text}")

        audit_log = product_root / "logs/audit/tools.jsonl"
        return ToolE2EResult(
            correlation_id=correlation_id,
            workspace_dir=workspace_dir,
            sheet_a_path=sheet_a,
            sheet_b_path=sheet_b,
            merged_csv_path=merged_csv,
            report_html_path=report_html,
            audit_log_path=audit_log,
        )


def _validate_roots(product_root: Path, workspace_dir: Path, repository_root: Path) -> None:
    for label, path in (
        ("product root", product_root),
        ("workspace directory", workspace_dir),
        ("repository root", repository_root),
    ):
        if not path.is_absolute():
            raise ValueError(f"{label} must be absolute")
    resolved = product_root.resolve(strict=False)
    if resolved == Path("/") or resolved == Path.home() or product_root.is_symlink():
        raise ValueError("product root is unsafe")
    if not workspace_dir.is_dir() or workspace_dir.is_symlink():
        raise ValueError("workspace directory must be an existing directory")
