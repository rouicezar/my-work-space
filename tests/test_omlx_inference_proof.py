"""Unit tests for the oMLX local-inference proof's honest evaluation logic."""

from __future__ import annotations

import unittest

from scripts.omlx_inference_proof import evaluate_completion, select_model


class _FakeTransport:
    def __init__(self, models: list[str]):
        self._models = models

    def request(self, method: str, path: str, payload=None):  # noqa: ANN001
        class _Result:
            pass

        result = _Result()
        result.status = 200
        result.body = {"data": [{"id": model} for model in self._models]}
        return result


class EvaluateCompletionTests(unittest.TestCase):
    def test_non_empty_content_passes(self) -> None:
        response = {
            "http_status": 200,
            "body": {
                "choices": [
                    {
                        "model": "Qwen3-0.6B-4bit",
                        "finish_reason": "stop",
                        "message": {"content": "FORMA_OK"},
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 3},
            },
        }
        evidence = evaluate_completion(response, "Qwen3-0.6B-4bit")
        self.assertEqual(evidence["status"], "proof_passed")
        self.assertEqual(evidence["content"], "FORMA_OK")
        self.assertEqual(evidence["finish_reason"], "stop")

    def test_empty_content_fails(self) -> None:
        response = {
            "http_status": 200,
            "body": {
                "choices": [{"model": "Qwen3-0.6B-4bit", "message": {"content": ""}}],
            },
        }
        evidence = evaluate_completion(response, "Qwen3-0.6B-4bit")
        self.assertEqual(evidence["status"], "proof_failed")
        self.assertEqual(evidence["reason"], "empty_content")

    def test_missing_choices_fails(self) -> None:
        evidence = evaluate_completion({"http_status": 200, "body": {}}, "Qwen3-0.6B-4bit")
        self.assertEqual(evidence["status"], "proof_failed")
        self.assertEqual(evidence["reason"], "no_choices")

    def test_http_error_fails(self) -> None:
        response = {
            "http_status": 500,
            "body": {
                "choices": [{"model": "Qwen3-0.6B-4bit", "message": {"content": "x"}}],
            },
        }
        evidence = evaluate_completion(response, "Qwen3-0.6B-4bit")
        self.assertEqual(evidence["status"], "proof_failed")
        self.assertEqual(evidence["reason"], "http_error")


class SelectModelTests(unittest.TestCase):
    def test_defaults_to_first_listed_model(self) -> None:
        transport = _FakeTransport(["Qwen3-0.6B-4bit"])
        self.assertEqual(select_model(transport, None), "Qwen3-0.6B-4bit")

    def test_matches_suffix(self) -> None:
        transport = _FakeTransport(["mlx-community/Qwen3-0.6B-4bit"])
        self.assertEqual(
            select_model(transport, "Qwen3-0.6B-4bit"), "mlx-community/Qwen3-0.6B-4bit"
        )


if __name__ == "__main__":
    unittest.main()
