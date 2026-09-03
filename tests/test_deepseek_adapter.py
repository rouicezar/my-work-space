import json
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from forma_ai.broker import MemoryAuditSink
from forma_ai.cloud_approval import CloudApprovalError, CloudApprovalStore
from forma_ai.cloud_catalog import load_cloud_provider
from forma_ai.deepseek_adapter import DeepSeekAdapter, DeepSeekError
from forma_ai.inference_routing import (
    TaskRequirements, create_cloud_proposal,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, body: bytes, *, status=200, content_type="application/json", url=None):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.url = url or "https://api.deepseek.com/chat/completions"

    def read(self, size=-1):
        return self.body[:size] if size >= 0 else self.body

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

    def __call__(self, request, *, timeout):
        self.requests.append(request)
        return self.responses.pop(0)


def response(model="deepseek-v4-flash", content="云端结果"):
    return json.dumps({
        "id": "fixture", "object": "chat.completion", "model": model,
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 100, "prompt_cache_hit_tokens": 20,
                  "prompt_cache_miss_tokens": 80, "completion_tokens": 25,
                  "total_tokens": 125},
    }).encode()


class DeepSeekAdapterTests(unittest.TestCase):
    def setUp(self):
        self.provider = load_cloud_provider(ROOT / "config/cloud-providers.json", "deepseek")
        self.now = datetime(2026, 8, 30, 12, tzinfo=timezone.utc)
        self.requirements = TaskRequirements(
            100, 1000, frozenset({"chat"}), 1024, frozenset({"user_text"}),
        )

    def proposal(self):
        return create_cloud_proposal(
            correlation_id=str(uuid.uuid4()), provider=self.provider,
            model_id="deepseek-v4-flash", requirements=self.requirements,
            reason_codes=("required_capability_missing",),
            outbound_body={
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": "经过脱敏的任务"}],
                "max_tokens": 1000, "stream": False,
            },
            redactions=("removed-email-address",), now=self.now,
        )

    def test_exact_approved_payload_executes_once_normalizes_usage_and_redacts_audit(self):
        proposal, payload = self.proposal()
        opened = FakeOpen([FakeResponse(response())])
        audit = MemoryAuditSink()
        with tempfile.TemporaryDirectory() as directory:
            approvals = CloudApprovalStore(Path(directory))
            approvals.approve(
                proposal, maximum_cost_usd=proposal.estimated_cost.maximum, now=self.now,
            )
            adapter = DeepSeekAdapter(self.provider, approvals, audit, open_url=opened)
            result = adapter.execute(
                proposal, payload, api_key="fixture-deepseek-secret", now=self.now,
            )
            with self.assertRaises(CloudApprovalError) as replay:
                adapter.execute(
                    proposal, payload, api_key="fixture-deepseek-secret", now=self.now,
                )
        self.assertEqual(replay.exception.code, "APPROVAL_ALREADY_CONSUMED")
        self.assertEqual(result.content, "云端结果")
        self.assertEqual(result.usage.total_tokens, 125)
        self.assertGreater(result.usage.cost_usd, 0)
        self.assertEqual(opened.requests[0].data, payload)
        self.assertEqual(opened.requests[0].headers["Authorization"], "Bearer fixture-deepseek-secret")
        event = audit.events[0]
        self.assertEqual(event["outcome"], "completed")
        serialized = json.dumps(event, ensure_ascii=False)
        self.assertNotIn("经过脱敏的任务", serialized)
        self.assertNotIn("云端结果", serialized)
        self.assertNotIn("fixture-deepseek-secret", serialized)

    def test_payload_change_is_refused_before_network_and_does_not_consume_approval(self):
        proposal, payload = self.proposal()
        opened = FakeOpen([])
        with tempfile.TemporaryDirectory() as directory:
            approvals = CloudApprovalStore(Path(directory))
            approvals.approve(
                proposal, maximum_cost_usd=proposal.estimated_cost.maximum, now=self.now,
            )
            adapter = DeepSeekAdapter(self.provider, approvals, MemoryAuditSink(), open_url=opened)
            with self.assertRaises(CloudApprovalError) as mismatch:
                adapter.execute(
                    proposal, payload + b" ", api_key="fixture-key", now=self.now,
                )
        self.assertEqual(mismatch.exception.code, "APPROVAL_BINDING_MISMATCH")
        self.assertEqual(opened.requests, [])

    def test_expiry_and_cost_ceiling_fail_closed(self):
        proposal, payload = self.proposal()
        with tempfile.TemporaryDirectory() as directory:
            approvals = CloudApprovalStore(Path(directory))
            with self.assertRaises(CloudApprovalError) as cost:
                approvals.approve(
                    proposal, maximum_cost_usd=0, now=self.now,
                )
            approvals.approve(
                proposal, maximum_cost_usd=proposal.estimated_cost.maximum,
                now=self.now, ttl_seconds=1,
            )
            with self.assertRaises(CloudApprovalError) as expired:
                approvals.consume(proposal, payload, now=self.now + timedelta(seconds=2))
        self.assertEqual(cost.exception.code, "APPROVAL_COST_TOO_LOW")
        self.assertEqual(expired.exception.code, "APPROVAL_EXPIRED")

    def test_provider_http_failures_are_classified_and_audited_without_body(self):
        proposal, payload = self.proposal()
        audit = MemoryAuditSink()
        with tempfile.TemporaryDirectory() as directory:
            approvals = CloudApprovalStore(Path(directory))
            approvals.approve(
                proposal, maximum_cost_usd=proposal.estimated_cost.maximum, now=self.now,
            )
            adapter = DeepSeekAdapter(
                self.provider, approvals, audit,
                open_url=FakeOpen([FakeResponse(b'{"error":"secret detail"}', status=402)]),
            )
            with self.assertRaises(DeepSeekError) as raised:
                adapter.execute(proposal, payload, api_key="fixture-key", now=self.now)
        self.assertEqual(raised.exception.code, "DEEPSEEK_INSUFFICIENT_BALANCE")
        self.assertEqual(audit.events[0]["error_code"], "DEEPSEEK_INSUFFICIENT_BALANCE")
        self.assertNotIn("secret detail", json.dumps(audit.events[0]))

    def test_wrong_model_or_inconsistent_usage_is_rejected(self):
        for body, code in (
            (response(model="unexpected-model"), "DEEPSEEK_MODEL_MISMATCH"),
            (json.dumps({
                "model": "deepseek-v4-flash",
                "choices": [{"finish_reason": "stop", "message": {"content": "x"}}],
                "usage": {"prompt_tokens": 2, "prompt_cache_hit_tokens": 2,
                          "prompt_cache_miss_tokens": 2, "completion_tokens": 1,
                          "total_tokens": 3},
            }).encode(), "DEEPSEEK_USAGE_INVALID"),
        ):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                proposal, payload = self.proposal()
                approvals = CloudApprovalStore(Path(directory))
                approvals.approve(
                    proposal, maximum_cost_usd=proposal.estimated_cost.maximum, now=self.now,
                )
                adapter = DeepSeekAdapter(
                    self.provider, approvals, MemoryAuditSink(),
                    open_url=FakeOpen([FakeResponse(body)]),
                )
                with self.assertRaises(DeepSeekError) as raised:
                    adapter.execute(proposal, payload, api_key="fixture-key", now=self.now)
                self.assertEqual(raised.exception.code, code)

    def test_unexpected_transport_exception_is_classified_without_sensitive_detail(self):
        proposal, payload = self.proposal()
        audit = MemoryAuditSink()

        def unexpected(_request, *, timeout):
            self.assertEqual(timeout, 120.0)
            raise RuntimeError("private provider detail")

        with tempfile.TemporaryDirectory() as directory:
            approvals = CloudApprovalStore(Path(directory))
            approvals.approve(
                proposal, maximum_cost_usd=proposal.estimated_cost.maximum, now=self.now,
            )
            adapter = DeepSeekAdapter(
                self.provider, approvals, audit, open_url=unexpected,
            )
            with self.assertRaises(DeepSeekError) as raised:
                adapter.execute(proposal, payload, api_key="fixture-key", now=self.now)
        self.assertEqual(raised.exception.code, "DEEPSEEK_UNEXPECTED_FAILURE")
        self.assertEqual(audit.events[0]["error_type"], "RuntimeError")
        self.assertNotIn("private provider detail", json.dumps(audit.events[0]))

    def test_small_output_budget_empty_content_is_handled_honestly(self):
        proposal, payload = self.proposal()
        body = json.dumps({
            "id": "fixture", "object": "chat.completion", "model": "deepseek-v4-flash",
            "choices": [{"index": 0, "finish_reason": "length",
                         "message": {"role": "assistant", "content": ""}}],
            "usage": {"prompt_tokens": 100, "prompt_cache_hit_tokens": 20,
                      "prompt_cache_miss_tokens": 80, "completion_tokens": 8,
                      "total_tokens": 108},
        }).encode()
        with tempfile.TemporaryDirectory() as directory:
            approvals = CloudApprovalStore(Path(directory))
            approvals.approve(
                proposal, maximum_cost_usd=proposal.estimated_cost.maximum, now=self.now,
            )
            adapter = DeepSeekAdapter(
                self.provider, approvals, MemoryAuditSink(),
                open_url=FakeOpen([FakeResponse(body)]),
            )
            result = adapter.execute(proposal, payload, api_key="fixture-key", now=self.now)
        self.assertEqual(result.content, "")
        self.assertEqual(result.finish_reason, "length")

    def test_actual_cost_above_approval_ceiling_is_rejected(self):
        proposal, payload = self.proposal()
        body = json.dumps({
            "id": "fixture", "object": "chat.completion", "model": "deepseek-v4-flash",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": "expensive"}}],
            "usage": {"prompt_tokens": 100, "prompt_cache_hit_tokens": 0,
                      "prompt_cache_miss_tokens": 100, "completion_tokens": 5_000_000,
                      "total_tokens": 5_000_100},
        }).encode()
        audit = MemoryAuditSink()
        with tempfile.TemporaryDirectory() as directory:
            approvals = CloudApprovalStore(Path(directory))
            approvals.approve(
                proposal, maximum_cost_usd=proposal.estimated_cost.maximum, now=self.now,
            )
            adapter = DeepSeekAdapter(
                self.provider, approvals, audit,
                open_url=FakeOpen([FakeResponse(body)]),
            )
            with self.assertRaises(DeepSeekError) as raised:
                adapter.execute(proposal, payload, api_key="fixture-key", now=self.now)
        self.assertEqual(raised.exception.code, "DEEPSEEK_COST_CEILING_EXCEEDED")
        self.assertEqual(audit.events[0]["outcome"], "failed")
        self.assertEqual(audit.events[0]["error_code"], "DEEPSEEK_COST_CEILING_EXCEEDED")
        self.assertGreater(audit.events[0]["actual_cost_usd"], audit.events[0]["maximum_cost_usd"])


if __name__ == "__main__":
    unittest.main()
