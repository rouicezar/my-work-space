import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mac_ai_work_os.downloads import ResumableDownloader
from mac_ai_work_os.model_downloads import download_model_snapshot
from mac_ai_work_os.models import ModelDefinition, ModelError, ModelFile
from tests.test_downloads import FakeOpen, FakeResponse


CONFIG = b'{"model_type":"bert","architectures":["BertModel"]}'
WEIGHTS = b"fixture-weights"


def model() -> ModelDefinition:
    return ModelDefinition(
        id="fixture-embedding", repository="fixture/embedding",
        revision="a" * 40, license="MIT", license_url="https://example.test/license",
        model_type="bert", architecture="BertModel", capabilities=("embedding",),
        quantization_bits=None, embedding_dimension=384,
        query_prefix="query: ", document_prefix="passage: ",
        files={
            "config.json": ModelFile(len(CONFIG), hashlib.sha256(CONFIG).hexdigest()),
            "weights.bin": ModelFile(len(WEIGHTS), hashlib.sha256(WEIGHTS).hexdigest()),
        },
    )


class ModelDownloadTests(unittest.TestCase):
    def test_downloads_all_files_to_exact_snapshot_then_verifies(self):
        opened = FakeOpen([
            FakeResponse(CONFIG, url="https://huggingface.co/fixture/config.json"),
            FakeResponse(WEIGHTS, url="https://cas-bridge.xethub.hf.co/fixture/weights"),
        ])
        downloader = ResumableDownloader(
            open_url=opened,
            allowed_hosts=frozenset({"huggingface.co", "cas-bridge.xethub.hf.co"}),
        )
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            result = download_model_snapshot(
                cache_root=cache, model=model(), approved_revision="a" * 40,
                downloader=downloader,
            )
            snapshot = Path(result.snapshot_path)
            self.assertEqual((snapshot / "config.json").read_bytes(), CONFIG)
            self.assertEqual((snapshot / "weights.bin").read_bytes(), WEIGHTS)
            self.assertEqual(result.transferred_bytes, len(CONFIG) + len(WEIGHTS))
            self.assertEqual(result.downloaded_files, 2)
            self.assertIn("/resolve/" + "a" * 40 + "/", opened.requests[0].full_url)

    def test_requires_exact_revision_approval_before_creating_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            with self.assertRaisesRegex(ModelError, "fixture-embedding"):
                download_model_snapshot(
                    cache_root=cache, model=model(), approved_revision="b" * 40,
                    downloader=ResumableDownloader(open_url=FakeOpen([])),
                )
            self.assertEqual(list(cache.iterdir()), [])

    def test_refuses_symlink_in_cache_path(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            cache = Path(directory)
            repository = cache / "models--fixture--embedding"
            repository.symlink_to(Path(outside), target_is_directory=True)
            with self.assertRaisesRegex(ModelError, "models--fixture--embedding"):
                download_model_snapshot(
                    cache_root=cache, model=model(), approved_revision="a" * 40,
                    downloader=ResumableDownloader(open_url=FakeOpen([])),
                )


if __name__ == "__main__":
    unittest.main()
