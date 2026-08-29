"""Pinned model catalog and zero-copy external-cache references."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


REVISION = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
MODEL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")


class ModelError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ModelFile:
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ModelDefinition:
    id: str
    repository: str
    revision: str
    license: str
    license_url: str
    model_type: str
    architecture: str
    quantization_bits: int
    files: dict[str, ModelFile]


@dataclass(frozen=True)
class ModelReference:
    schema_version: int
    model_id: str
    repository: str
    revision: str
    source_path: str
    link_path: str
    storage_mode: str
    source_ownership: str
    linked_at: str


def load_model(path: Path, model_id: str) -> ModelDefinition:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ModelError("CATALOG_SCHEMA", "unsupported model catalog schema")
    matches = [item for item in data.get("models", []) if item.get("id") == model_id]
    if len(matches) != 1:
        raise ModelError("MODEL_NOT_FOUND", model_id)
    item = matches[0]
    if not MODEL_ID.fullmatch(str(item.get("id", ""))):
        raise ModelError("UNSAFE_MODEL_ID", str(item.get("id")))
    if not REPOSITORY.fullmatch(str(item.get("repository", ""))):
        raise ModelError("UNSAFE_REPOSITORY", str(item.get("repository")))
    if not REVISION.fullmatch(str(item.get("revision", ""))):
        raise ModelError("UNPINNED_REVISION", str(item.get("revision")))
    files: dict[str, ModelFile] = {}
    for name, metadata in item.get("files", {}).items():
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or str(pure) != name:
            raise ModelError("UNSAFE_MODEL_FILE", name)
        size = metadata.get("size_bytes")
        digest = str(metadata.get("sha256", ""))
        if not isinstance(size, int) or size <= 0 or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ModelError("INVALID_MODEL_FILE", name)
        files[name] = ModelFile(size, digest)
    if not files:
        raise ModelError("MODEL_FILES_MISSING", model_id)
    return ModelDefinition(
        id=item["id"],
        repository=item["repository"],
        revision=item["revision"],
        license=item["license"],
        license_url=item["license_url"],
        model_type=item["model_type"],
        architecture=item["architecture"],
        quantization_bits=item["quantization_bits"],
        files=files,
    )


def huggingface_snapshot(cache_root: Path, model: ModelDefinition) -> Path:
    repository_directory = f"models--{model.repository.replace('/', '--')}"
    return cache_root / repository_directory / "snapshots" / model.revision


def verify_snapshot(cache_root: Path, model: ModelDefinition) -> Path:
    snapshot = huggingface_snapshot(cache_root, model)
    if snapshot.is_symlink() or not snapshot.is_dir():
        raise ModelError("SNAPSHOT_MISSING", str(snapshot))
    repository_root = snapshot.parents[1].resolve()
    for relative, expected in model.files.items():
        path = snapshot / relative
        try:
            metadata = path.lstat()
        except FileNotFoundError as exc:
            raise ModelError("MODEL_FILE_MISSING", relative) from exc
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(repository_root)
        except ValueError as exc:
            raise ModelError("MODEL_LINK_ESCAPES_CACHE", relative) from exc
        if not stat.S_ISREG(resolved.stat().st_mode):
            raise ModelError("MODEL_FILE_NOT_REGULAR", relative)
        if resolved.stat().st_size != expected.size_bytes:
            raise ModelError("MODEL_SIZE_MISMATCH", relative)
        digest_state = hashlib.sha256()
        with resolved.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest_state.update(chunk)
        digest = digest_state.hexdigest()
        if digest != expected.sha256:
            raise ModelError("MODEL_DIGEST_MISMATCH", relative)
        if not (stat.S_ISLNK(metadata.st_mode) or stat.S_ISREG(metadata.st_mode)):
            raise ModelError("MODEL_ENTRY_UNSAFE", relative)
    config = json.loads((snapshot / "config.json").read_text(encoding="utf-8"))
    if config.get("model_type") != model.model_type:
        raise ModelError("MODEL_TYPE_MISMATCH", str(config.get("model_type")))
    if model.architecture not in config.get("architectures", []):
        raise ModelError("MODEL_ARCHITECTURE_MISMATCH", str(config.get("architectures")))
    if config.get("quantization", {}).get("bits") != model.quantization_bits:
        raise ModelError("MODEL_QUANTIZATION_MISMATCH", str(config.get("quantization")))
    return snapshot


def link_external_model(
    *,
    product_root: Path,
    cache_root: Path,
    model: ModelDefinition,
) -> ModelReference:
    snapshot = verify_snapshot(cache_root, model)
    owner, name = model.repository.split("/", 1)
    link = product_root / "data" / "omlx" / "models" / owner / name
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        try:
            linked_snapshot = link.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ModelError("MODEL_LINK_BROKEN", str(link)) from exc
        if linked_snapshot != snapshot.resolve():
            raise ModelError("MODEL_LINK_CONFLICT", str(link))
    elif link.exists():
        raise ModelError("MODEL_LINK_CONFLICT", str(link))
    else:
        temporary = link.with_name(f".{link.name}-{uuid.uuid4().hex}.tmp")
        os.symlink(snapshot, temporary, target_is_directory=True)
        os.replace(temporary, link)
    record = ModelReference(
        schema_version=1,
        model_id=model.id,
        repository=model.repository,
        revision=model.revision,
        source_path=str(snapshot),
        link_path=str(link),
        storage_mode="external-reference",
        source_ownership="external-cache-not-product-owned",
        linked_at=datetime.now(timezone.utc).isoformat(),
    )
    _atomic_json(product_root / "state" / "models" / f"{model.id}.json", asdict(record))
    return record


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    temporary = Path(name)
    os.fchmod(descriptor, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
