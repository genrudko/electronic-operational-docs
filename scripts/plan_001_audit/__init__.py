from __future__ import annotations

import sys

from apps.system.plan_001_audit import core, django_evidence, package, source_evidence

sys.modules[f"{__name__}.core"] = core
sys.modules[f"{__name__}.django_evidence"] = django_evidence
sys.modules[f"{__name__}.package"] = package
sys.modules[f"{__name__}.source_evidence"] = source_evidence
