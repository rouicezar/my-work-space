"""Persistent storage for product task metadata without runtime authority claims."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from forma_ai.models import _atomic_json
from forma_ai.task_metadata_projection import (
    TaskMetadataProjectionError,
    TaskMetadataRecord,
    metadata_record_from_dict,
    metadata_record_to_dict,
    validate_metadata_payload,
)


class TaskMetadataStoreError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class TaskMetadataStore:
    def __init__(self, product_root: Path) -> None:
        if not product_root.is_absolute():
            raise TaskMetadataStoreError("PRODUCT_ROOT_INVALID", str(product_root))
        self.directory = product_root / "state/task-metadata"

    def save(self, record: TaskMetadataRecord) -> TaskMetadataRecord:
        self._validate_task_id(record.task_id)
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        self._validate_directory()
        path = self._path(record.task_id)
        if path.is_symlink():
            raise TaskMetadataStoreError("METADATA_PATH_UNSAFE", record.task_id)
        _atomic_json(path, metadata_record_to_dict(record))
        return record

    def load(self, task_id: str) -> TaskMetadataRecord:
        record = self.load_optional(task_id)
        if record is None:
            raise TaskMetadataStoreError("METADATA_NOT_FOUND", task_id)
        return record

    def load_optional(self, task_id: str) -> TaskMetadataRecord | None:
        self._validate_task_id(task_id)
        if not self.directory.exists() and not self.directory.is_symlink():
            return None
        self._validate_directory()
        path = self._path(task_id)
        if not path.exists() and not path.is_symlink():
            return None
        return self._read_record(path, task_id)

    def list_task_ids(self) -> tuple[str, ...]:
        if not self.directory.is_dir() or self.directory.is_symlink():
            return ()
        self._validate_directory()
        task_ids: list[str] = []
        for path in sorted(self.directory.glob("*.json")):
            if not path.is_file() or path.is_symlink():
                continue
            if stat.S_IMODE(path.stat().st_mode) & 0o077:
                continue
            task_id = path.stem
            try:
                self._validate_task_id(task_id)
            except TaskMetadataStoreError:
                continue
            task_ids.append(task_id)
        return tuple(task_ids)

    def delete(self, task_id: str) -> None:
        self._validate_task_id(task_id)
        if not self.directory.is_dir() or self.directory.is_symlink():
            return
        path = self._path(task_id)
        if path.is_symlink():
            raise TaskMetadataStoreError("METADATA_PATH_UNSAFE", task_id)
        path.unlink(missing_ok=True)

    def _read_record(self, path: Path, task_id: str) -> TaskMetadataRecord:
        if (
            not path.is_file()
            or path.is_symlink()
            or stat.S_IMODE(path.stat().st_mode) & 0o077
        ):
            raise TaskMetadataStoreError("METADATA_UNSAFE", task_id)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise TypeError("metadata record must be an object")
            validate_metadata_payload(raw)
            record = metadata_record_from_dict(raw)
        except (OSError, TypeError, ValueError, json.JSONDecodeError, TaskMetadataProjectionError) as exc:
            raise TaskMetadataStoreError("METADATA_INVALID", task_id) from exc
        if record.task_id != task_id:
            raise TaskMetadataStoreError("METADATA_INVALID", task_id)
        return record

    def _path(self, task_id: str) -> Path:
        return self.directory / f"{task_id}.json"

    def _validate_directory(self) -> None:
        if (
            not self.directory.is_dir()
            or self.directory.is_symlink()
            or stat.S_IMODE(self.directory.stat().st_mode) & 0o077
        ):
            raise TaskMetadataStoreError("METADATA_DIRECTORY_UNSAFE", str(self.directory))

    @staticmethod
    def _validate_task_id(task_id: str) -> None:
        if not task_id or Path(task_id).name != task_id or task_id.startswith("."):
            raise TaskMetadataStoreError("METADATA_TASK_ID_INVALID", task_id)


def binding_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "storage_relative_directory": "state/task-metadata",
        "record_file_suffix": ".json",
        "persists_runtime_claims": False,
    }
