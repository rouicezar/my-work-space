import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mac_ai_work_os.omlx_embeddings import (
    EmbeddingError,
    OMLXEmbeddingClient,
    PersistentOMLXVectorStore,
)


class FakeResponse:
    def __init__(self, payload):
        self.buffer = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, limit):
        return self.buffer.read(limit)


class FixtureClient:
    model = "fixture-embedding"

    def embed(self, text):
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]

    def probe(self):
        return {"status": "healthy", "model": self.model, "dimension": 2}


class OMLXEmbeddingClientTests(unittest.TestCase):
    def client(self, **kwargs):
        return OMLXEmbeddingClient(
            port=8000, api_key="k" * 32, model="fixed/model", expected_dimension=2, **kwargs
        )

    @patch("urllib.request.urlopen")
    def test_validates_auth_model_indexes_and_vectors(self, urlopen):
        urlopen.return_value = FakeResponse({
            "object": "list", "model": "fixed/model",
            "data": [
                {"index": 1, "embedding": [0, 1]},
                {"index": 0, "embedding": [1, 0]},
            ],
        })
        vectors = self.client().embed_many(["alpha", "beta"])
        self.assertEqual(vectors, [[1.0, 0.0], [0.0, 1.0]])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer " + "k" * 32)
        self.assertEqual(json.loads(request.data)["encoding_format"], "float")

    @patch("urllib.request.urlopen")
    def test_rejects_wrong_model_and_nonfinite_vector(self, urlopen):
        urlopen.return_value = FakeResponse({"model": "wrong", "data": [{"index": 0, "embedding": [1, 0]}]})
        with self.assertRaisesRegex(EmbeddingError, "unexpected model") as error:
            self.client().embed("alpha")
        self.assertEqual(error.exception.code, "EMBEDDING_MODEL_MISMATCH")
        urlopen.return_value = FakeResponse({"model": "fixed/model", "data": [{"index": 0, "embedding": [1, float("nan")]}]})
        with self.assertRaises(EmbeddingError) as error:
            self.client().embed("alpha")
        self.assertEqual(error.exception.code, "EMBEDDING_INVALID_VECTOR")

    @patch("urllib.request.urlopen")
    def test_rejects_oversized_response(self, urlopen):
        client = self.client(max_response_bytes=8)
        urlopen.return_value = FakeResponse({"model": "fixed/model", "data": []})
        with self.assertRaises(EmbeddingError) as error:
            client.embed("alpha")
        self.assertEqual(error.exception.code, "EMBEDDING_RESPONSE_TOO_LARGE")


class PersistentVectorStoreTests(unittest.TestCase):
    def test_rejects_relative_index_path(self):
        with self.assertRaisesRegex(ValueError, "absolute"):
            PersistentOMLXVectorStore(Path("relative.sqlite3"), FixtureClient())

    def test_persists_searches_deletes_and_binds_model_and_dimension(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.sqlite3"
            store = PersistentOMLXVectorStore(path, FixtureClient())
            identities = store.store_vectors(
                [[1, 0], [0, 1]],
                [{"record_id": "record-alpha"}, {"record_id": "record-beta"}],
            )
            self.assertEqual(store.search_vectors([0.9, 0.1], k=1)[0]["metadata"]["record_id"], "record-alpha")
            restored = PersistentOMLXVectorStore(path, FixtureClient())
            self.assertEqual(restored.health()["vector_count"], 2)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            self.assertEqual(restored.delete_vectors([identities[0]]), 1)
            with self.assertRaises(EmbeddingError) as error:
                restored.search_vectors([1, 0, 0])
            self.assertEqual(error.exception.code, "VECTOR_INDEX_BINDING_MISMATCH")

            incompatible = FixtureClient()
            incompatible.model = "other-model"
            with self.assertRaises(EmbeddingError) as error:
                PersistentOMLXVectorStore(path, incompatible)
            self.assertEqual(error.exception.code, "VECTOR_INDEX_BINDING_MISMATCH")


if __name__ == "__main__":
    unittest.main()
