#!/usr/bin/env python3
"""Focused owner-visible browser evidence for UX-PLATFORM Repair v4.

This runner deliberately executes the established 210-state baseline first and
then appends bounded Repair v4 evidence to the same computed-styles.json.
It does not seed or mutate domain data. Where a normative marker is absent in
the presentation fixture, a synthetic marker is inserted into the rendered DOM
only to exercise the real OPJ marker CSS/runtime geometry and tooltip portal.
"""

from __future__ import annotations

import json
import os
import re
import runpy
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
BASELINE = runpy.run_path(str(HERE / "run.py"), run_name="eod_browser_baseline")
BASELINE["main"]()

BASE = os.getenv("EOD_BROWSER_BASE_URL", "http://127.0.0.1:8766").rstrip("/")
OUT = Path(os.getenv("EOD_BROWSER_EVIDENCE", "artifacts/browser-theme"))
SHOTS = OUT / "screenshots"
ROUTES = BASELINE["ROUTES"]
THEMES = BASELINE["THEMES"]
need = BASELINE["need"]
theme = BASELINE["theme"]
screenshots = BASELINE["screenshots"]
bind_runtime_errors = BASELINE["bind_runtime_errors"]
clear_runtime_errors = BASELINE["clear_runtime_errors"]
runtime_error_snapshot = BASELINE["runtime_error_snapshot"]

MIN_SECONDARY_FONT_PX = 11.0


def node_metrics(node):
    return node.evaluate(
        """node => {
            const style = getComputedStyle(node);
            const rect = node.getBoundingClientRect();
            return {
                text: (node.innerText || node.textContent || '').replace(/\s+/g, ' ').trim(),
                display: style.display,
                visibility: style.visibility,
                opacity: Number.parseFloat(style.opacity || '1'),
                font_size: Number.parseFloat(style.fontSize || '0'),
                line_height: style.lineHeight,
                color: style.color,
                background: style.backgroundColor,
                border: style.borderColor,
                disabled: Boolean(node.disabled),
                box: {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    left: rect.left,
                    top: rect.top,
                    right: rect.right,
                    bottom: rect.bottom,
                },
            };
        }"""
    )


def visible_metrics(page, selector):
    locator = page.locator(f"{selector}:visible").first
    if not locator.count():
        return None
    return node_metrics(locator)


def login(page, password):
    clear_runtime_errors(page._eod_runtime_errors)
    page.goto(BASE + "/accounts/login/")
    need(page, "input[name=username]").fill(
        os.getenv("EOD_BROWSER_USERNAME", "operator.demo")
    )
    need(page, "input[name=password]").fill(password)
    need(page, "button[type=submit]").click()
    need(page, "[data-direction-a-shell]")


def discover_first(page, route, pattern):
    page.goto(BASE + route)
    hrefs = page.locator("a[href]").evaluate_all(
        "nodes => nodes.map(node => new URL(node.href).pathname)"
    )
    return next((href for href in hrefs if re.fullmatch(pattern, href)), None)


def ensure_synthetic_marker(page):
    marker = page.locator("[data-opj-marker]:visible").first
    if marker.count():
        return marker, False

    host = page.locator(".draft-ledger-visas:visible").first
    if not host.count():
        raise AssertionError("Repair v4 marker probe has no visible OPJ visas cell")
    host.evaluate(
        """host => {
            for (let index = 1; index <= 3; index += 1) {
                const marker = document.createElement('span');
                marker.className = 'draft-normative-marker opj-normative-marker is-pz_install';
                marker.tabIndex = 0;
                marker.dataset.opjMarker = '';
                marker.dataset.markerKind = 'pz_install';
                marker.dataset.markerNumber = String(108 + index);
                marker.dataset.markerCount = '1';
                marker.dataset.markerLabel = 'Проверочная нормативная отметка';
                marker.setAttribute('aria-label', `Проверочная нормативная отметка, №${108 + index}`);
                marker.innerHTML = [
                    '<span class="draft-normative-marker-top">ПЗ</span>',
                    '<span class="draft-normative-marker-bolt" aria-hidden="true">ϟ</span>',
                    `<span class="draft-normative-marker-bottom">№${108 + index}</span>`,
                    '<i class="draft-normative-marker-cross" aria-hidden="true"></i>',
                ].join('');
                host.append(marker);
            }
            window.__EOD_OPJ_MARKER_REFRESH_00612__?.();
        }"""
    )
    marker = page.locator("[data-opj-marker]:visible").first
    marker.wait_for(state="visible")
    return marker, True


def append_check(bucket, condition, message):
    if not condition:
        bucket.append(message)


