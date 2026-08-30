import json
import unittest
from dataclasses import replace
from pathlib import Path

from mac_ai_work_os.cloud_preferences import CloudPreferenceState
from mac_ai_work_os.local_profiles import load_local_profile
from mac_ai_work_os.task_orchestrator import (
    TaskOrchestratorError, estimate_input_tokens, parse_unified_task, plan_unified_task,
)


ROOT = Path(__file__).resolve().parents[1]


def task(prompt="短任务", output=32, capabilities=("chat",), classes=("user_text",)):
    return parse_unified_task(json.dumps({
        "schema_version": 1, "prompt": prompt, "maximum_output_tokens": output,
        "required_capabilities": list(capabilities), "data_classes": list(classes),
    }, ensure_ascii=False).encode())


def profile():
    return load_local_profile(
        ROOT / "config/local-model-profiles.json", "qwen3-0.6b-4bit-apple-silicon-alpha",
        known_model_ids=frozenset({"qwen3-0.6b-4bit-alpha"}),
        known_hardware_profile_ids=frozenset({
            "apple-silicon-16gb", "apple-silicon-32gb", "apple-silicon-64gb",
        }), repository_root=ROOT,
    )


def cloud(enabled=False, valid=True):
    return CloudPreferenceState(
        1, enabled, "deepseek" if enabled else None,
        "deepseek-v4-flash" if enabled else None, valid,
        "CLOUD_ENABLED" if enabled else "CLOUD_DISABLED", "now",
    )


class TaskOrchestratorTests(unittest.TestCase):
    def test_short_verified_healthy_chat_stays_local_even_when_cloud_enabled(self):
        plan, requirements, decision = plan_unified_task(
            task(), profile=profile(), runtime_healthy=True,
            available_memory_mb=1024, cloud=cloud(True),
        )
        self.assertEqual(plan.route, "local")
        self.assertEqual(decision.reasons, ())
        self.assertGreater(requirements.estimated_input_tokens, 0)

    def test_every_local_boundary_can_create_only_an_offline_proposal_when_enabled(self):
        fixtures = (
            (replace(profile(), evidence_status="provisional_single_machine"), True, 1024, task(), "local_profile_unverified"),
            (profile(), False, 1024, task(), "local_unhealthy"),
            (profile(), True, 0, task(), "local_resource_insufficient"),
            (profile(), True, 1024, task(capabilities=("tools",)), "required_capability_missing"),
            (profile(), True, 1024, task(prompt="很长" * 100), "context_exceeds_local_limit"),
            (profile(), True, 1024, task(output=65), "local_output_limit_exceeded"),
        )
        for item, healthy, memory, request, reason in fixtures:
            with self.subTest(reason=reason):
                plan, _, _ = plan_unified_task(
                    request, profile=item, runtime_healthy=healthy,
                    available_memory_mb=memory, cloud=cloud(True),
                )
                self.assertEqual(plan.route, "cloud_proposal_required")
                self.assertIn(reason, plan.reason_codes)

    def test_disabled_or_invalid_cloud_returns_capability_unavailable(self):
        for state in (cloud(False), cloud(True, valid=False)):
            with self.subTest(state=state):
                plan, _, _ = plan_unified_task(
                    task(capabilities=("tools",)), profile=profile(), runtime_healthy=True,
                    available_memory_mb=1024, cloud=state,
                )
                self.assertEqual(plan.route, "capability_unavailable")
                self.assertFalse(plan.cloud_enabled)

    def test_prompt_estimate_is_conservative_and_schema_is_strict(self):
        self.assertEqual(estimate_input_tokens("abcd"), 2)
        self.assertEqual(estimate_input_tokens("你好"), 3)
        with self.assertRaises(TaskOrchestratorError):
            parse_unified_task(json.dumps({
                "schema_version": 1, "prompt": "x", "maximum_output_tokens": 1,
                "required_capabilities": ["chat"], "data_classes": ["user_text"],
                "extra": True,
            }).encode())


if __name__ == "__main__":
    unittest.main()
