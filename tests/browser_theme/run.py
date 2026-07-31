#!/usr/bin/env python3
"""Blocking browser evidence for seven theme routes."""

import json
import os
import re
from pathlib import Path
from uuid import UUID

from playwright.sync_api import sync_playwright

BASE = os.getenv("EOD_BROWSER_BASE_URL", "http://127.0.0.1:8766").rstrip("/")
OUT = Path(os.getenv("EOD_BROWSER_EVIDENCE", "artifacts/browser-theme"))
VIEWPORTS = ((1440, 900), (1024, 768), (390, 844))
THEMES = ("light", "dark")
ROUTES = {
    "home": "/",
    "defect_registry": "/operations/defects/",
    "opj_registry": "/operations/journal/",
    "account_settings": "/accounts/me/",
}
SELECTORS = {
    "home": ".metric.da-card",
    "defect_registry": ".defect-da-work-table",
    "defect_detail": ".defect-record-section",
    "opj_registry": ".journal-registry-card",
    "registered_opj": ".approved-journal-shell",
    "draft_workspace": ".opj-workspace",
    "account_settings": ".account-setting-card",
}
TOKENS = {
    "home": "--theme-surface",
    "defect_registry": "--theme-surface",
    "defect_detail": "--theme-surface",
    "opj_registry": "--theme-surface",
    "registered_opj": "--theme-surface-document",
    "draft_workspace": "--theme-surface",
    "account_settings": "--theme-surface",
}


def need(page, selector):
    node = page.locator(selector).first
    if not node.count():
        raise AssertionError(f"missing {selector} at {page.url}")
    node.wait_for(state="visible")
    return node


def style(node):
    return node.evaluate(
        """n => { const s=getComputedStyle(n); return {
            background:s.backgroundColor, border:s.borderColor,
            color:s.color, scheme:s.colorScheme}; }"""
    )


def resolved_background(page, token):
    return page.locator("html").evaluate(
        """(root, token) => {
            const probe = document.createElement("span");
            probe.style.backgroundColor = `var(${token})`;
            probe.style.display = "none";
            root.appendChild(probe);
            const value = getComputedStyle(probe).backgroundColor;
            probe.remove();
            return value;
        }""",
        token,
    )


def theme(page, value):
    available = page.evaluate(
        "()=>Boolean(window.EODTheme && typeof window.EODTheme.apply === 'function')"
    )
    if not available:
        raise AssertionError(f"missing window.EODTheme at {page.url}")
    page.evaluate("v=>window.EODTheme.apply(v,'browser-theme')", value)
    page.wait_for_function("v=>document.documentElement.dataset.theme===v", arg=value)


def defect_detail_path(hrefs):
    for href in hrefs:
        match = re.fullmatch(r"/operations/defects/([^/]+)/", href)
        if not match:
            continue
        try:
            UUID(match.group(1))
        except ValueError:
            continue
        return href
    raise AssertionError(f"missing UUID defect detail link: {hrefs}")


def discover(page):
    page.goto(BASE + ROUTES["defect_registry"])
    hrefs = page.locator('a[href*="/operations/defects/"]').evaluate_all(
        "ns=>ns.map(n=>new URL(n.href).pathname)"
    )
    ROUTES["defect_detail"] = defect_detail_path(hrefs)
    page.goto(BASE + ROUTES["opj_registry"])
    hrefs = page.locator('a[href*="/operations/journal/"]').evaluate_all(
        "ns=>ns.map(n=>new URL(n.href).pathname)"
    )
    ROUTES["registered_opj"] = next(h for h in hrefs if re.fullmatch(r"/operations/journal/\d+/", h))
    page.goto(BASE + ROUTES["registered_opj"])
    ROUTES["draft_workspace"] = need(page, 'a[href*="/shift/"]').evaluate("n=>new URL(n.href).pathname")


def main():
    shots = OUT / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    report = {"baseline": {}, "open_states": {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/accounts/login/")
        need(page, "input[name=username]").fill(os.getenv("EOD_BROWSER_USERNAME", "operator.demo"))
        need(page, "input[name=password]").fill(os.getenv("EOD_BROWSER_PASSWORD", "EodDemo!2026"))
        need(page, "button[type=submit]").click()
        discover(page)
        for route, path in ROUTES.items():
            for mode in THEMES:
                for width, height in VIEWPORTS:
                    page.set_viewport_size({"width": width, "height": height})
                    page.goto(BASE + path)
                    theme(page, mode)
                    node = need(page, SELECTORS[route])
                    actual = style(node)
                    expected = resolved_background(page, TOKENS[route])
                    key = f"{route}__{mode}__{width}x{height}"
                    report["baseline"][key] = {**actual, "expected_background": expected}
                    page.screenshot(path=shots / f"{key}.png", full_page=True)
                    if (
                        actual["background"].replace(" ", "") != expected.replace(" ", "")
                        or mode not in style(page.locator("html"))["scheme"].split()
                    ):
                        raise AssertionError(f"theme mismatch {route} {mode}: {actual} {expected}")
        if len(report["baseline"]) != 42:
            raise AssertionError("must contain exactly 42 files")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(BASE + ROUTES["defect_registry"])
        theme(page, "dark")
        need(page, ".defect-filter-drawer > summary").click()
        report["open_states"]["defect_filters"] = style(need(page, ".defect-filter-grid"))
        page.goto(BASE + "/operations/defects/new/")
        theme(page, "dark")
        need(page, ".defect-picker-trigger").click()
        picker = need(page, ".defect-picker-panel")
        report["open_states"]["defect_datetime"] = style(picker)
        page.keyboard.press("Escape")
        picker.wait_for(state="hidden")
        for kind in ("equipment", "personnel", "workplace"):
            field = need(page, f".defect-tree-selector--{kind} .defect-tree-input")
            field.click()
            report["open_states"][kind] = style(
                need(page, f".defect-tree-selector--{kind} .defect-tree-panel")
            )
            field.press("Escape")
        page.goto(BASE + ROUTES["registered_opj"])
        theme(page, "dark")
        need(page, ".journal-settings-trigger").click()
        report["open_states"]["opj_settings"] = style(need(page, ".journal-settings-dialog"))
        page.goto(BASE + ROUTES["draft_workspace"])
        theme(page, "dark")
        need(page, "[data-open-view-drawer]").click()
        report["open_states"]["opj_drawer"] = style(need(page, "[data-view-drawer]"))
        need(page, "[data-close-view-drawer]").click()
        need(page, '.draft-rich-editor-host [contenteditable="true"]').click()
        need(page, "[data-reference-trigger]:not([disabled])").click()
        report["open_states"]["opj_reference"] = style(need(page, "[data-reference-picker]"))
        page.goto(BASE + ROUTES["account_settings"])
        theme(page, "dark")
        select = need(page, '.interface-settings-form select[name="theme"]')
        select.focus()
        report["open_states"]["account_theme"] = style(select)
        page.goto(BASE + ROUTES["registered_opj"])
        theme(page, "dark")
        page.emulate_media(media="print")
        printed = style(page.locator("html"))
        report["print"] = printed
        if "light" not in printed["scheme"]:
            raise AssertionError("print isolation failed")
        browser.close()
    (OUT / "computed-styles.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