def main():
    password = os.getenv("EOD_BROWSER_PASSWORD", "").strip()
    if not password:
        raise AssertionError("EOD_BROWSER_PASSWORD must be an ephemeral test credential")

    report_path = OUT / "computed-styles.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    focused = {
        "failures": [],
        "routes": {},
        "wide": {},
        "spread": {},
        "marker_edge": {},
        "marker_tooltip": {},
        "readability": {},
        "runtime_errors": {},
    }
    failures = focused["failures"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page._eod_runtime_errors = bind_runtime_errors(page)
        login(page, password)

        focused_routes = {
            "organizations": "/organization/",
            "equipment_detail": discover_first(
                page,
                ROUTES["equipment"],
                r"/equipment/items/[0-9a-f-]{36}/",
            ),
            "dispatching_detail": discover_first(
                page,
                ROUTES["dispatching"],
                r"/dispatching/equipment/[0-9a-f-]{36}/",
            ),
            "defect_detail": discover_first(
                page,
                ROUTES["defect_registry"],
                r"/operations/defects/[0-9a-f-]{36}/",
            ),
        }
        focused["routes"] = focused_routes

        for route_name, path in focused_routes.items():
            if not path:
                continue
            for mode in THEMES:
                clear_runtime_errors(page._eod_runtime_errors)
                page.goto(BASE + path)
                theme(page, mode)
                screenshots(page, SHOTS, f"repair_v4__{route_name}__{mode}__1920x1080")
                focused["runtime_errors"][f"{route_name}_{mode}"] = runtime_error_snapshot(
                    page._eod_runtime_errors
                )

        # UX-VIS-20: Development credential presentation remains readable.
        credential_context = browser.new_context(viewport={"width": 1920, "height": 1080})
        credential_page = credential_context.new_page()
        for mode in THEMES:
            credential_page.goto(BASE + "/accounts/login/")
            theme(credential_page, mode)
            note = visible_metrics(credential_page, ".ux-demo-access-note")
            focused["readability"][f"credential_note_{mode}"] = note
            if note:
                append_check(
                    failures,
                    note["font_size"] >= MIN_SECONDARY_FONT_PX,
                    f"credential note is too small in {mode}: {note['font_size']}px",
                )
                append_check(
                    failures,
                    note["opacity"] >= 0.95,
                    f"credential note is faded in {mode}: opacity {note['opacity']}",
                )
            screenshots(
                credential_page,
                SHOTS,
                f"repair_v4__development_credentials__{mode}__1920x1080",
            )
        credential_context.close()

        # UX-VIS-11/16: current-user context and secondary text must not become micro/faded.
        page.goto(BASE + ROUTES["home"])
        theme(page, "dark")
        sidebar_secondary = visible_metrics(page, ".da-nav-user span")
        focused["readability"]["sidebar_user_secondary_dark"] = sidebar_secondary
        if sidebar_secondary:
            append_check(
                failures,
                sidebar_secondary["font_size"] >= MIN_SECONDARY_FONT_PX,
                f"sidebar user context is too small: {sidebar_secondary['font_size']}px",
            )
            append_check(
                failures,
                sidebar_secondary["opacity"] >= 0.95,
                f"sidebar user context is faded: opacity {sidebar_secondary['opacity']}",
            )

        # UX-VIS-15/21: wide/full width and spread geometry on 1920 desktop.
        clear_runtime_errors(page._eod_runtime_errors)
        page.goto(BASE + ROUTES["draft_workspace"])
        theme(page, "dark")
        need(page, "[data-open-view-drawer]").click()
        need(page, '[data-page-width-choice="full"]').click()
        page.wait_for_function(
            "()=>document.querySelector('[data-draft-workspace]')?.dataset.pageWidth==='full'"
        )
        need(page, "[data-close-view-drawer]").click()
        workspace = need(page, "[data-draft-workspace]")
        workspace_metrics = node_metrics(workspace)
        viewport = page.evaluate("()=>({width: innerWidth, height: innerHeight})")
        focused["wide"] = {
            "workspace": workspace_metrics,
            "viewport": viewport,
            "ratio": workspace_metrics["box"]["width"] / viewport["width"],
        }
        append_check(
            failures,
            workspace_metrics["box"]["width"] >= 1450,
            f"OPJ full width underuses 1920 viewport: {workspace_metrics['box']['width']}px",
        )
        screenshots(page, SHOTS, "repair_v4__opj_full__dark__1920x1080")

        need(page, "[data-open-view-drawer]").click()
        need(page, '[data-view-mode="spread"]').click()
        page.wait_for_function(
            "()=>document.querySelector('[data-draft-workspace]')?.dataset.viewMode==='spread'"
        )
        need(page, "[data-close-view-drawer]").click()
        left = need(page, '[data-page-shell="left"]')
        right = need(page, '[data-page-shell="right"]')
        left_metrics = node_metrics(left)
        right_metrics = node_metrics(right)
        focused["spread"] = {
            "left": left_metrics,
            "right": right_metrics,
            "container": node_metrics(need(page, "[data-draft-book]")),
        }
        append_check(
            failures,
            left_metrics["box"]["height"] >= 300,
            f"OPJ spread left page collapsed: {left_metrics['box']['height']}px",
        )
        append_check(
            failures,
            right_metrics["box"]["height"] >= 300,
            f"OPJ spread right page collapsed: {right_metrics['box']['height']}px",
        )
        append_check(
            failures,
            abs(left_metrics["box"]["top"] - right_metrics["box"]["top"]) <= 4,
            "OPJ spread pages are vertically misaligned",
        )
        screenshots(page, SHOTS, "repair_v4__opj_spread__dark__1920x1080")

        # UX-VIS-07/16: disabled actions stay visible and toolbar captions are readable.
        disabled = visible_metrics(page, ".draft-row-action:disabled")
        caption = visible_metrics(page, ".opj-tool-group > small")
        focused["readability"]["opj_disabled_action_dark"] = disabled
        focused["readability"]["opj_toolbar_caption_dark"] = caption
        if disabled:
            append_check(
                failures,
                disabled["opacity"] >= 0.95,
                f"OPJ disabled action is faded: opacity {disabled['opacity']}",
            )
        if caption:
            append_check(
                failures,
                caption["font_size"] >= MIN_SECONDARY_FONT_PX,
                f"OPJ toolbar caption is too small: {caption['font_size']}px",
            )
            append_check(
                failures,
                caption["opacity"] >= 0.95,
                f"OPJ toolbar caption is faded: opacity {caption['opacity']}",
            )

        # UX-VIS-22/02: marker edge geometry and dark tooltip portal.
        marker, synthetic = ensure_synthetic_marker(page)
        host = marker.locator("xpath=ancestor::*[contains(@class,'draft-ledger-visas')][1]")
        marker_metrics = node_metrics(marker)
        host_metrics = node_metrics(host)
        focused["marker_edge"] = {
            "synthetic_fixture": synthetic,
            "marker": marker_metrics,
            "host": host_metrics,
        }
        append_check(
            failures,
            marker_metrics["box"]["left"] >= host_metrics["box"]["left"] - 1,
            "OPJ marker clips beyond the left edge of the visas column",
        )
        append_check(
            failures,
            marker_metrics["box"]["right"] <= host_metrics["box"]["right"] + 1,
            "OPJ marker clips beyond the right edge of the visas column",
        )

        marker.focus()
        popover = page.locator(".opj-marker-popover.is-floating:visible").first
        popover.wait_for(state="visible")
        tooltip_metrics = node_metrics(popover)
        focused["marker_tooltip"] = tooltip_metrics
        append_check(
            failures,
            tooltip_metrics["box"]["left"] >= 8,
            "OPJ marker tooltip leaves the left viewport edge",
        )
        append_check(
            failures,
            tooltip_metrics["box"]["right"] <= viewport["width"] - 8,
            "OPJ marker tooltip leaves the right viewport edge",
        )
        append_check(
            failures,
            tooltip_metrics["box"]["top"] >= 8,
            "OPJ marker tooltip leaves the top viewport edge",
        )
        append_check(
            failures,
            tooltip_metrics["box"]["bottom"] <= viewport["height"] - 8,
            "OPJ marker tooltip leaves the bottom viewport edge",
        )
        append_check(
            failures,
            tooltip_metrics["opacity"] >= 0.95,
            f"OPJ marker tooltip is faded: opacity {tooltip_metrics['opacity']}",
        )
        append_check(
            failures,
            tooltip_metrics["background"] not in {"rgba(0, 0, 0, 0)", "transparent"},
            "OPJ marker tooltip has transparent background",
        )
        screenshots(page, SHOTS, "repair_v4__opj_marker_tooltip__dark__1920x1080")

        # UX-VIS-06/08/09/16: lifecycle cards and status stay legible in dark mode.
        defect_path = focused_routes.get("defect_detail")
        if defect_path:
            page.goto(BASE + defect_path)
            theme(page, "dark")
            lifecycle_step = visible_metrics(page, ".defect-da-lifecycle-card .defect-lifecycle li")
            lifecycle_small = visible_metrics(
                page, ".defect-da-lifecycle-card .defect-lifecycle li small"
            )
            status = visible_metrics(page, ".defect-da-status")
            focused["readability"]["defect_lifecycle_dark"] = lifecycle_step
            focused["readability"]["defect_lifecycle_secondary_dark"] = lifecycle_small
            focused["readability"]["defect_status_dark"] = status
            if lifecycle_step:
                append_check(
                    failures,
                    lifecycle_step["opacity"] >= 0.95,
                    f"DEFECT lifecycle card is faded: opacity {lifecycle_step['opacity']}",
                )
            if lifecycle_small:
                append_check(
                    failures,
                    lifecycle_small["font_size"] >= MIN_SECONDARY_FONT_PX,
                    f"DEFECT lifecycle secondary text is too small: {lifecycle_small['font_size']}px",
                )
            if status:
                append_check(
                    failures,
                    status["box"]["width"] >= 60 and status["box"]["height"] >= 28,
                    "DEFECT status chip geometry is too small",
                )

        focused["runtime_errors"]["focused_opj"] = runtime_error_snapshot(
            page._eod_runtime_errors
        )
        browser.close()

    focused["verdict"] = "PASS" if not failures else "FAIL"
    report["repair_v4"] = focused
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Repair v4 focused browser evidence: {focused['verdict']}")
    for failure in failures:
        print(f"REPAIR_V4_FAILURE: {failure}")


if __name__ == "__main__":
    main()
