from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/release_plan_validation.py"


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    old = '''    expected_status = (\n        "PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION"\n    )\n    actual_status = plan.get("execution", {}).get("domain_queue_status")\n    if actual_status != expected_status:\n        errors.append(\n            diagnostic(\n                PLAN_PATH,\n                "domain_queue",\n                "safe-continuation-pause",\n                expected_status,\n                actual_status,\n            )\n        )\n'''
    new = '''    safe_required = (\n        "PROJECT-STATE-RECONCILIATION-001",\n        "INDUSTRIALIZATION-PROGRAM-EXECUTION-001",\n        "MODULE-ACTIVATION-CONTRACT-001",\n        "SECRET-HYGIENE-001",\n        "DEPENDENCY-PROVENANCE-001",\n        "DEPLOYMENT-PROFILE-001",\n        "BACKUP-RESTORE-DRILL-001",\n        "SECURITY-BASELINE-001",\n    )\n    post_safe_foundations = (\n        "MODULE-REGISTRY-001",\n        "UX-PLATFORM-FOUNDATION-001",\n        "PAGE-TEMPLATE-LIBRARY-001",\n    )\n    safe_complete = all(\n        work_by_id.get(item_id, {}).get("status") == "ACCEPTED"\n        for item_id in safe_required\n    )\n    foundations_complete = all(\n        work_by_id.get(item_id, {}).get("status") == "ACCEPTED"\n        for item_id in post_safe_foundations\n    )\n    if not safe_complete:\n        expected_status = (\n            "PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION"\n        )\n    elif not foundations_complete:\n        expected_status = "PAUSED_PENDING_MODULE_REGISTRY_AND_UX_FOUNDATIONS"\n    else:\n        expected_status = "READY_FOR_PRODUCT_MODULE_DEVELOPMENT"\n    actual_status = plan.get("execution", {}).get("domain_queue_status")\n    if actual_status != expected_status:\n        errors.append(\n            diagnostic(\n                PLAN_PATH,\n                "domain_queue",\n                "domain-queue-state",\n                expected_status,\n                actual_status,\n            )\n        )\n'''
    if old not in text:
        raise RuntimeError("domain queue validator block not found")
    PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("POST_SAFE_QUEUE_CONTRACT=OK")


if __name__ == "__main__":
    main()
