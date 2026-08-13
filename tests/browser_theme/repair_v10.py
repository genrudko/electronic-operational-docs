#!/usr/bin/env python3
"""Focused rendered geometry gate for UX-PLATFORM-FOUNDATION-001 Repair v10."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = os.getenv("EOD_BROWSER_BASE_URL", "http://127.0.0.1:8766").rstrip("/")
OUT = Path(os.getenv("EOD_BROWSER_EVIDENCE", "artifacts/browser-theme")) / "repair-v10"
DESKTOPS = ((1920, 1080), (2560, 1440))
MOBILES = ((390, 844), (430, 932))
THEMES = ("light", "dark")


def need(page: Page, selector: str):
    node = page.locator(selector).first
    if not node.count():
        raise AssertionError(f"missing {selector} at {page.url}")
    node.wait_for(state="visible")
    return node


def theme(page: Page, value: str) -> None:
    page.evaluate("v => window.EODTheme.apply(v, 'repair-v10')", value)
    page.wait_for_function("v => document.documentElement.dataset.theme === v", arg=value)


def no_page_overflow(page: Page, context: str) -> dict[str, float]:
    state = page.evaluate(
        """() => ({
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: window.innerWidth,
        })"""
    )
    if state["scrollWidth"] > state["innerWidth"] + 2:
        raise AssertionError(f"page overflow {context}: {state}")
    return state


def discover_record_detail(page: Page) -> str:
    page.goto(BASE + "/operational-documents/")
    hrefs = page.locator('a[href^="/operational-documents/"]').evaluate_all(
        "nodes => nodes.map(node => new URL(node.href).pathname)"
    )
    pattern = re.compile(r"^/operational-documents/[0-9a-fA-F-]{36}/$")
    try:
        return next(path for path in hrefs if pattern.fullmatch(path))
    except StopIteration as error:
        raise AssertionError("Repair v10 geometry requires one demo operational document") from error


def assert_registry_geometry(page: Page, width: int, height: int) -> dict[str, object]:
    need(page, ".opdoc-filter-card + .da-card")
    need(page, ".opdoc-date-range")
    need(page, ".opdoc-filter-grid > .ux-form-actions")
    need(page, ".opdoc-page-header h1")
    need(page, ".opdoc-page-header .ux-kicker")

    state = page.evaluate(
        """() => {
            const card = document.querySelector('.opdoc-filter-card + .da-card');
            const dates = [...document.querySelectorAll('.opdoc-date-range > .da-field')];
            const actions = document.querySelector('.opdoc-filter-grid > .ux-form-actions');
            const heading = document.querySelector('.opdoc-page-header h1');
            const kicker = document.querySelector('.opdoc-page-header .ux-kicker');
            const rect = node => node.getBoundingClientRect();
            return {
                tableTop: rect(card).top,
                dateRows: dates.map(node => ({top: rect(node).top, width: rect(node).width})),
                actionWidth: rect(actions).width,
                formWidth: rect(actions.parentElement).width,
                headingSize: parseFloat(getComputedStyle(heading).fontSize),
                kickerSize: parseFloat(getComputedStyle(kicker).fontSize),
            };
        }"""
    )
    if state["tableTop"] >= height * 0.78:
        raise AssertionError(f"operational registry begins too low {width}x{height}: {state}")
    if len(state["dateRows"]) != 2:
        raise AssertionError(f"date range is not a two-field group: {state}")
    if abs(state["dateRows"][0]["top"] - state["dateRows"][1]["top"]) > 4:
        raise AssertionError(f"date fields do not share a desktop row: {state}")
    if state["actionWidth"] < state["formWidth"] * 0.9:
        raise AssertionError(f"filter actions do not own the full grid row: {state}")
    if state["headingSize"] <= state["kickerSize"]:
        raise AssertionError(f"H1 is not the primary visual anchor: {state}")
    return state


def assert_related_geometry(page: Page) -> dict[str, object]:
    links = page.locator(".opdoc-related-link")
    if not links.count():
        raise AssertionError("operational document detail has no related-object demo rows")
    rows = links.evaluate_all(
        """nodes => nodes.map(node => {
            const style = getComputedStyle(node);
            const primary = node.querySelector('.ux-value-primary');
            const technical = node.querySelector('.ux-technical');
            const p = primary?.getBoundingClientRect();
            const t = technical?.getBoundingClientRect();
            return {
                tag: node.tagName,
                href: node.getAttribute('href'),
                paddingTop: parseFloat(style.paddingTop),
                paddingBottom: parseFloat(style.paddingBottom),
                primaryTop: p?.top ?? null,
                primaryBottom: p?.bottom ?? null,
                technicalTop: t?.top ?? null,
                technicalBottom: t?.bottom ?? null,
            };
        })"""
    )
    broken = [
        row
        for row in rows
        if row["tag"] != "A"
        or not row["href"]
        or row["paddingTop"] <= 0
        or row["paddingBottom"] <= 0
        or row["primaryTop"] is None
        or row["technicalTop"] is None
        or row["technicalTop"] < row["primaryBottom"] - 1
    ]
    if broken:
        raise AssertionError(f"related-object semantic geometry violation: {broken}")
    return {"count": len(rows), "rows": rows}


def assert_personnel_geometry(page: Page, width: int) -> dict[str, object]:
    state = page.evaluate(
        """() => {
            const sidebar = document.querySelector('.personnel-directory-sidebar');
            const main = document.querySelector('.personnel-directory-main');
            const current = document.querySelector('.personnel-contour-card[aria-current="page"]');
            const other = document.querySelector('.personnel-contour-card:not([aria-current="page"])');
            const s = sidebar.getBoundingClientRect();
            const m = main.getBoundingClientRect();
            return {
                gap: m.left - s.right,
                sidebarWidth: s.width,
                mainWidth: m.width,
                currentHref: current ? new URL(current.href).pathname : null,
                currentBackground: current ? getComputedStyle(current).backgroundColor : null,
                otherBackground: other ? getComputedStyle(other).backgroundColor : null,
            };
        }"""
    )
    if state["gap"] < 0 or state["gap"] > 64:
        raise AssertionError(f"personnel tree/table gap outside platform range {width}: {state}")
    if width >= 1920 and state["mainWidth"] <= state["sidebarWidth"] * 1.8:
        raise AssertionError(f"employee table does not receive remaining width {width}: {state}")
    if state["currentHref"] != "/organization/":
        raise AssertionError(f"personnel current category is not route-owned: {state}")
    if state["currentBackground"] == state["otherBackground"]:
        raise AssertionError(f"personnel current category is not visually visible: {state}")
    return state


def capture(page: Page, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=OUT / f"{name}.png", full_page=True)


def main() -> None:
    password = os.getenv("EOD_BROWSER_PASSWORD", "").strip()
    if not password:
        raise AssertionError("EOD_BROWSER_PASSWORD must be an ephemeral Development credential")

    report: dict[str, object] = {"base": BASE, "states": {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(BASE + "/accounts/login/")
        need(page, "input[name=username]").fill(os.getenv("EOD_BROWSER_USERNAME", "operator.demo"))
        need(page, "input[name=password]").fill(password)
        need(page, "button[type=submit]").click()
        need(page, "[data-direction-a-shell]")
        detail_path = discover_record_detail(page)

        for mode in THEMES:
            for width, height in DESKTOPS:
                page.set_viewport_size({"width": width, "height": height})

                page.goto(BASE + "/operational-documents/")
                theme(page, mode)
                registry = assert_registry_geometry(page, width, height)
                no_page_overflow(page, f"opdoc registry {mode} {width}")
                capture(page, f"opdoc-registry__{mode}__{width}x{height}")

                page.goto(BASE + detail_path)
                theme(page, mode)
                related = assert_related_geometry(page)
                no_page_overflow(page, f"opdoc detail {mode} {width}")
                capture(page, f"opdoc-detail__{mode}__{width}x{height}")

                page.goto(BASE + "/organization/")
                theme(page, mode)
                personnel = assert_personnel_geometry(page, width)
                no_page_overflow(page, f"personnel {mode} {width}")
                capture(page, f"personnel__{mode}__{width}x{height}")

                report["states"][f"{mode}-{width}x{height}"] = {
                    "registry": registry,
                    "related": related,
                    "personnel": personnel,
                }

            for width, height in MOBILES:
                page.set_viewport_size({"width": width, "height": height})
                for name, path in (
                    ("opdoc-registry", "/operational-documents/"),
                    ("opdoc-detail", detail_path),
                    ("personnel", "/organization/"),
                ):
                    page.goto(BASE + path)
                    theme(page, mode)
                    no_page_overflow(page, f"{name} {mode} {width}")
                    capture(page, f"{name}__{mode}__{width}x{height}")

        browser.close()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "geometry.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
