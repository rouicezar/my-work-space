"""Explicitly approved, resumable downloads for pinned Hugging Face model snapshots."""

from __future__ import annotations

import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import quote

from forma_ai.artifacts import ArtifactExpectation
from forma_ai.downloads import DownloadResult, ResumableDownloader
from forma_ai.models import ModelDefinition, ModelError, huggingface_snapshot, verify_snapshot


HUGGINGFACE_DOWNLOAD_HOSTS = frozenset({
    "huggingface.co",
    "cdn-lfs.huggingface.co",
    "cdn-lfs.hf.co",
    "cas-bridge.xethub.hf.co",
    "us.aws.cdn.hf.co",
})


@dataclass(frozen=True)
class ModelDownloadResult:
    schema_version: int
    model_id: str
    revision: str
    snapshot_path: str
    total_size_bytes: int
    transferred_bytes: int
    reused_files: int
    downloaded_files: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def download_model_snapshot(
    *,
    cache_root: Path,
    model: ModelDefinition,
    approved_revision: str,
    downloader: ResumableDownloader | None = None,
) -> ModelDownloadResult:
    if approved_revision != model.revision:
        raise ModelError("MODEL_APPROVAL_MISMATCH", model.id)
    if not cache_root.is_absolute() or not cache_root.is_dir() or cache_root.is_symlink():
        raise ModelError("MODEL_CACHE_UNSAFE", str(cache_root))
    snapshot = huggingface_snapshot(cache_root, model)
    _prepare_snapshot_directory(cache_root, snapshot)
    client = downloader or ResumableDownloader(allowed_hosts=HUGGINGFACE_DOWNLOAD_HOSTS)
    transferred = 0
    reused = 0
    downloaded = 0
    for relative, metadata in sorted(model.files.items()):
        relative_path = Path(relative)
        directory = snapshot / relative_path.parent
        _prepare_snapshot_directory(cache_root, directory)
        expectation = ArtifactExpectation(
            component=model.id,
            release=model.revision,
            artifact_id=relative,
            name=relative_path.name,
            size_bytes=metadata.size_bytes,
            sha256=metadata.sha256,
            url=(
                f"https://huggingface.co/{model.repository}/resolve/"
                f"{model.revision}/{quote(relative, safe='/')}?download=true"
            ),
        )
        result: DownloadResult = client.fetch(expectation, directory)
        transferred += result.bytes_downloaded
        if result.reused_verified_file:
            reused += 1
        else:
            downloaded += 1
    verified = verify_snapshot(cache_root, model)
    return ModelDownloadResult(
        schema_version=1,
        model_id=model.id,
        revision=model.revision,
        snapshot_path=str(verified),
        total_size_bytes=sum(item.size_bytes for item in model.files.values()),
        transferred_bytes=transferred,
        reused_files=reused,
        downloaded_files=downloaded,
    )


def _prepare_snapshot_directory(cache_root: Path, directory: Path) -> None:
    root = cache_root.resolve(strict=True)
    try:
        directory.relative_to(cache_root)
    except ValueError as exc:
        raise ModelError("MODEL_CACHE_ESCAPE", str(directory)) from exc
    current = cache_root
    for part in directory.relative_to(cache_root).parts:
        current = current / part
        if current.exists() or current.is_symlink():
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise ModelError("MODEL_CACHE_PATH_UNSAFE", str(current))
        else:
            current.mkdir(mode=0o700)
        try:
            current.resolve(strict=True).relative_to(root)
        except ValueError as exc:
            raise ModelError("MODEL_CACHE_ESCAPE", str(current)) from exc
