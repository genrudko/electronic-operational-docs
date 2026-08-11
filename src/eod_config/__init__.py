from __future__ import annotations

import importlib.util
import sys
import types


def _install_packaged_test_compatibility() -> None:
    """Expose legacy test helpers only when repository-only tests are absent."""
    if "test" not in sys.argv:
        return

    try:
        fixture_spec = importlib.util.find_spec("tests.credential_fixtures")
    except (ImportError, ModuleNotFoundError, ValueError):
        fixture_spec = None
    if fixture_spec is not None:
        return

    from apps.system.tests import ephemeral_credential

    tests_package = sys.modules.get("tests")
    if tests_package is None:
        tests_package = types.ModuleType("tests")
        setattr(tests_package, "__path__", [])
        sys.modules["tests"] = tests_package

    fixture_module = types.ModuleType("tests.credential_fixtures")
    setattr(fixture_module, "ephemeral_credential", ephemeral_credential)
    sys.modules["tests.credential_fixtures"] = fixture_module
    setattr(tests_package, "credential_fixtures", fixture_module)


_install_packaged_test_compatibility()
