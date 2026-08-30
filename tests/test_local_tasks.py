import json
import unittest

from mac_ai_work_os.local_tasks import (
    LocalTaskError, completion_body, normalize_local_result, parse_local_task,
)


class LocalTaskContractTests(unittest.TestCase):
    def test_valid_task_builds_bounded_nonstreaming_local_request(self):
        task = parse_local_task(json.dumps({
            "schema_version": 1, "prompt": "请总结这段文字", "maximum_output_tokens": 512,
        }).encode())
        body = completion_body(task, "local-qwen")
        self.assertEqual(body["messages"][0]["content"], "请总结这段文字")
        self.assertEqual(body["max_tokens"], 512)
        self.assertFalse(body["stream"])
        self.assertFalse(body["chat_template_kwargs"]["enable_thinking"])

    def test_schema_prompt_and_output_limits_fail_closed(self):
        fixtures = (
            (b"not-json", "LOCAL_TASK_JSON_INVALID"),
            (json.dumps({"schema_version": 1, "prompt": " ", "maximum_output_tokens": 1}).encode(), "LOCAL_TASK_PROMPT_INVALID"),
            (json.dumps({"schema_version": 1, "prompt": "x", "maximum_output_tokens": 4097}).encode(), "LOCAL_TASK_OUTPUT_LIMIT_INVALID"),
            (json.dumps({"schema_version": 1, "prompt": "x", "maximum_output_tokens": 1, "extra": True}).encode(), "LOCAL_TASK_SCHEMA_INVALID"),
        )
        for data, code in fixtures:
            with self.subTest(code=code), self.assertRaises(LocalTaskError) as raised:
                parse_local_task(data)
            self.assertEqual(raised.exception.code, code)

    def test_normalized_result_is_explicitly_local_and_usage_consistent(self):
        result = normalize_local_result({
            "model": "local-qwen",
            "choices": [{"message": {"content": "结果"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        }, correlation_id="correlation", expected_model="local-qwen")
        self.assertEqual(result.route, "local")
        self.assertEqual(result.output, "结果")
        self.assertEqual(result.total_tokens, 12)

    def test_empty_output_tool_call_model_mismatch_and_bad_usage_are_rejected(self):
        fixtures = (
            {"model": "other", "choices": [{"message": {"content": "x"}, "finish_reason": "stop"}]},
            {"model": "local", "choices": [{"message": {"content": ""}, "finish_reason": "stop"}]},
            {"model": "local", "choices": [{"message": {"content": "x", "tool_calls": [{}]}, "finish_reason": "stop"}]},
            {"model": "local", "choices": [{"message": {"content": "x"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 3}},
        )
        for response in fixtures:
            with self.subTest(response=response), self.assertRaises(LocalTaskError):
                normalize_local_result(response, correlation_id="c", expected_model="local")


if __name__ == "__main__":
    unittest.main()
