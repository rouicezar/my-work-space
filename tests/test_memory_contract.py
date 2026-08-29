import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MemoryContractTests(unittest.TestCase):
    def test_schema_is_closed_versioned_and_requires_governance_fields(self):
        schema = json.loads(
            (ROOT / "config/schemas/memory-record-v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertFalse(schema["additionalProperties"])
        required = set(schema["required"])
        self.assertTrue({
            "record_id", "claim_key", "content", "status", "version",
            "sources", "correlation_id", "created_at", "updated_at",
        }.issubset(required))
        self.assertGreaterEqual(schema["properties"]["sources"]["minItems"], 1)
        self.assertNotIn("deleted", schema["properties"]["status"]["enum"])

    def test_deleted_content_is_intentionally_not_a_memory_record(self):
        schema = json.loads(
            (ROOT / "config/schemas/memory-record-v1.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("deleted", schema["properties"]["status"]["enum"])


if __name__ == "__main__":
    unittest.main()
