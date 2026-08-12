#!/usr/bin/env python3
# ruff: noqa: E501
"""Repair v5 visual normalization evidence.

1920x1080 is the normative desktop acceptance viewport. 2560x1440 is retained
only as a supplemental wide-screen stress case. Tablet and mobile regression
coverage is inherited from the focused Repair v4 owner-walkthrough runner.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PRIMARY_DESKTOP = {"width": 1920, "height": 1080}
WIDE_STRESS = {"width": 2560, "height": 1440}
TABLET = {"width": 1024, "height": 768}
MOBILE = {"width": 390, "height": 844}


def load_repair_v4():
    spec = importlib.util.spec_from_file_location("eod_repair_v4", HERE / "repair_v4.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Repair v4 browser evidence helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    password = os.getenv("EOD_BROWSER_PASSWORD", "").strip()
    if not password:
        raise AssertionError("EOD_BROWSER_PASSWORD must be an ephemeral test credential")

    mod = load_repair_v4()
    out = Path(os.getenv("EOD_BROWSER_EVIDENCE", "artifacts/browser-theme"))
    shots = out / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    shots.mkdir(parents=True, exist_ok=True)

    # Repair v5 deliberately makes every representative desktop/wide Repair v4
    # stress case execute at Full HD. The former 2560 and 1440 screenshot suffixes
    # are normalized to the actual 1920 acceptance viewport.
    mod.WIDE = PRIMARY_DESKTOP.copy()
    mod.DESKTOP = PRIMARY_DESKTOP.copy()
    mod.TABLET = TABLET.copy()
    mod.MOBILE = MOBILE.copy()
    mod.OUT = out
    mod.SHOTS = shots

    def evidence_shot(page, name: str, *, full_page: bool = True) -> None:
        normalized = name.replace("__2560", "__1920").replace("__1440", "__1920")
        page.screenshot(path=shots / f"{normalized}.png", full_page=full_page)

    mod.shot = evidence_shot

    # Repair v4's absolute >=1800px OPJ assertion was valid only when its WIDE
    # viewport was 2560px. Repair v5 replaces that one stale absolute threshold
    # with a relative Full-HD stage-utilisation check below; all other v4 checks
    # continue to fail closed without weakening.
    v4_check = mod.check

    def repair_v5_check(failures: list[str], condition: bool, message: str) -> None:
        if message.startswith("OPJ full width compressed at 2560:"):
            return
        v4_check(failures, condition, message)

    mod.check = repair_v5_check

    failures: list[str] = []
    report: dict[str, object] = {
        "meta": {
            "scope": "UX-PLATFORM-FOUNDATION-001 Repair v5 visual normalization evidence",
            "desktopAcceptancePolicy": "1920x1080 is normative; 2560x1440 is supplemental wide stress only",
            "baseUrl": mod.BASE,
            "viewports": {
                "primaryDesktop": PRIMARY_DESKTOP,
                "wideStress": WIDE_STRESS,
                "tablet": TABLET,
                "mobile": MOBILE,
            },
        }
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # Run the complete representative owner walkthrough with both former
        # desktop and former wide cases constrained to the normative Full HD
        # viewport.
        mod.public_import_structured(browser, failures, report)
        page = browser.new_page(viewport=PRIMARY_DESKTOP)
        mod.login(page, password)
        routes = mod.discover(page)
        report["meta"]["routes"] = routes
        mod.organization_workplace(page, routes, failures, report)
        mod.defect_states(page, routes, failures, report)
        mod.opj_states(page, routes, failures, report)

        # Validate the "Полная" OPJ profile against the actual usable Full-HD
        # workspace, not against an absolute 2K-era pixel count. A full workspace
        # must consume essentially the complete main content box after the fixed
        # sidebar and canonical page gutters are accounted for.
        draft = routes.get("draft_opj")
        if draft:
            page.set_viewport_size(PRIMARY_DESKTOP)
            page.goto(mod.BASE + draft)
            mod.theme(page, "dark")
            workspace = mod.need(page, "[data-draft-workspace]")
            if workspace.get_attribute("data-page-width") != "full":
                mod.need(page, "[data-open-view-drawer]").click()
                drawer = mod.need(page, "[data-view-drawer]")
                drawer.locator('[data-page-width-choice="full"]:visible').click()
                page.wait_for_function("()=>document.querySelector('[data-draft-workspace]')?.dataset.pageWidth==='full'")
                close = drawer.locator("[data-close-view-drawer]").first
                if close.count():
                    close.evaluate("node=>node.click()")
                    page.wait_for_function("()=>document.querySelector('[data-view-drawer]')?.hidden===true")
            workspace_state = mod.metrics(workspace)
            main_node = mod.need(page, "main.opj-shift-main")
            main_state = mod.metrics(main_node)
            workspace_width = float(workspace_state["box"]["width"])
            main_width = float(main_state["box"]["width"])
            utilisation = workspace_width / main_width if main_width else 0.0
            v4_check(
                failures,
                utilisation >= 0.98,
                f"OPJ full profile does not consume Full HD main workspace: utilisation={utilisation:.3f}, workspace={workspace_state['box']}, main={main_state['box']}",
            )
            report["opjPrimaryDesktopFullWidth"] = {
                "workspace": workspace_state,
                "main": main_state,
                "utilisation": round(utilisation, 4),
            }
            evidence_shot(page, "opj_full_width_primary__dark__1920")

        mod.equipment_dispatching(page, routes, failures, report)
        mod.account_mobile(page, routes, failures, report)
        page.close()

        # 2K is not the design target. It is a bounded supplemental check that
        # the wider canvas does not introduce document overflow or pathological
        # whitespace on representative high-density surfaces.
        context = browser.new_context(viewport=WIDE_STRESS)
        wide = context.new_page()
        wide.goto(mod.BASE + "/")
        mod.theme(wide, "light")
        wide_states: dict[str, object] = {
            "publicHome": mod.check_width(wide, failures, "public home 2560 supplemental")
        }
        evidence_shot(wide, "wide_stress_public_home__light__2560")

        mod.login(wide, password)
        representative = [
            ("organization", "/organization/"),
            ("imports", "/imports/"),
            ("structuredJournals", "/operational-documents/"),
        ]
        if routes.get("registered_opj"):
            representative.append(("operationalJournal", routes["registered_opj"]))

        for name, route in representative:
            wide.goto(mod.BASE + route)
            mod.theme(wide, "light")
            width_state = mod.check_width(wide, failures, f"{name} 2560 supplemental")
            main_node = wide.locator("main:visible").first
            main_state = mod.metrics(main_node) if main_node.count() else None
            wide_states[name] = {"width": width_state, "main": main_state}
            evidence_shot(wide, f"wide_stress_{name}__light__2560")

        report["wideStress2560"] = wide_states
        context.close()
        browser.close()

    report["meta"]["screenshotCount"] = len(list(shots.glob("*.png")))
    report["failures"] = failures
    report["verdict"] = "PASS" if not failures else "FAIL"
    (out / "computed-styles.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Repair v5 visual normalization evidence: {report['verdict']}")
    print("Primary desktop acceptance viewport: 1920x1080")
    print("Supplemental wide stress viewport: 2560x1440")
    for failure in failures:
        print(f"REPAIR_V5_FAILURE: {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
