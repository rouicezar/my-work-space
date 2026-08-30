import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mac_ai_work_os.cloud_catalog import load_cloud_provider
from mac_ai_work_os.cloud_proposals import CloudProposalError, CloudProposalStore
from mac_ai_work_os.inference_routing import TaskRequirements, create_cloud_proposal


ROOT = Path(__file__).resolve().parents[1]


def proposal():
    provider = load_cloud_provider(ROOT / "config/cloud-providers.json", "deepseek")
    return create_cloud_proposal(
        correlation_id=str(uuid.uuid4()), provider=provider,
        model_id="deepseek-v4-flash",
        requirements=TaskRequirements(
            100, 1000, frozenset({"chat"}), 1024, frozenset({"user_text"}),
        ),
        reason_codes=("local_unhealthy",),
        outbound_body={
            "model": "deepseek-v4-flash", "messages": [{"role": "user", "content": "x"}],
            "max_tokens": 1000, "stream": False,
        },
        redactions=(), now=datetime(2026, 8, 30, 12, tzinfo=timezone.utc),
    )


class CloudProposalStoreTests(unittest.TestCase):
    def test_private_round_trip_and_reject_remove_payload_and_metadata(self):
        item, payload = proposal()
        with tempfile.TemporaryDirectory() as directory:
            store = CloudProposalStore(Path(directory))
            store.save(item, payload)
            loaded, loaded_payload = store.load(item.proposal_id)
            self.assertEqual(loaded, item)
            self.assertEqual(loaded_payload, payload)
            state = Path(directory) / "state/cloud-proposals"
            self.assertEqual(state.stat().st_mode & 0o777, 0o700)
            self.assertEqual((state / f"{item.proposal_id}.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((state / f"{item.proposal_id}.payload").stat().st_mode & 0o777, 0o600)
            self.assertEqual(store.reject(item.proposal_id), item)
            self.assertEqual(list(state.glob(f"{item.proposal_id}.*")), [])

    def test_tampered_payload_is_rejected_and_cannot_be_silently_replaced(self):
        item, payload = proposal()
        with tempfile.TemporaryDirectory() as directory:
            store = CloudProposalStore(Path(directory))
            store.save(item, payload)
            state = Path(directory) / "state/cloud-proposals"
            body = state / f"{item.proposal_id}.payload"
            body.write_bytes(b"tampered")
            with self.assertRaises(CloudProposalError) as raised:
                store.load(item.proposal_id)
            with self.assertRaises(CloudProposalError) as duplicate:
                store.save(item, payload)
        self.assertEqual(raised.exception.code, "PROPOSAL_INVALID")
        self.assertEqual(duplicate.exception.code, "PROPOSAL_ALREADY_EXISTS")

    def test_invalid_id_and_symlink_payload_fail_closed(self):
        item, payload = proposal()
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            store = CloudProposalStore(Path(directory))
            with self.assertRaises(CloudProposalError):
                store.load("../escape")
            store.save(item, payload)
            body = Path(directory) / "state/cloud-proposals" / f"{item.proposal_id}.payload"
            body.unlink()
            body.symlink_to(Path(outside) / "victim")
            with self.assertRaises(CloudProposalError) as raised:
                store.load(item.proposal_id)
        self.assertEqual(raised.exception.code, "PROPOSAL_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
