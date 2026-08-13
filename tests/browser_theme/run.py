#!/usr/bin/env python3
"""Blocking browser evidence for the representative UX Platform surface matrix."""

import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.getenv("EOD_BROWSER_BASE_URL", "http://127.0.0.1:8766").rstrip("/")
OUT = Path(os.getenv("EOD_BROWSER_EVIDENCE", "artifacts/browser-theme"))
DESKTOP_VIEWPORTS = (
    (1280, 800),
    (1366, 768),
    (1440, 900),
    (1536, 864),
    (1920, 1080),
    (2560, 1440),
)
MOBILE_VIEWPORTS = (
    (390, 844),
    (412, 915),
    (430, 932),
)
VIEWPORTS = DESKTOP_VIEWPORTS + MOBILE_VIEWPORTS
THEMES = ("light", "dark")
PUBLIC_ROUTES = {
    "login": "/accounts/login/",
}
ROUTES = {
    "home": "/",
    "documents": "/documents/",
    "equipment": "/equipment/",
    "personnel": "/organization/",
    "authorities": "/organization/authorities/",
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
    "personnel": ".personnel-directory-sidebar",
    "authorities": ".authority-summary-card",
    "dispatching": ".dispatching-object-card",
    "normatives": ".da-card.ux-stack",
    "imports": "section.da-card",
    "workplace_docs": ".workplace-document-registry",
    "operational_documents": ".opdoc-filter-card",
    "defect_registry": ".defect-da-work-table",
    "defect_registration": ".defect-guided-form",
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
    "personnel": "--theme-surface",
    "authorities": "--theme-surface",
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


def screenshots(page, shots: Path, name: str) -> None:
    page.screenshot(path=shots / f"{name}__screen.png", full_page=False)
    page.screenshot(path=shots / f"{name}__fullpage.png", full_page=True)


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
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: window.innerWidth,
            clientWidth: document.documentElement.clientWidth,
        })"""
    )


def mobile_geometry(page, route, width):
    if width > 520:
        return None
    return page.evaluate(
        """route => {
            const visible = node => {
                const style = getComputedStyle(node);
                const rect = node.getBoundingClientRect();
                return style.display !== "none"
                    && style.visibility !== "hidden"
                    && Number(style.opacity || 1) !== 0
                    && rect.width > 0
                    && rect.height > 0;
            };
            const describe = node => {
                const rect = node.getBoundingClientRect();
                return {
                    tag: node.tagName.toLowerCase(),
                    className: String(node.className || ""),
                    text: (node.innerText || node.textContent || "").trim().slice(0, 120),
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    right: rect.right,
                    bottom: rect.bottom,
                };
            };
            const intersect = (a, b) => {
                const x = Math.min(a.right, b.right) - Math.max(a.left, b.left);
                const y = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
                return x > 2 && y > 2;
            };
            const siblingOverlaps = selector => {
                const collisions = [];
                for (const parent of document.querySelectorAll(selector)) {
                    if (!visible(parent)) continue;
                    const nodes = [...parent.children].filter(visible);
                    for (let i = 0; i < nodes.length; i += 1) {
                        for (let j = i + 1; j < nodes.length; j += 1) {
                            const a = nodes[i].getBoundingClientRect();
                            const b = nodes[j].getBoundingClientRect();
                            if (intersect(a, b)) {
                                collisions.push({
                                    parent: String(parent.className || selector),
                                    first: describe(nodes[i]),
                                    second: describe(nodes[j]),
                                });
                            }
                        }
                    }
                }
                return collisions;
            };

            const touchSelectors = [".da-menu-button"];
            if (route === "authorities") {
                touchSelectors.push(".authority-tabs button", ".authority-tree-heading button");
            }
            if (route === "personnel") {
                touchSelectors.push(".personnel-management-actions .da-button");
            }
            if (route === "draft_workspace") {
                touchSelectors.push(
                    ".opj-toolbar-actions .da-button",
                    ".opj-ribbon-toggle",
                    ".opj-view-switch > button",
                    "button.draft-editor-ribbon-button",
                    ".opj-page-navigation button.da-icon-button",
                    "button.da-icon-button.draft-row-action"
                );
            }
            if (route === "registered_opj") {
                touchSelectors.push(".journal-workspace-actions .da-button");
            }

            const touchNodes = new Set();
            for (const selector of touchSelectors) {
                for (const node of document.querySelectorAll(selector)) {
                    if (visible(node)) touchNodes.add(node);
                }
            }
            const smallTargets = [...touchNodes]
                .map(describe)
                .filter(item => item.width < 42 || item.height < 42);
            const escapedControls = [...touchNodes]
                .map(describe)
                .filter(item => item.x < -2 || item.right > innerWidth + 2);

            const authorityPositionedCells = route === "authorities"
                ? [...document.querySelectorAll(".authority-matrix-person > td")]
                    .filter(visible)
                    .filter(node => ["sticky", "fixed", "absolute"].includes(
                        getComputedStyle(node).position
                    ))
                    .map(describe)
                : [];

            return {
                viewportWidth: innerWidth,
                smallTargets,
                escapedControls,
                publicationOverlaps: route === "authorities"
                    ? siblingOverlaps(".authority-publication-banner")
                    : [],
                personnelManagementOverlaps: route === "personnel"
                    ? siblingOverlaps(".personnel-recent-row")
                    : [],
                authorityPositionedCells,
            };
        }""",
        route,
    )


def rendered_regions(page, surface):
    surface_box = surface.bounding_box()
    heading_state = page.evaluate(
        """() => {
            const main = document.querySelector("main");
            const candidates = [
                ...(main ? main.querySelectorAll("h1, [role='heading'], h2") : []),
                ...document.querySelectorAll("h1, [role='heading'], h2"),
            ];
            const seen = new Set();
            for (const node of candidates) {
                if (seen.has(node)) continue;
                seen.add(node);
                const rect = node.getBoundingClientRect();
                const style = getComputedStyle(node);
                const visible = rect.width > 0 && rect.height > 0
                    && style.display !== "none"
                    && style.visibility !== "hidden";
                if (!visible) continue;
                return {
                    text: (node.innerText || node.textContent || "").trim(),
                    tag: node.tagName.toLowerCase(),
                    box: {
                        x: rect.x, y: rect.y, width: rect.width, height: rect.height,
                    },
                };
            }
            return null;
        }"""
    )
    main = page.locator("main").first
    main_box = main.bounding_box() if main.count() and main.is_visible() else None
    return {
        "heading": heading_state,
        "content_region": surface_box,
        "main_region": main_box,
    }


def bind_runtime_errors(page):
    bucket = {"console_errors": [], "page_errors": []}

    def on_console(message):
        if message.type == "error":
            bucket["console_errors"].append(message.text)

    page.on("console", on_console)
    page.on("pageerror", lambda error: bucket["page_errors"].append(str(error)))
    return bucket


def clear_runtime_errors(bucket):
    bucket["console_errors"].clear()
    bucket["page_errors"].clear()


def runtime_error_snapshot(bucket):
    return {
        "console_errors": list(bucket["console_errors"]),
        "page_errors": list(bucket["page_errors"]),
    }


def assert_no_runtime_errors(bucket, context):
    errors = runtime_error_snapshot(bucket)
    if errors["console_errors"] or errors["page_errors"]:
        raise AssertionError(f"browser runtime errors {context}: {errors}")
    return errors


def visual_viewport_state(page):
    return page.evaluate(
        """() => ({
            scale: window.visualViewport ? window.visualViewport.scale : 1,
            width: window.visualViewport ? window.visualViewport.width : innerWidth,
            height: window.visualViewport ? window.visualViewport.height : innerHeight,
            offsetLeft: window.visualViewport ? window.visualViewport.offsetLeft : 0,
            offsetTop: window.visualViewport ? window.visualViewport.offsetTop : 0,
        })"""
    )


def mask_public_demo_password(page):
    password_node = page.locator("[data-development-demo-password]")
    if password_node.count():
        password_node.evaluate("node => { node.textContent = '••••••••'; }")


def capture_surface(
    page,
    shots,
    report,
    runtime_errors,
    route,
    path,
    mode,
    width,
    height,
):
    page.set_viewport_size({"width": width, "height": height})
    clear_runtime_errors(runtime_errors)
    page.goto(BASE + path)
    if route == "login":
        mask_public_demo_password(page)
    theme(page, mode)
    node = need(page, SELECTORS[route])
    actual = style(node)
    expected = resolved_background(page, TOKENS[route])
    width_state = document_width(page)
    geometry = mobile_geometry(page, route, width)
    regions = rendered_regions(page, node)
    page.wait_for_timeout(50)
    errors = runtime_error_snapshot(runtime_errors)
    key = f"{route}__{mode}__{width}x{height}"
    report["baseline"][key] = {
        **actual,
        "expected_background": expected,
        "document_width": width_state,
        "responsive_geometry": geometry,
        "rendered": regions,
        **errors,
    }
    screenshots(page, shots, key)

    if width_state["scrollWidth"] > width_state["innerWidth"] + 2:
        raise AssertionError(
            f"document overflow {route} {mode} {width}px: {width_state}"
        )
    if geometry:
        broken = {
            name: geometry[name]
            for name in (
                "smallTargets",
                "escapedControls",
                "publicationOverlaps",
                "personnelManagementOverlaps",
                "authorityPositionedCells",
            )
            if geometry[name]
        }
        if broken:
            raise AssertionError(
                f"mobile geometry violation {route} {mode} {width}px: {broken}"
            )
    if not regions["heading"] or not regions["heading"]["text"]:
        raise AssertionError(f"missing rendered heading {route} {mode} {width}px")
    if not regions["content_region"]:
        raise AssertionError(f"missing rendered content region {route} {mode} {width}px")
    assert_no_runtime_errors(runtime_errors, key)

    html_scheme = style(page.locator("html"))["scheme"].split()
    if (
        actual["background"].replace(" ", "") != expected.replace(" ", "")
        or mode not in html_scheme
    ):
        raise AssertionError(
            f"theme mismatch {route} {mode}: {actual} {expected} {html_scheme}"
        )


def capture_mobile_login_focus(browser, shots, report):
    context = browser.new_context(
        viewport={"width": MOBILE_VIEWPORTS[0][0], "height": MOBILE_VIEWPORTS[0][1]},
        is_mobile=True,
        has_touch=True,
    )
    page = context.new_page()
    runtime_errors = bind_runtime_errors(page)

    for mode in THEMES:
        for width, height in MOBILE_VIEWPORTS:
            page.set_viewport_size({"width": width, "height": height})
            clear_runtime_errors(runtime_errors)
            page.goto(BASE + PUBLIC_ROUTES["login"])
            mask_public_demo_password(page)
            theme(page, mode)
            username_input = need(page, "input[name=username]")
            password_input = need(page, "input[name=password]")
            before = visual_viewport_state(page)
            key = f"login_focus__{mode}__{width}x{height}"
            screenshots(page, shots, f"{key}__unfocused")

            username_input.focus()
            page.wait_for_timeout(150)
            username_scale = visual_viewport_state(page)
            username_font_size = float(
                username_input.evaluate(
                    "node => parseFloat(getComputedStyle(node).fontSize)"
                )
            )
            password_input.focus()
            page.wait_for_timeout(150)
            password_scale = visual_viewport_state(page)
            password_font_size = float(
                password_input.evaluate(
                    "node => parseFloat(getComputedStyle(node).fontSize)"
                )
            )
            width_state = document_width(page)
            errors = runtime_error_snapshot(runtime_errors)
            report["mobile_focus"][key] = {
                "before": before,
                "username_focus": username_scale,
                "password_focus": password_scale,
                "username_font_size": username_font_size,
                "password_font_size": password_font_size,
                "document_width": width_state,
                **errors,
            }
            screenshots(page, shots, f"{key}__focused")

            if username_font_size < 16 or password_font_size < 16:
                raise AssertionError(
                    f"mobile login input font too small {width}px: "
                    f"{username_font_size}px/{password_font_size}px"
                )
            for label, state in (
                ("before", before),
                ("username", username_scale),
                ("password", password_scale),
            ):
                if abs(float(state["scale"]) - 1.0) > 0.01:
                    raise AssertionError(
                        f"mobile login visualViewport zoom {label} {mode} "
                        f"{width}px: {state}"
                    )
            if width_state["scrollWidth"] > width_state["innerWidth"] + 2:
                raise AssertionError(
                    f"mobile login focus overflow {mode} {width}px: {width_state}"
                )
            assert_no_runtime_errors(runtime_errors, key)

    context.close()


def activate_editor_reference_selection(page):
    editor = need(page, '.draft-rich-editor-host [contenteditable="true"]')
    editor.click()
    prepared = editor.evaluate(
        r"""editor => {
  const walker = document.createTreeWalker(
      editor,
      NodeFilter.SHOW_TEXT,
      {
acceptNode(node) {
    const parent = node.parentElement;
    const block = parent?.closest?.('p, li');
    if (!block || !editor.contains(block)) {
        return NodeFilter.FILTER_REJECT;
    }
    return (node.textContent || '').trim()
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT;
},
      },
  );
  const textNode = walker.nextNode();
  if (!textNode) return null;
  const text = textNode.textContent || '';
  const start = text.search(/\S/u);
  if (start < 0) return null;
  let end = Math.min(text.length, start + 8);
  while (end > start && /\s/u.test(text[end - 1])) end -= 1;
  if (end <= start) end = Math.min(text.length, start + 1);
  const range = document.createRange();
  range.setStart(textNode, start);
  range.setEnd(textNode, end);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  editor.focus({preventScroll: true});
  document.dispatchEvent(new Event('selectionchange'));
  return {text: range.toString(), collapsed: range.collapsed};
        }"""
    )
    if not prepared or prepared["collapsed"] or not prepared["text"].strip():
        raise AssertionError(f"missing selectable editor text at {page.url}")
    page.wait_for_timeout(80)
    return editor


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
            "desktop_viewports": DESKTOP_VIEWPORTS,
            "mobile_viewports": MOBILE_VIEWPORTS,
            "viewports": VIEWPORTS,
            "public_routes": PUBLIC_ROUTES,
        },
        "baseline": {},
        "mobile_focus": {},
        "open_states": {},
    }
    password = os.getenv("EOD_BROWSER_PASSWORD", "").strip()
    if not password:
        raise AssertionError("EOD_BROWSER_PASSWORD must be an ephemeral test credential")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": DESKTOP_VIEWPORTS[0][0], "height": DESKTOP_VIEWPORTS[0][1]}
        )
        runtime_errors = bind_runtime_errors(page)

        for route, path in PUBLIC_ROUTES.items():
            for mode in THEMES:
                for width, height in VIEWPORTS:
                    capture_surface(
                        page,
                        shots,
                        report,
                        runtime_errors,
                        route,
                        path,
                        mode,
                        width,
                        height,
                    )

        capture_mobile_login_focus(browser, shots, report)

        page.set_viewport_size(
            {"width": DESKTOP_VIEWPORTS[0][0], "height": DESKTOP_VIEWPORTS[0][1]}
        )
        clear_runtime_errors(runtime_errors)
        page.goto(BASE + PUBLIC_ROUTES["login"])
        need(page, "input[name=username]").fill(
            os.getenv("EOD_BROWSER_USERNAME", "operator.demo")
        )
        need(page, "input[name=password]").fill(password)
        need(page, "button[type=submit]").click()
        need(page, "[data-direction-a-shell]")
        assert_no_runtime_errors(runtime_errors, "authenticated login")

        clear_runtime_errors(runtime_errors)
        discover(page)
        assert_no_runtime_errors(runtime_errors, "OPJ route discovery")
        report["meta"]["authenticated_routes"] = dict(ROUTES)

        for route, path in ROUTES.items():
            for mode in THEMES:
                for width, height in VIEWPORTS:
                    capture_surface(
                        page,
                        shots,
                        report,
                        runtime_errors,
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

        clear_runtime_errors(runtime_errors)
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
        screenshots(page, shots, "transient__mobile_navigation__dark__390x844")
        page.keyboard.press("Escape")
        page.wait_for_function("()=>!document.body.classList.contains('da-nav-open')")

        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(BASE + ROUTES["documents"])
        theme(page, "dark")
        create_path = need(page, 'a[href*="/documents/"]').evaluate(
            """node => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                const found = links.find(
                    link => link.textContent.trim() === 'Новый черновик'
                );
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
        screenshots(
            page,
            shots,
            "transient__document_equipment_dialog__dark__1440x900",
        )
        page.keyboard.press("Escape")

        page.goto(BASE + ROUTES["dispatching"])
        theme(page, "dark")
        dispatching_filter = need(page, ".filter-disclosure")
        need(page, ".filter-disclosure > summary").click()
        if not dispatching_filter.evaluate("details => details.open"):
            raise AssertionError("dispatching filter disclosure did not open")
        report["open_states"]["dispatching_filters"] = style(dispatching_filter)
        screenshots(page, shots, "transient__dispatching_filters__dark__1440x900")

        page.goto(BASE + ROUTES["defect_registry"])
        theme(page, "dark")
        need(page, ".defect-filter-drawer > summary").click()
        report["open_states"]["defect_filters"] = style(
            need(page, ".defect-filter-grid")
        )
        screenshots(page, shots, "transient__defect_filters__dark__1440x900")

        page.goto(BASE + ROUTES["defect_registration"])
        theme(page, "dark")
        need(page, ".defect-picker-trigger").click()
        picker = need(page, ".defect-picker-panel")
        report["open_states"]["defect_datetime"] = style(picker)
        screenshots(page, shots, "transient__defect_datetime__dark__1440x900")
        page.keyboard.press("Escape")
        picker.wait_for(state="hidden")

        for kind in ("equipment", "personnel", "workplace"):
            field = need(page, f".defect-tree-selector--{kind} .defect-tree-input")
            field.click()
            report["open_states"][f"defect_{kind}"] = style(
                need(page, f".defect-tree-selector--{kind} .defect-tree-panel")
            )
            screenshots(page, shots, f"transient__defect_{kind}__dark__1440x900")
            field.press("Escape")

        page.goto(BASE + ROUTES["defect_registry"])
        theme(page, "dark")
        defect_rows = page.locator("[data-defect-row-link]")
        report["meta"]["defect_row_present"] = bool(defect_rows.count())
        if defect_rows.count():
            defect_row = defect_rows.first
            defect_row.hover()
            report["open_states"]["defect_hover"] = style(defect_row)
            screenshots(page, shots, "transient__defect_hover__dark__1440x900")

        page.goto(BASE + ROUTES["registered_opj"])
        theme(page, "dark")
        need(page, "[data-open-journal-settings]").click()
        report["open_states"]["opj_settings"] = style(
            need(page, ".journal-settings-dialog")
        )
        screenshots(page, shots, "transient__opj_settings__dark__1440x900")

        page.goto(BASE + ROUTES["draft_workspace"])
        theme(page, "dark")
        need(page, "[data-open-view-drawer]").click()
        report["open_states"]["opj_drawer"] = style(need(page, "[data-view-drawer]"))
        screenshots(page, shots, "transient__opj_drawer__dark__1440x900")
        need(page, "[data-close-view-drawer]").click()
        activate_editor_reference_selection(page)
        reference_trigger = need(
            page,
            "[data-reference-trigger]:not([disabled])",
        )
        page.keyboard.press("Control+Shift+M")
        need(page, "[data-reference-picker]")
        if reference_trigger.get_attribute("aria-expanded") != "true":
            raise AssertionError(
                "OPJ reference picker did not publish expanded state"
            )
        report["open_states"]["opj_reference"] = style(
            need(page, "[data-reference-picker]")
        )
        screenshots(page, shots, "transient__opj_reference__dark__1440x900")

        page.goto(BASE + ROUTES["account_settings"])
        theme(page, "dark")
        select = need(page, '.interface-settings-form select[name="theme"]')
        select.focus()
        report["open_states"]["account_theme"] = style(select)
        screenshots(page, shots, "transient__account_focus__dark__1440x900")
        assert_no_runtime_errors(runtime_errors, "transient states")

        clear_runtime_errors(runtime_errors)
        page.goto(BASE + ROUTES["registered_opj"])
        theme(page, "dark")
        page.emulate_media(media="print")
        printed = style(page.locator("html"))
        report["print"] = {
            **printed,
            **runtime_error_snapshot(runtime_errors),
        }
        if "light" not in printed["scheme"]:
            raise AssertionError("print isolation failed")
        screenshots(page, shots, "registered_opj__print__light__1440x900")
        assert_no_runtime_errors(runtime_errors, "print isolation")

        browser.close()

    (OUT / "computed-styles.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
