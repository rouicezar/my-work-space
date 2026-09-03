import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from forma_ai.mcp_client import MCPClient
from forma_ai.tool_registry import (
    ToolRegistry,
    ToolRegistryError,
    load_tool_package,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config/tool-packages.json"
FIXTURE_SERVER = ROOT / "tests/fixtures/mcp_echo_server/server.py"


class ToolRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.product_root = Path(self.tempdir.name) / "Product"
        self.product_root.mkdir()

    def tearDown(self) -> None:
        for tool_id in ("fixture-echo-mcp", "local-echo"):
            path = self.product_root / "state/tools/running" / f"{tool_id}.json"
            if path.is_file():
                registry = self.registry(local_paths=[])
                try:
                    registry.stop(tool_id)
                except ToolRegistryError:
                    pass
        self.tempdir.cleanup()

    def registry(self, *, local_paths: list[Path]) -> ToolRegistry:
        return ToolRegistry(
            self.product_root,
            catalog_path=CATALOG,
            repository_root=ROOT,
            local_paths=local_paths,
        )

    def test_local_discovery_takes_precedence_over_installed(self) -> None:
        local_root = Path(self.tempdir.name) / "local-tools"
        local_dir = local_root / "echo"
        local_dir.mkdir(parents=True)
        shutil.copy2(FIXTURE_SERVER, local_dir / "server.py")
        (local_dir / "mcp-tool.json").write_text(
            json.dumps({
                "schema_version": 1,
                "id": "fixture-echo-mcp",
                "version": "9.9.9",
                "command": sys.executable,
                "args": ["server.py"],
            }),
            encoding="utf-8",
        )
        registry = self.registry(local_paths=[local_root])
        registry.install("fixture-echo-mcp")
        discovered = registry.discover()
        match = next(item for item in discovered if item.tool_id == "fixture-echo-mcp")
        self.assertEqual(match.source, "local")
        self.assertEqual(match.version, "9.9.9")

    def test_install_verifies_digest_and_records_activation(self) -> None:
        registry = self.registry(local_paths=[])
        installation = registry.install("fixture-echo-mcp")
        self.assertEqual(installation.source, "registry")
        self.assertTrue((installation.install_dir / "server.py").is_file())
        index = json.loads((self.product_root / "state/tools/installed.json").read_text())
        self.assertEqual(index["tools"]["fixture-echo-mcp"]["artifact_sha256"],
                         load_tool_package(CATALOG, "fixture-echo-mcp").artifact.sha256)

    def test_install_rejects_tampered_artifact(self) -> None:
        class TamperedSource:
            def copy(self, *, source: Path, destination: Path) -> None:
                destination.write_text("tampered", encoding="utf-8")

        registry = ToolRegistry(
            self.product_root,
            catalog_path=CATALOG,
            repository_root=ROOT,
            artifact_source=TamperedSource(),
        )
        with self.assertRaises(ToolRegistryError) as raised:
            registry.install("fixture-echo-mcp")
        self.assertEqual(raised.exception.code, "TOOL_ARTIFACT_VERIFY_FAILED")

    def test_start_and_stop_manage_running_process(self) -> None:
        registry = self.registry(local_paths=[])
        registry.install("fixture-echo-mcp")
        state = registry.start("fixture-echo-mcp")
        self.assertTrue(registry.is_running("fixture-echo-mcp"))
        try:
            os.kill(state.pid, 0)
        finally:
            registry.stop("fixture-echo-mcp")
        self.assertFalse(registry.is_running("fixture-echo-mcp"))

    def test_installed_package_exposes_working_mcp_spec(self) -> None:
        registry = self.registry(local_paths=[])
        installation = registry.install("fixture-echo-mcp")
        client = MCPClient.from_server_spec(installation.server_spec())
        try:
            client.connect()
            tools = client.list_tools()
            self.assertEqual([tool.name for tool in tools], ["echo"])
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
