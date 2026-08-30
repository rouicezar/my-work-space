import unittest
from unittest.mock import patch

from forma_ai.system_resources import measure_available_memory, parse_vm_stat


class SystemResourceTests(unittest.TestCase):
    def test_parses_only_conservative_available_page_classes(self):
        report = parse_vm_stat("""Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                               1000.
Pages active:                             9999.
Pages inactive:                           2000.
Pages speculative:                         500.
Pages wired down:                         9999.
""")
        self.assertTrue(report.verified)
        self.assertEqual(report.available_memory_mb, 54)
        self.assertEqual(report.code, "AVAILABLE_MEMORY_MEASURED")

    def test_missing_header_or_required_class_is_unknown_not_zero_success(self):
        for output in ("", "page size of 0 bytes\nPages free: 1.",
                       "page size of 4096 bytes\nPages free: 1."):
            with self.subTest(output=output):
                report = parse_vm_stat(output)
                self.assertFalse(report.verified)
                self.assertEqual(report.available_memory_mb, 0)

    def test_command_failure_is_unknown(self):
        result = type("Result", (), {"returncode": 1, "stdout": ""})()
        with patch("subprocess.run", return_value=result):
            self.assertFalse(measure_available_memory().verified)


if __name__ == "__main__":
    unittest.main()
