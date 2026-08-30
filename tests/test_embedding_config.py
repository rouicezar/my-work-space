import json
import os
import tempfile
import unittest
from pathlib import Path

from mac_ai_work_os.embedding_config import (
    EmbeddingConfigError, activate_embedding_route, load_approved_embedding_route,
)
from mac_ai_work_os.models import ModelDefinition, ModelReference


class ApprovedEmbeddingRouteTests(unittest.TestCase):
    def model(self):
        return ModelDefinition(
            id="fixture-embedding", repository="fixture/embedding", revision="a" * 40,
            license="MIT", license_url="https://example.test/license", model_type="bert",
            architecture="BertModel", capabilities=("embedding",), quantization_bits=None,
            embedding_dimension=384, query_prefix="query: ", document_prefix="passage: ",
            files={},
        )
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
            "query_prefix": "query: ", "document_prefix": "passage: ",
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
            self.assertEqual(route.query_prefix, "query: ")
            self.assertEqual(route.document_prefix, "passage: ")

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

    def test_activation_is_private_and_refuses_existing_incompatible_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, link = self.fixture(Path(directory))
            active = root / "state/models/embedding-active.json"
            active.unlink()
            reference = ModelReference(
                1, "fixture-embedding", "fixture/embedding", "a" * 40,
                str(link.resolve()), str(link), "external-reference",
                "external-cache-not-product-owned", "now",
            )
            route = activate_embedding_route(
                root, self.model(), reference, approved_revision="a" * 40,
            )
            self.assertEqual(route.expected_dimension, 384)
            self.assertEqual(active.stat().st_mode & 0o777, 0o600)
            self.assertEqual(load_approved_embedding_route(root), route)

            import sqlite3
            index = root / "data/semantica/vector-index.sqlite3"
            index.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(index) as db:
                db.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("INSERT INTO metadata VALUES ('model', 'different-model')")
            with self.assertRaises(EmbeddingConfigError) as error:
                activate_embedding_route(
                    root, self.model(), reference, approved_revision="a" * 40,
                )
            self.assertEqual(error.exception.code, "VECTOR_INDEX_MIGRATION_REQUIRED")
