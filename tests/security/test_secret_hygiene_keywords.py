from __future__ import annotations

import unittest

from scripts.secret_hygiene import scan_python_keyword_literals


def _credential_value(label: str) -> str:
    return "".join((label, "Credential", "!2026", "-", "LongValue"))


def _source(value: str) -> str:
    keyword_name = "".join(("pass", "word"))
    return "authenticate(username='demo', " + keyword_name + "=" + repr(value) + ")"


class SensitiveKeywordLiteralTests(unittest.TestCase):
    def test_credential_keyword_literal_is_blocked_in_product_source(self) -> None:
        value = _credential_value("Product")
        findings = scan_python_keyword_literals("app/service.py", _source(value))
        self.assertEqual({item.rule for item in findings}, {"sensitive-keyword-literal"})
        self.assertNotIn(value, findings[0].diagnostic())

    def test_credential_keyword_literal_is_blocked_in_test_source(self) -> None:
        value = _credential_value("TestPath")
        findings = scan_python_keyword_literals("tests/test_login.py", _source(value))
        self.assertEqual({item.rule for item in findings}, {"sensitive-keyword-literal"})

    def test_test_or_fixture_substring_is_not_an_exemption(self) -> None:
        for label in ("IncludesTest", "IncludesFixture"):
            with self.subTest(label=label):
                findings = scan_python_keyword_literals(
                    "tests/test_login.py",
                    _source(_credential_value(label)),
                )
                self.assertEqual(
                    {item.rule for item in findings},
                    {"sensitive-keyword-literal"},
                )

    def test_runtime_keyword_value_is_safe(self) -> None:
        keyword_name = "".join(("pass", "word"))
        source = "authenticate(username='demo', " + keyword_name + "=injected_value)"
        self.assertEqual(scan_python_keyword_literals("app/service.py", source), [])


if __name__ == "__main__":
    unittest.main()
