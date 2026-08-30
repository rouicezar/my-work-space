import hashlib
import tempfile
import unittest
import urllib.error
from pathlib import Path

from forma_ai.artifacts import ArtifactExpectation
from forma_ai.downloads import DownloadError, ResumableDownloader


PAYLOAD = b"0123456789abcdef"


def expectation() -> ArtifactExpectation:
    return ArtifactExpectation(
        component="fixture",
        release="v1",
        artifact_id="fixture",
        name="fixture.bin",
        size_bytes=len(PAYLOAD),
        sha256=hashlib.sha256(PAYLOAD).hexdigest(),
        url="https://github.com/example/releases/download/v1/fixture.bin",
    )


class FakeResponse:
    def __init__(self, body, status=200, headers=None, url=None, fail_after=None):
        self.body = body
        self.status = status
        self.headers = headers or {}
        self.url = url or expectation().url
        self.position = 0
        self.fail_after = fail_after

    def read(self, size=-1):
        if self.fail_after is not None and self.position >= self.fail_after:
            raise OSError("connection lost")
        if size < 0:
            size = len(self.body)
        chunk = self.body[self.position : self.position + size]
        self.position += len(chunk)
        return chunk

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeOpen:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        return self.responses.pop(0)


class DownloadTests(unittest.TestCase):
    def test_new_download_is_verified_then_atomically_published(self):
        opened = FakeOpen([FakeResponse(PAYLOAD)])
        progress = []
        with tempfile.TemporaryDirectory() as directory:
            result = ResumableDownloader(open_url=opened, chunk_size=3).fetch(
                expectation(), Path(directory), lambda done, total: progress.append((done, total))
            )
            self.assertEqual(result.path.read_bytes(), PAYLOAD)
            self.assertFalse((Path(directory) / "fixture.bin.part").exists())
        self.assertEqual(result.bytes_downloaded, len(PAYLOAD))
        self.assertEqual(progress[-1], (len(PAYLOAD), len(PAYLOAD)))

    def test_interrupted_transfer_keeps_partial_and_next_run_resumes(self):
        first = FakeOpen([FakeResponse(PAYLOAD, fail_after=6)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(DownloadError, "connection lost"):
                ResumableDownloader(open_url=first, chunk_size=3).fetch(expectation(), root)
            partial_size = (root / "fixture.bin.part").stat().st_size
            self.assertEqual(partial_size, 6)

            second = FakeOpen([
                FakeResponse(
                    PAYLOAD[partial_size:],
                    status=206,
                    headers={"Content-Range": f"bytes {partial_size}-{len(PAYLOAD)-1}/{len(PAYLOAD)}"},
                )
            ])
            result = ResumableDownloader(open_url=second, chunk_size=4).fetch(expectation(), root)
            self.assertEqual(second.requests[0].headers["Range"], f"bytes={partial_size}-")
            self.assertEqual(result.resumed_from, partial_size)
            self.assertEqual(result.path.read_bytes(), PAYLOAD)

    def test_server_ignoring_range_restarts_instead_of_appending(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture.bin.part").write_bytes(PAYLOAD[:5])
            opened = FakeOpen([FakeResponse(PAYLOAD, status=200)])
            result = ResumableDownloader(open_url=opened, chunk_size=4).fetch(expectation(), root)
            self.assertEqual(result.resumed_from, 0)
            self.assertEqual(result.path.read_bytes(), PAYLOAD)

    def test_invalid_content_range_fails_without_publishing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture.bin.part").write_bytes(PAYLOAD[:5])
            opened = FakeOpen([
                FakeResponse(PAYLOAD[5:], status=206, headers={"Content-Range": "bytes 4-15/16"})
            ])
            with self.assertRaisesRegex(DownloadError, "Content-Range"):
                ResumableDownloader(open_url=opened).fetch(expectation(), root)
            self.assertFalse((root / "fixture.bin").exists())

    def test_digest_mismatch_never_publishes_final_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            opened = FakeOpen([FakeResponse(b"x" * len(PAYLOAD))])
            with self.assertRaisesRegex(DownloadError, "SHA-256"):
                ResumableDownloader(open_url=opened).fetch(expectation(), root)
            self.assertFalse((root / "fixture.bin").exists())

    def test_untrusted_redirect_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            opened = FakeOpen([FakeResponse(PAYLOAD, url="https://evil.example/payload")])
            with self.assertRaisesRegex(DownloadError, "untrusted"):
                ResumableDownloader(open_url=opened).fetch(expectation(), root)
            self.assertFalse((root / "fixture.bin.part").exists())

    def test_existing_verified_file_is_reused_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture.bin").write_bytes(PAYLOAD)
            opened = FakeOpen([])
            result = ResumableDownloader(open_url=opened).fetch(expectation(), root)
            self.assertTrue(result.reused_verified_file)
            self.assertEqual(opened.requests, [])

    def test_symlink_partial_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            victim = root / "victim"
            victim.write_bytes(b"keep")
            (root / "fixture.bin.part").symlink_to(victim)
            with self.assertRaisesRegex(DownloadError, "not a regular file"):
                ResumableDownloader(open_url=FakeOpen([FakeResponse(PAYLOAD)])).fetch(
                    expectation(), root
                )
            self.assertEqual(victim.read_bytes(), b"keep")

    def test_unsafe_artifact_name_is_rejected(self):
        unsafe = ArtifactExpectation(
            component="fixture",
            release="v1",
            artifact_id="fixture",
            name="../escape.bin",
            size_bytes=len(PAYLOAD),
            sha256=hashlib.sha256(PAYLOAD).hexdigest(),
            url=expectation().url,
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(DownloadError, "plain filename"):
                ResumableDownloader(open_url=FakeOpen([])).fetch(unsafe, Path(directory))


if __name__ == "__main__":
    unittest.main()
