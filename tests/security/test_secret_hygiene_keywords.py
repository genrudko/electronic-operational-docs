from __future__ import annotations

import unittest

from scripts.secret_hygiene_keyword_scan import scan_python_keyword_literals


class SensitiveKeywordLiteralTests(unittest.TestCase):
    def test_committed_keyword_literal_is_detected_without_disclosure(self) -> None:
        value = "".join(("Committed", "Keyword", "Credential!"))
        source = "authenticate(username='demo', password=" + repr(value) + ")"
        findings = scan_python_keyword_literals("app/service.py", source)
        self.assertEqual({item.rule for item in findings}, {"sensitive-keyword-literal"})
        self.assertNotIn(value, findings[0].diagnostic())

    def test_named_test_fixture_keyword_is_safe(self) -> None:
        value = "".join(("Fixture", "Only", "Test", "Credential!"))
        source = "authenticate(username='demo', password=" + repr(value) + ")"
        self.assertEqual(
            scan_python_keyword_literals("tests/test_login.py", source),
            [],
        )

    def test_runtime_keyword_value_is_safe(self) -> None:
        source = "authenticate(username='demo', password=injected_password)"
        self.assertEqual(
            scan_python_keyword_literals("app/service.py", source),
            [],
        )


if __name__ == "__main__":
    unittest.main()
