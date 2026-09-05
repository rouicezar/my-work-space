"""The signed app must not depend on a repository checkout or Python CLI."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
import uuid
from tests.test_models import fixture
from forma_ai.models import load_model, link_external_model

from scripts import supervisor


class NativeEntrypointTests(unittest.TestCase):
    def test_model_plan_reuses_existing_verified_product_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            cache, catalog, snapshot = fixture(base)
            root = base / 'Product'
            link_external_model(product_root=root, cache_root=cache, model=load_model(catalog, 'fixture'))
            empty = base / 'new-product-cache'
            empty.mkdir()
            args = supervisor.parser().parse_args([
                '--request-id', str(uuid.uuid4()), 'model-plan', '--root', str(root),
                '--cache-root', str(empty), '--catalog', str(catalog), '--model-id', 'fixture'])
            result = supervisor.run(args)['payload']
            self.assertTrue(result['available_verified'])
            self.assertEqual(Path(result['source_path']).resolve(), snapshot.resolve())
    def test_frozen_resource_root_is_app_resources(self):
        self.assertEqual(supervisor.resource_root(
            frozen=True, executable=Path('/Applications/Forma AI.app/Contents/Helpers/Supervisor/forma-ai-supervisor'),
            source=Path('/irrelevant/_internal/supervisor.py')),
            Path('/Applications/Forma AI.app/Contents/Resources'))

    def test_internal_mcp_is_ndjson_not_supervisor_envelope(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([
            sys.executable, str(root / 'scripts/supervisor.py'), 'internal-qwen-mcp',
            '--root', '/tmp/forma-unused-handshake', '--repository-root', str(root),
            '--catalog', str(root / 'config/tool-routing.json'),
        ], input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n',
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['result']['serverInfo']['name'], 'forma-governed-tools')
