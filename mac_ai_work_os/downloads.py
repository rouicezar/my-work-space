"""Crash-safe, integrity-gated downloads for pinned product artifacts."""

from __future__ import annotations

import os
import re
import stat
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Callable, Protocol
from urllib.parse import urlsplit

from mac_ai_work_os.artifacts import ArtifactExpectation, verify_file


CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")
DEFAULT_ALLOWED_HOSTS = frozenset(
    {
        "github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
    }
)


class DownloadError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class HTTPResponse(Protocol):
    status: int
    headers: object

    def read(self, size: int = -1) -> bytes: ...
    def geturl(self) -> str: ...
    def __enter__(self) -> "HTTPResponse": ...
    def __exit__(self, *args: object) -> None: ...


OpenURL = Callable[[urllib.request.Request, float], HTTPResponse]
Progress = Callable[[int, int], None]


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    bytes_downloaded: int
    resumed_from: int
    reused_verified_file: bool


def _open(request: urllib.request.Request, timeout: float) -> HTTPResponse:
    return urllib.request.urlopen(request, timeout=timeout)  # type: ignore[return-value]


class ResumableDownloader:
    def __init__(
        self,
        *,
        open_url: OpenURL = _open,
        timeout: float = 30.0,
        chunk_size: int = 1024 * 1024,
        allowed_hosts: frozenset[str] = DEFAULT_ALLOWED_HOSTS,
    ):
        if timeout <= 0 or chunk_size <= 0:
            raise ValueError("download timeout and chunk size must be positive")
        self.open_url = open_url
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.allowed_hosts = allowed_hosts

    def fetch(
        self,
        expected: ArtifactExpectation,
        directory: Path,
        progress: Progress | None = None,
    ) -> DownloadResult:
        directory.mkdir(parents=True, exist_ok=True)
        if directory.is_symlink() or not directory.is_dir():
            raise DownloadError("UNSAFE_DIRECTORY", "download directory must be a real directory")
        if not expected.name or Path(expected.name).name != expected.name:
            raise DownloadError("UNSAFE_NAME", "artifact name must be a plain filename")
        destination = directory / expected.name
        partial = directory / f"{expected.name}.part"

        self._reject_unsafe_existing_path(destination)
        self._reject_unsafe_existing_path(partial)

        if destination.exists():
            verification = verify_file(destination, expected)
            if verification.valid:
                if progress:
                    progress(expected.size_bytes, expected.size_bytes)
                return DownloadResult(destination, 0, expected.size_bytes, True)
            raise DownloadError(
                "DESTINATION_INVALID",
                "an existing final artifact failed integrity verification; repair must quarantine it",
            )

        offset = partial.stat().st_size if partial.exists() else 0
        if offset >= expected.size_bytes:
            verification = verify_file(partial, expected)
            if verification.valid:
                os.replace(partial, destination)
                return DownloadResult(destination, 0, offset, False)
            partial.unlink()
            offset = 0

        headers = {"Accept": "application/octet-stream", "User-Agent": "MacAIWorkOS/0.1"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        request = urllib.request.Request(expected.url, headers=headers, method="GET")

        try:
            with self.open_url(request, self.timeout) as response:
                self._validate_final_url(response.geturl())
                mode, resumed_from = self._response_mode(response, offset, expected.size_bytes)
                if mode == "wb":
                    offset = 0
                downloaded = self._write(
                    response,
                    partial,
                    mode,
                    offset,
                    expected.size_bytes,
                    progress,
                )
        except DownloadError:
            raise
        except urllib.error.HTTPError as exc:
            raise DownloadError("HTTP_STATUS", f"HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise DownloadError("TRANSFER_INTERRUPTED", str(exc)) from exc

        verification = verify_file(partial, expected)
        if not verification.valid:
            raise DownloadError(
                "INTEGRITY_MISMATCH",
                f"downloaded artifact failed size or SHA-256 verification: {partial}",
            )
        os.replace(partial, destination)
        return DownloadResult(destination, downloaded, resumed_from, False)

    def _validate_final_url(self, url: str) -> None:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise DownloadError("UNSAFE_REDIRECT", f"artifact redirected to untrusted URL: {url}")

    @staticmethod
    def _response_mode(response: HTTPResponse, offset: int, total: int) -> tuple[str, int]:
        if offset == 0:
            if response.status != 200:
                raise DownloadError("HTTP_STATUS", f"expected HTTP 200, got {response.status}")
            return "wb", 0
        if response.status == 200:
            return "wb", 0
        if response.status != 206:
            raise DownloadError("RESUME_REJECTED", f"expected HTTP 206, got {response.status}")
        raw = response.headers.get("Content-Range")  # type: ignore[attr-defined]
        match = CONTENT_RANGE.fullmatch(str(raw or ""))
        if not match or int(match.group(1)) != offset or int(match.group(3)) != total:
            raise DownloadError("INVALID_CONTENT_RANGE", f"unexpected Content-Range: {raw}")
        return "ab", offset

    def _write(
        self,
        response: BinaryIO,
        partial: Path,
        mode: str,
        offset: int,
        expected_size: int,
        progress: Progress | None,
    ) -> int:
        current = offset
        transferred = 0
        flags = os.O_CREAT | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        flags |= os.O_APPEND if mode == "ab" else os.O_TRUNC
        descriptor = os.open(partial, flags, 0o600)
        with os.fdopen(descriptor, "ab" if mode == "ab" else "wb") as handle:
            while True:
                chunk = response.read(self.chunk_size)
                if not chunk:
                    break
                current += len(chunk)
                transferred += len(chunk)
                if current > expected_size:
                    raise DownloadError("SIZE_EXCEEDED", "download exceeded pinned artifact size")
                handle.write(chunk)
                if progress:
                    progress(current, expected_size)
            handle.flush()
            os.fsync(handle.fileno())
        if current != expected_size:
            raise DownloadError(
                "TRANSFER_INCOMPLETE", f"expected {expected_size} bytes, received {current}"
            )
        return transferred

    @staticmethod
    def _reject_unsafe_existing_path(path: Path) -> None:
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise DownloadError("UNSAFE_LOCAL_PATH", f"artifact path is not a regular file: {path}")
