import json
import os
import tempfile
import unittest
from pathlib import Path

from mac_ai_work_os.embedding_config import EmbeddingConfigError, load_approved_embedding_route


class ApprovedEmbeddingRouteTests(unittest.TestCase):
    def fixture(self, base: Path):
        root = base / "Product"
        source = base / "cache/snapshot"
        source.mkdir(parents=True)
        link = root / "data/omlx/models/fixture/embedding"
        link.parent.mkdir(parents=True)
        os.symlink(source, link, target_is_directory=True)
        state = root / "state/models"
        state.mkdir(parents=True)
        reference = state / "fixture-embedding.json"
        reference.write_text(json.dumps({
            "schema_version": 1, "model_id": "fixture-embedding",
            "revision": "a" * 40, "source_path": str(source), "link_path": str(link),
            "storage_mode": "external-reference",
        }), encoding="utf-8")
        reference.chmod(0o600)
        route = state / "embedding-active.json"
        route.write_text(json.dumps({
            "schema_version": 1, "provider": "omlx", "capability": "embedding",
            "model_id": "fixture-embedding", "api_model": "fixture/embedding",
            "revision": "a" * 40, "expected_dimension": 384,
        }), encoding="utf-8")
        route.chmod(0o600)
        return root, route, link

    def test_absent_route_is_explicitly_inactive_without_creating_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            self.assertIsNone(load_approved_embedding_route(root))
            self.assertFalse(root.exists())

    def test_loads_only_private_route_bound_to_existing_model_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _ = self.fixture(Path(directory))
            route = load_approved_embedding_route(root)
            self.assertEqual(route.model_id, "fixture-embedding")
            self.assertEqual(route.api_model, "fixture/embedding")
            self.assertEqual(route.expected_dimension, 384)

    def test_rejects_world_readable_or_broken_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            root, route, link = self.fixture(Path(directory))
            route.chmod(0o644)
            with self.assertRaises(EmbeddingConfigError) as error:
                load_approved_embedding_route(root)
            self.assertEqual(error.exception.code, "EMBEDDING_ROUTE_UNSAFE")
            route.chmod(0o600)
            link.unlink()
            with self.assertRaises(EmbeddingConfigError) as error:
                load_approved_embedding_route(root)
            self.assertEqual(error.exception.code, "EMBEDDING_REFERENCE_MISMATCH")
