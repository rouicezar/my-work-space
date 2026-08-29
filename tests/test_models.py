import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mac_ai_work_os.models import ModelError, link_external_model, load_model, verify_snapshot


def fixture(tmp: Path):
    cache = tmp / "hub"
    repository = cache / "models--test--tiny"
    blobs = repository / "blobs"
    snapshot = repository / "snapshots" / ("a" * 40)
    blobs.mkdir(parents=True)
    snapshot.mkdir(parents=True)
    contents = {
        "config.json": json.dumps({
            "model_type": "fixture",
            "architectures": ["FixtureModel"],
            "quantization": {"bits": 4},
        }).encode(),
        "model.safetensors": b"weights",
    }
    files = {}
    for index, (name, payload) in enumerate(contents.items()):
        blob = blobs / f"blob-{index}"
        blob.write_bytes(payload)
        (snapshot / name).symlink_to(blob)
        files[name] = {"size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    catalog = tmp / "models.json"
    catalog.write_text(json.dumps({
        "schema_version": 1,
        "models": [{
            "id": "fixture",
            "repository": "test/tiny",
            "revision": "a" * 40,
            "license": "Apache-2.0",
            "license_url": "https://example.test/license",
            "model_type": "fixture",
            "architecture": "FixtureModel",
            "capabilities": ["chat"],
            "quantization_bits": 4,
            "files": files,
        }],
    }))
    return cache, catalog, snapshot


class ModelReferenceTests(unittest.TestCase):
    def test_catalog_capabilities_are_explicit_and_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, catalog, _ = fixture(root)
            self.assertEqual(load_model(catalog, "fixture").capabilities, ("chat",))
            data = json.loads(catalog.read_text())
            data["models"][0]["capabilities"] = ["chat", "secret-network-route"]
            catalog.write_text(json.dumps(data))
            with self.assertRaises(ModelError) as failed:
                load_model(catalog, "fixture")
            self.assertEqual(failed.exception.code, "MODEL_CAPABILITIES_INVALID")

    def test_verified_snapshot_is_linked_without_copying_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, catalog, snapshot = fixture(root)
            model = load_model(catalog, "fixture")
            reference = link_external_model(
                product_root=root / "Product", cache_root=cache, model=model
            )
            link = Path(reference.link_path)
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), snapshot.resolve())
            self.assertEqual(reference.storage_mode, "external-reference")
            self.assertEqual(reference.source_ownership, "external-cache-not-product-owned")
            self.assertEqual(
                (root / "Product/state/models/fixture.json").stat().st_mode & 0o777,
                0o600,
            )

    def test_tampered_file_is_rejected_before_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, catalog, snapshot = fixture(root)
            (snapshot / "model.safetensors").resolve().write_bytes(b"tampered")
            with self.assertRaises(ModelError) as failed:
                verify_snapshot(cache, load_model(catalog, "fixture"))
            self.assertIn(failed.exception.code, {"MODEL_SIZE_MISMATCH", "MODEL_DIGEST_MISMATCH"})

    def test_symlink_escaping_repository_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, catalog, snapshot = fixture(root)
            outside = root / "outside"
            outside.write_bytes(b"weights")
            (snapshot / "model.safetensors").unlink()
            (snapshot / "model.safetensors").symlink_to(outside)
            with self.assertRaisesRegex(ModelError, "model.safetensors") as failed:
                verify_snapshot(cache, load_model(catalog, "fixture"))
            self.assertEqual(failed.exception.code, "MODEL_LINK_ESCAPES_CACHE")

    def test_existing_conflicting_product_path_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, catalog, _ = fixture(root)
            conflict = root / "Product/data/omlx/models/test/tiny"
            conflict.mkdir(parents=True)
            with self.assertRaises(ModelError) as failed:
                link_external_model(
                    product_root=root / "Product",
                    cache_root=cache,
                    model=load_model(catalog, "fixture"),
                )
            self.assertEqual(failed.exception.code, "MODEL_LINK_CONFLICT")


if __name__ == "__main__":
    unittest.main()
