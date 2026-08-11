#!/usr/bin/env python3
"""Blocking browser evidence for the representative UX Platform surface matrix."""

import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.getenv("EOD_BROWSER_BASE_URL", "http://127.0.0.1:8766").rstrip("/")
OUT = Path(os.getenv("EOD_BROWSER_EVIDENCE", "artifacts/browser-theme"))
VIEWPORTS = ((1440, 900), (1024, 768), (390, 844))
THEMES = ("light", "dark")
PUBLIC_ROUTES = {
    "login": "/accounts/login/",
}
ROUTES = {
    "home": "/",
    "documents": "/documents/",
    "equipment": "/equipment/",
    "dispatching": "/dispatching/",
    "normatives": "/normatives/",
    "imports": "/imports/",
    "workplace_docs": "/workplace-documentation/",
    "operational_documents": "/operational-documents/",
    "defect_registry": "/operations/defects/",
    "defect_registration": "/operations/defects/new/",
    "opj_registry": "/operations/journal/",
    "account_settings": "/accounts/me/",
}
SELECTORS = {
    "login": ".ux-auth-card",
    "home": ".ux-launcher-card",
    "documents": ".document-list-card",
    "equipment": ".equipment-filter-card",
    "dispatching": ".dispatching-object-card",
    "normatives": ".da-card.ux-stack",
    "imports": "section.da-card",
    "workplace_docs": ".da-card.ux-stack",
    "operational_documents": ".opdoc-filter-card",
    "defect_registry": ".defect-da-work-table",
    "defect_registration": ".defect-form-workspace",
    "opj_registry": ".journal-registry-card",
    "registered_opj": ".approved-journal-shell",
    "draft_workspace": ".opj-workspace",
    "account_settings": ".account-setting-card",
}
TOKENS = {
    "login": "--theme-surface",
    "home": "--theme-surface",
    "documents": "--theme-surface",
    "equipment": "--theme-surface",
    "dispatching": "--theme-surface",
    "normatives": "--theme-surface",
    "imports": "--theme-surface",
    "workplace_docs": "--theme-surface",
    "operational_documents": "--theme-surface",
    "defect_registry": "--theme-surface",
    "defect_registration": "--theme-surface",
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


def screenshot(page, shots: Path, name: str) -> None:
    page.screenshot(path=shots / f"{name}.png", full_page=True)


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


def document_width(page):
    return page.evaluate(
        """() => ({
            scroll: document.documentElement.scrollWidth,
            client: document.documentElement.clientWidth,
        })"""
    )


def mask_public_demo_password(page):
    password_node = page.locator("[data-development-demo-password]")
    if password_node.count():
        password_node.evaluate("node => { node.textContent = '••••••••'; }")


def capture_surface(page, shots, report, route, path, mode, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.goto(BASE + path)
    if route == "login":
        mask_public_demo_password(page)
    theme(page, mode)
    node = need(page, SELECTORS[route])
    actual = style(node)
    expected = resolved_background(page, TOKENS[route])
    width_state = document_width(page)
    key = f"{route}__{mode}__{width}x{height}"
    report["baseline"][key] = {
        **actual,
        "expected_background": expected,
        "document_width": width_state,
    }
    screenshot(page, shots, key)
    if width_state["scroll"] > width_state["client"] + 2:
        raise AssertionError(
            f"document overflow {route} {mode} {width}px: {width_state}"
        )
    html_scheme = style(page.locator("html"))["scheme"].split()
    if (
        actual["background"].replace(" ", "")
        != expected.replace(" ", "")
        or mode not in html_scheme
    ):
        raise AssertionError(
            f"theme mismatch {route} {mode}: {actual} {expected} {html_scheme}"
        )


def activate_editor_caret(page):
    editor = need(page, '.draft-rich-editor-host [contenteditable="true"]')
    editor.click()
    prepared = editor.evaluate(
        """editor => {
            const block = editor.querySelector('p, li');
            if (!block) return false;
            const range = document.createRange();
            range.selectNodeContents(block);
            range.collapse(false);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
            editor.focus({preventScroll: true});
            document.dispatchEvent(new Event('selectionchange'));
            return true;
        }"""
    )
    if not prepared:
        raise AssertionError(f"missing editable paragraph at {page.url}")
    page.wait_for_timeout(80)


def discover(page):
    page.goto(BASE + ROUTES["opj_registry"])
    hrefs = page.locator('a[href*="/operations/journal/"]').evaluate_all(
        "ns=>ns.map(n=>new URL(n.href).pathname)"
    )
    ROUTES["registered_opj"] = next(
        h for h in hrefs if re.fullmatch(r"/operations/journal/\d+/", h)
    )
    page.goto(BASE + ROUTES["registered_opj"])
    ROUTES["draft_workspace"] = need(page, 'a[href*="/shift/"]').evaluate(
        "n=>new URL(n.href).pathname"
    )


def main():
    shots = OUT / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    report = {
        "meta": {
            "base_url": BASE,
            "themes": THEMES,
            "viewports": VIEWPORTS,
            "public_routes": PUBLIC_ROUTES,
        },
        "baseline": {},
        "open_states": {},
    }
    password = os.getenv("EOD_BROWSER_PASSWORD", "").strip()
    if not password:
        raise AssertionError("EOD_BROWSER_PASSWORD must be an ephemeral test credential")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        for route, path in PUBLIC_ROUTES.items():
            for mode in THEMES:
                for width, height in VIEWPORTS:
                    capture_surface(
                        page,
                        shots,
                        report,
                        route,
                        path,
                        mode,
                        width,
                        height,
                    )

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE + PUBLIC_ROUTES["login"])
        mask_public_demo_password(page)
        theme(page, "dark")
        username_input = need(page, "input[name=username]")
        username_input.focus()
        font_size = float(
            username_input.evaluate("node => parseFloat(getComputedStyle(node).fontSize)")
        )
        if font_size < 16:
            raise AssertionError(f"mobile login input font too small: {font_size}px")
        login_width = document_width(page)
        if login_width["scroll"] > login_width["client"] + 2:
            raise AssertionError(f"mobile login focus overflow: {login_width}")
        report["open_states"]["login_mobile_focus"] = {
            **style(username_input),
            "font_size": font_size,
            "document_width": login_width,
        }
        screenshot(page, shots, "transient__login_focus__dark__390x844")

        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(BASE + PUBLIC_ROUTES["login"])
        need(page, "input[name=username]").fill(
            os.getenv("EOD_BROWSER_USERNAME", "operator.demo")
        )
        need(page, "input[name=password]").fill(password)
        need(page, "button[type=submit]").click()
        need(page, "[data-direction-a-shell]")
        discover(page)
        report["meta"]["authenticated_routes"] = dict(ROUTES)

        for route, path in ROUTES.items():
            for mode in THEMES:
                for width, height in VIEWPORTS:
                    capture_surface(
                        page,
                        shots,
                        report,
                        route,
                        path,
                        mode,
                        width,
                        height,
                    )

        expected_baselines = (
            len(PUBLIC_ROUTES) + len(ROUTES)
        ) * len(THEMES) * len(VIEWPORTS)
        if len(report["baseline"]) != expected_baselines:
            raise AssertionError(
                f"must contain exactly {expected_baselines} baseline states, "
                f"got {len(report['baseline'])}"
            )
        report["meta"]["baseline_state_count"] = expected_baselines

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE + ROUTES["home"])
        theme(page, "dark")
        toggle = need(page, "[data-direction-a-toggle]")
        toggle.click()
        page.wait_for_function("()=>document.body.classList.contains('da-nav-open')")
        sidebar = need(page, "[data-direction-a-sidebar]")
        if toggle.get_attribute("aria-expanded") != "true":
            raise AssertionError("mobile shell toggle did not publish expanded state")
        report["open_states"]["mobile_navigation"] = style(sidebar)
        screenshot(page, shots, "transient__mobile_navigation__dark__390x844")
        page.keyboard.press("Escape")
        page.wait_for_function("()=>!document.body.classList.contains('da-nav-open')")

        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(BASE + ROUTES["documents"])
        theme(page, "dark")
        create_path = need(page, 'a[href*="/documents/"]').evaluate(
            """node => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                const found = links.find(link => link.textContent.trim() === 'Новый черновик');
                return found ? new URL(found.href).pathname : '';
            }"""
        )
        if not create_path:
            raise AssertionError("missing document create route")
        page.goto(BASE + create_path)
        theme(page, "dark")
        need(page, "[data-equipment-selector-open]").click()
        equipment_dialog = need(page, ".equipment-selector-dialog")
        if not equipment_dialog.evaluate("dialog => dialog.open"):
            raise AssertionError("equipment selector dialog did not open")
        report["open_states"]["document_equipment_dialog"] = style(equipment_dialog)
        screenshot(page, shots, "transient__document_equipment_dialog__dark__1440x900")
        page.keyboard.press("Escape")

        page.goto(BASE + ROUTES["dispatching"])
        theme(page, "dark")
        dispatching_filter = need(page, ".filter-disclosure")
        need(page, ".filter-disclosure > summary").click()
        if not dispatching_filter.evaluate("details => details.open"):
            raise AssertionError("dispatching filter disclosure did not open")
        report["open_states"]["dispatching_filters"] = style(dispatching_filter)
        screenshot(page, shots, "transient__dispatching_filters__dark__1440x900")

        page.goto(BASE + ROUTES["defect_registry"])
        theme(page, "dark")
        need(page, ".defect-filter-drawer > summary").click()
        report["open_states"]["defect_filters"] = style(
            need(page, ".defect-filter-grid")
        )
        screenshot(page, shots, "transient__defect_filters__dark__1440x900")

        page.goto(BASE + ROUTES["defect_registration"])
        theme(page, "dark")
        need(page, ".defect-picker-trigger").click()
        picker = need(page, ".defect-picker-panel")
        report["open_states"]["defect_datetime"] = style(picker)
        screenshot(page, shots, "transient__defect_datetime__dark__1440x900")
        page.keyboard.press("Escape")
        picker.wait_for(state="hidden")

        for kind in ("equipment", "personnel", "workplace"):
            field = need(page, f".defect-tree-selector--{kind} .defect-tree-input")
            field.click()
            report["open_states"][f"defect_{kind}"] = style(
                need(page, f".defect-tree-selector--{kind} .defect-tree-panel")
            )
            screenshot(page, shots, f"transient__defect_{kind}__dark__1440x900")
            field.press("Escape")

        page.goto(BASE + ROUTES["defect_registry"])
        theme(page, "dark")
        defect_rows = page.locator("[data-defect-row-link]")
        report["meta"]["defect_row_present"] = bool(defect_rows.count())
        if defect_rows.count():
            defect_row = defect_rows.first
            defect_row.hover()
            report["open_states"]["defect_hover"] = style(defect_row)
            screenshot(page, shots, "transient__defect_hover__dark__1440x900")

        page.goto(BASE + ROUTES["registered_opj"])
        theme(page, "dark")
        need(page, "[data-open-journal-settings]").click()
        report["open_states"]["opj_settings"] = style(
            need(page, ".journal-settings-dialog")
        )
        screenshot(page, shots, "transient__opj_settings__dark__1440x900")

        page.goto(BASE + ROUTES["draft_workspace"])
        theme(page, "dark")
        need(page, "[data-open-view-drawer]").click()
        report["open_states"]["opj_drawer"] = style(need(page, "[data-view-drawer]"))
        screenshot(page, shots, "transient__opj_drawer__dark__1440x900")
        need(page, "[data-close-view-drawer]").click()
        activate_editor_caret(page)
        need(page, "[data-reference-trigger]:not([disabled])").click()
        report["open_states"]["opj_reference"] = style(
            need(page, "[data-reference-picker]")
        )
        screenshot(page, shots, "transient__opj_reference__dark__1440x900")

        page.goto(BASE + ROUTES["account_settings"])
        theme(page, "dark")
        select = need(page, '.interface-settings-form select[name="theme"]')
        select.focus()
        report["open_states"]["account_theme"] = style(select)
        screenshot(page, shots, "transient__account_focus__dark__1440x900")

        page.goto(BASE + ROUTES["registered_opj"])
        theme(page, "dark")
        page.emulate_media(media="print")
        printed = style(page.locator("html"))
        report["print"] = printed
        if "light" not in printed["scheme"]:
            raise AssertionError("print isolation failed")
        screenshot(page, shots, "registered_opj__print__light__1440x900")

        browser.close()

    (OUT / "computed-styles.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()