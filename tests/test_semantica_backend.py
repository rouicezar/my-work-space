import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from forma_ai.semantica_backend import (
    ManagedSemanticaError,
    create_managed_semantica_backend,
)


class FixtureAgentContext:
    def __init__(self, **kwargs):
        self.vector_store = kwargs["vector_store"]

    def get_memory(self, memory_id):
        return None


class ManagedSemanticaBackendFactoryTests(unittest.TestCase):
    def modules(self, root, version="0.6.7"):
        module_path = root / "runtimes/semantica/v0.6.7/lib/python3.12/site-packages/semantica/__init__.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text("", encoding="utf-8")
        return SimpleNamespace(__file__=str(module_path), __version__=version), \
            SimpleNamespace(AgentContext=FixtureAgentContext)

    def test_builds_only_from_exact_managed_runtime_and_product_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "Product"
            semantica, context = self.modules(root)
            with patch("forma_ai.semantica_backend.importlib.import_module",
                       side_effect=[semantica, context]):
                backend = create_managed_semantica_backend(
                    product_root=root, omlx_port=8000, omlx_api_key="o" * 40,
                    embedding_model="fixture/embedding", expected_dimension=384,
                    query_prefix="query: ", document_prefix="passage: ",
                )
            self.assertEqual(backend.embedding_route, "omlx://fixture/embedding")
            self.assertEqual(
                backend.semantic_store.path,
                root / "data/semantica/vector-index.sqlite3",
            )
            self.assertEqual(backend.state_path, root / "data/semantica/context")

    def test_rejects_wrong_version_even_when_importable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "Product"
            semantica, context = self.modules(root, version="0.6.8")
            with patch("forma_ai.semantica_backend.importlib.import_module",
                       side_effect=[semantica, context]):
                with self.assertRaises(ManagedSemanticaError) as error:
                    create_managed_semantica_backend(
                        product_root=root, omlx_port=8000, omlx_api_key="o" * 40,
                        embedding_model="fixture/embedding", expected_dimension=384,
                        query_prefix="query: ", document_prefix="passage: ",
                    )
            self.assertEqual(error.exception.code, "SEMANTICA_VERSION_MISMATCH")
