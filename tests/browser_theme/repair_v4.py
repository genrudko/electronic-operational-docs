#!/usr/bin/env python3
"""Bounded owner-visible browser evidence for UX-PLATFORM Repair v4.

The older broad browser matrix remains available in run.py. This runner reuses
its stable helpers without executing the combinatorial baseline, then exercises
only representative states tied to UX-VIS-02..23. UX-VIS-01 is verified by the
trusted Development stability contour, not by browser retry masking here.
"""

from __future__ import annotations

import json
import os
import re
import runpy
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Locator, Page, sync_playwright

HERE = Path(__file__).resolve().parent
BASELINE = runpy.run_path(str(HERE / "run.py"), run_name="eod_browser_baseline")

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
assert_no_runtime_errors = BASELINE["assert_no_runtime_errors"]
document_width = BASELINE["document_width"]
discover_opj = BASELINE["discover"]
mask_public_demo_password = BASELINE["mask_public_demo_password"]

WIDE = {"width": 2560, "height": 1440}
DESKTOP = {"width": 1440, "height": 900}
TABLET = {"width": 1024, "height": 768}
MOBILE = {"width": 390, "height": 844}
MIN_SECONDARY_FONT_PX = 11.0


def set_viewport(page: Page, viewport: dict[str, int]) -> None:
    page.set_viewport_size(viewport)


def node_metrics(node: Locator) -> dict[str, object]:
    return node.evaluate(
        r"""node => {
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
                white_space: style.whiteSpace,
                word_break: style.wordBreak,
                overflow_wrap: style.overflowWrap,
                text_overflow: style.textOverflow,
                overflow_x: style.overflowX,
                disabled: Boolean(node.disabled),
                scroll_width: node.scrollWidth,
                client_width: node.clientWidth,
                box: {
                    x: rect.x, y: rect.y, width: rect.width, height: rect.height,
                    left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom,
                },
            };
        }"""
    )


def visible(page: Page, selector: str) -> Locator | None:
    locator = page.locator(f"{selector}:visible").first
    return locator if locator.count() else None


def visible_metrics(page: Page, selector: str) -> dict[str, object] | None:
    locator = visible(page, selector)
    return node_metrics(locator) if locator else None


def check(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def assert_page_width(failures: list[str], page: Page, name: str) -> dict[str, int]:
    state = document_width(page)
    check(
        failures,
        state["scrollWidth"] <= state["innerWidth"] + 2,
        f"document overflow {name}: {state}",
    )
    return state


def contrast(node: Locator) -> dict[str, object]:
    return node.evaluate(
        r"""node => {
            const parse = value => {
                const match = value.match(/rgba?\(([^)]+)\)/i);
                if (!match) return null;
                const values = match[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
                return {r: values[0], g: values[1], b: values[2], a: values.length > 3 ? values[3] : 1};
            };
            const channel = value => {
                const c = value / 255;
                return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
            };
            const luminance = colour => 0.2126 * channel(colour.r)
                + 0.7152 * channel(colour.g)
                + 0.0722 * channel(colour.b);
            const foregroundCss = getComputedStyle(node).color;
            const foreground = parse(foregroundCss);
            let current = node;
            let backgroundCss = '';
            let background = null;
            while (current) {
                backgroundCss = getComputedStyle(current).backgroundColor;
                const candidate = parse(backgroundCss);
                if (candidate && candidate.a >= 0.98) {
                    background = candidate;
                    break;
                }
                current = current.parentElement;
            }
            if (!background) {
                backgroundCss = getComputedStyle(document.documentElement).backgroundColor;
                background = parse(backgroundCss) || {r: 255, g: 255, b: 255, a: 1};
            }
            const l1 = luminance(foreground);
            const l2 = luminance(background);
            const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
            return {foreground: foregroundCss, background: backgroundCss, ratio: Math.round(ratio * 100) / 100};
        }"""
    )


def contrast_check(
    failures: list[str], node: Locator, minimum: float, name: str
) -> dict[str, object]:
    sample = contrast(node)
    check(
        failures,
        float(sample["ratio"]) >= minimum,
        f"contrast {name} below {minimum}: {sample}",
    )
    return sample


def no_silent_ellipsis(
    failures: list[str], node: Locator, name: str
) -> dict[str, object]:
    metrics = node_metrics(node)
    clipped = (
        metrics["scroll_width"] > metrics["client_width"] + 1
        and metrics["white_space"] in {"nowrap", "pre"}
        and metrics["overflow_x"] in {"hidden", "clip"}
    )
    check(
        failures,
        metrics["text_overflow"] != "ellipsis" and not clipped,
        f"critical label silently clipped {name}: {metrics}",
    )
    return metrics


def discover_first(page: Page, route: str, pattern: str) -> str | None:
    page.goto(BASE + route)
    values = page.locator("a[href]").evaluate_all(
        "nodes => nodes.map(node => new URL(node.href).pathname)"
    )
    return next((value for value in values if re.fullmatch(pattern, value)), None)


def login(page: Page, password: str, runtime_errors: dict[str, list[str]]) -> None:
    clear_runtime_errors(runtime_errors)
    page.goto(BASE + "/accounts/login/")
    need(page, "input[name=username]").fill(
        os.getenv("EOD_BROWSER_USERNAME", "operator.demo")
    )
    need(page, "input[name=password]").fill(password)
    need(page, "button[type=submit]").click()
    need(page, "[data-direction-a-shell]")
    assert_no_runtime_errors(runtime_errors, "Repair v4 login")


def ensure_marker(page: Page) -> tuple[Locator, Locator, bool]:
    host = page.locator(".draft-ledger-visas:visible").first
    if not host.count():
        raise AssertionError("Repair v4 marker probe has no visible OPJ visas cell")
    marker = host.locator("[data-opj-marker]:visible").first
    if marker.count():
        return marker, host, False
    host.evaluate(
        r"""host => {
            const marker = document.createElement('span');
            marker.className = 'draft-normative-marker opj-normative-marker is-pz_install';
            marker.tabIndex = 0;
            marker.dataset.opjMarker = '';
            marker.dataset.markerKind = 'pz_install';
            marker.dataset.markerNumber = '109';
            marker.dataset.markerCount = '1';
            marker.dataset.markerLabel = 'Проверочная нормативная отметка';
            marker.setAttribute('aria-label', 'Проверочная нормативная отметка, №109');
            marker.innerHTML = [
                '<span class="draft-normative-marker-top">ПЗ</span>',
                '<span class="draft-normative-marker-bolt" aria-hidden="true">ϟ</span>',
                '<span class="draft-normative-marker-bottom">№109</span>',
                '<i class="draft-normative-marker-cross" aria-hidden="true"></i>',
            ].join('');
            host.append(marker);
            window.__EOD_OPJ_MARKER_REFRESH_00612__?.();
        }"""
    )
    marker = host.locator("[data-opj-marker]:visible").first
    marker.wait_for(state="visible")
    return marker, host, True


def icon_audit(failures: list[str], page: Page, name: str) -> dict[str, object]:
    raw = page.locator("button, summary, [role='button']").evaluate_all(
        r"""nodes => nodes
            .filter(node => {
                const rect = node.getBoundingClientRect();
                const style = getComputedStyle(node);
                return rect.width > 0 && rect.height > 0
                    && style.display !== 'none' && style.visibility !== 'hidden';
            })
            .map(node => ({
                text: (node.textContent || '').replace(/\s+/g, ' ').trim(),
                aria: node.getAttribute('aria-label') || '',
            }))
            .filter(item => ['^', 'v', '>', '<', '+', '-'].includes(item.text))"""
    )
    check(failures, not raw, f"raw UI disclosure/control glyph fallback {name}: {raw}")
    count = 0
    icons = page.locator("button svg:visible, a svg:visible, summary svg:visible")
    for index in range(min(icons.count(), 80)):
        icon = icons.nth(index)
        metrics = node_metrics(icon)
        check(
            failures,
            metrics["box"]["width"] > 0 and metrics["box"]["height"] > 0,
            f"zero-size owner-visible icon {name}: {metrics}",
        )
        hrefs = icon.locator("use").evaluate_all(
            "nodes => nodes.map(node => node.getAttribute('href') || node.getAttribute('xlink:href') || '')"
        )
        check(failures, all(hrefs), f"empty SVG use target {name}: {hrefs}")
        count += 1
    return {"raw_fallbacks": raw, "icons_audited": count}


def public_evidence(browser, failures: list[str], report: dict[str, object]) -> None:
    context = browser.new_context(viewport=WIDE)
    page = context.new_page()
    runtime_errors = bind_runtime_errors(page)
    clear_runtime_errors(runtime_errors)
    page.goto(BASE + "/")
    theme(page, "light")
    main = need(page, "main.ux-public-home-page")
    metrics = node_metrics(main)
    check(
        failures,
        metrics["box"]["width"] >= 1200,
        f"public home remains excessively narrow at 2560: {metrics['box']}",
    )
    report["public_home_wide"] = {
        "main": metrics,
        "document_width": assert_page_width(failures, page, "public home 2560"),
        "icons": icon_audit(failures, page, "public home"),
    }
    screenshots(page, SHOTS, "repair_v4__public_home__light__2560x1440")

    set_viewport(page, DESKTOP)
    page.goto(BASE + "/accounts/login/")
    theme(page, "light")
    credential = visible(page, "[data-development-demo-password]")
    credential_report: dict[str, object] = {"present": bool(credential)}
    if credential:
        style = credential.evaluate(
            """node => { const s=getComputedStyle(node); return {
                fontFamily:s.fontFamily, whiteSpace:s.whiteSpace,
                overflowWrap:s.overflowWrap, wordBreak:s.wordBreak}; }"""
        )
        credential_report["style"] = style
        check(
            failures,
            "mono" in style["fontFamily"].lower() or "consolas" in style["fontFamily"].lower(),
            f"Development credential is not monospace: {style}",
        )
        check(
            failures,
            style["whiteSpace"] in {"pre-wrap", "break-spaces"},
            f"Development credential wrapping remains ambiguous: {style}",
        )
    report["development_credential"] = credential_report
    mask_public_demo_password(page)
    screenshots(page, SHOTS, "repair_v4__login__light__1440x900")

    set_viewport(page, MOBILE)
    page.goto(BASE + "/accounts/login/")
    theme(page, "dark")
    mask_public_demo_password(page)
    report["mobile_login"] = assert_page_width(failures, page, "mobile login")
    screenshots(page, SHOTS, "repair_v4__login__dark__390x844")
    assert_no_runtime_errors(runtime_errors, "public/login evidence")
    context.close()


def import_and_grid_evidence(
    page: Page, failures: list[str], report: dict[str, object]
) -> None:
    set_viewport(page, WIDE)
    page.goto(BASE + ROUTES["imports"])
    theme(page, "light")
    header = need(page, ".ux-page-header-balanced")
    heading = need(page, ".ux-page-header-balanced h1")
    header_metrics = node_metrics(header)
    heading_metrics = node_metrics(heading)
    check(
        failures,
        heading_metrics["box"]["width"] >= 320,
        f"Import desktop heading remains squeezed: {heading_metrics['box']}",
    )
    readable = page.locator(".ux-profile-strip .ux-readable-value:visible")
    values = [
        no_silent_ellipsis(failures, readable.nth(index), f"import summary {index}")
        for index in range(readable.count())
    ]
    report["imports_wide"] = {
        "header": header_metrics,
        "heading": heading_metrics,
        "summary_values": values,
        "document_width": assert_page_width(failures, page, "imports 2560"),
    }
    screenshots(page, SHOTS, "repair_v4__imports__light__2560x1440")

    theme(page, "dark")
    screenshots(page, SHOTS, "repair_v4__imports__dark__2560x1440")
    set_viewport(page, TABLET)
    report["imports_tablet"] = assert_page_width(failures, page, "imports tablet")
    screenshots(page, SHOTS, "repair_v4__imports__dark__1024x768")

    set_viewport(page, WIDE)
    page.goto(BASE + ROUTES["operational_documents"])
    theme(page, "light")
    cards = page.locator(".document-summary .ux-stat:visible")
    check(failures, cards.count() == 4, f"expected four structured summary cards, got {cards.count()}")
    wide_tops = [round(node_metrics(cards.nth(i))["box"]["top"], 1) for i in range(cards.count())]
    if wide_tops:
        check(
            failures,
            max(wide_tops) - min(wide_tops) <= 2,
            f"wide Structured Journals grid is not four columns: {wide_tops}",
        )
    report["structured_wide"] = {"tops": wide_tops}
    screenshots(page, SHOTS, "repair_v4__structured__light__2560x1440")

    set_viewport(page, TABLET)
    cards = page.locator(".document-summary .ux-stat:visible")
    tablet_tops = [round(node_metrics(cards.nth(i))["box"]["top"], 1) for i in range(cards.count())]
    check(
        failures,
        len(set(tablet_tops)) == 2,
        f"tablet Structured Journals grid is not 2x2: {tablet_tops}",
    )
    report["structured_tablet"] = {"tops": tablet_tops}
    screenshots(page, SHOTS, "repair_v4__structured__light__1024x768")


def organization_workplace_evidence(
    page: Page,
    workplace_detail: str | None,
    failures: list[str],
    report: dict[str, object],
) -> None:
    set_viewport(page, WIDE)
    page.goto(BASE + "/organization/")
    theme(page, "light")
    selector = need(page, "#personnel-organization")
    selected = selector.locator("option:checked").inner_text().strip()
    selector_metrics = node_metrics(selector)
    check(
        failures,
        selector_metrics["box"]["width"] >= 280,
        f"organization selector remains too narrow: {selector_metrics['box']}",
    )
    user = need(page, ".da-user")
    user_name = need(page, ".da-user-copy strong").inner_text().strip()
    title = user.get_attribute("title") or ""
    check(
        failures,
        not user_name or user_name in title,
        f"sidebar current-user full identity unavailable: name={user_name!r} title={title!r}",
    )
    report["organization_wide"] = {
        "selected": selected,
        "selector": selector_metrics,
        "current_user_title": title,
        "document_width": assert_page_width(failures, page, "organization 2560"),
    }
    screenshots(page, SHOTS, "repair_v4__organization__light__2560x1440")

    if workplace_detail:
        set_viewport(page, DESKTOP)
        page.goto(BASE + workplace_detail)
        theme(page, "light")
        stack = visible(page, ".da-table tbody tr .ux-cell-stack")
        if stack:
            primary = stack.locator(".ux-cell-primary").first
            code = stack.locator(".ux-technical-chip").first
            check(failures, primary.count() and code.count(), "workplace row lacks explicit primary/code separation")
            if primary.count() and code.count():
                a = node_metrics(primary)["box"]
                b = node_metrics(code)["box"]
                check(
                    failures,
                    b["top"] >= a["bottom"] - 1,
                    f"workplace title/code collision: primary={a} code={b}",
                )
        applicability = visible(page, ".da-table tbody tr td:nth-child(3) .ux-cell-stack")
        if applicability:
            primary = applicability.locator(".ux-cell-primary").first
            secondary = applicability.locator(".ux-cell-secondary").first
            if primary.count() and secondary.count():
                a = node_metrics(primary)["box"]
                b = node_metrics(secondary)["box"]
                check(
                    failures,
                    b["top"] >= a["bottom"] - 1,
                    f"workplace applicability/explanation collision: primary={a} secondary={b}",
                )
        report["workplace_documentation"] = {
            "document_width": assert_page_width(failures, page, "workplace documentation desktop")
        }
        screenshots(page, SHOTS, "repair_v4__workplace_docs__light__1440x900")
        theme(page, "dark")
        screenshots(page, SHOTS, "repair_v4__workplace_docs__dark__1440x900")
        set_viewport(page, MOBILE)
        report["workplace_documentation_mobile"] = assert_page_width(
            failures, page, "workplace documentation mobile"
        )
        screenshots(page, SHOTS, "repair_v4__workplace_docs__dark__390x844")


def defect_evidence(
    page: Page,
    defect_detail: str | None,
    failures: list[str],
    report: dict[str, object],
) -> None:
    if not defect_detail:
        failures.append("representative DEFECT detail route not discovered")
        return

    set_viewport(page, DESKTOP)
    page.goto(BASE + defect_detail)
    theme(page, "light")
    lifecycle = need(page, ".defect-lifecycle")
    current = lifecycle.get_attribute("data-current-status") or ""
    future = []
    items = page.locator(".defect-lifecycle li:visible")
    for index in range(items.count()):
        item = items.nth(index)
        step = item.get_attribute("data-step") or ""
        if step == current:
            continue
        metrics = node_metrics(item)
        title = item.locator("strong").first
        subtitle = item.locator("small").first
        check(
            failures,
            metrics["opacity"] >= 0.95,
            f"future DEFECT lifecycle step faded {step}: {metrics['opacity']}",
        )
        sample = {"step": step, "metrics": metrics}
        if title.count():
            sample["title_contrast"] = contrast_check(
                failures, title, 4.5, f"future DEFECT title {step} light"
            )
        if subtitle.count():
            sample["subtitle_contrast"] = contrast_check(
                failures, subtitle, 4.5, f"future DEFECT subtitle {step} light"
            )
        future.append(sample)
    report["defect_future_lifecycle_light"] = {"current": current, "future": future}
    screenshots(page, SHOTS, "repair_v4__defect_lifecycle__light__1440x900")

    theme(page, "dark")
    link_samples = {}
    for key, selector in {
        "back": ".defect-da-back-link",
        "source": ".defect-da-aside-card summary",
        "history": ".defect-da-detail details > summary",
    }.items():
        node = visible(page, selector)
        if node:
            link_samples[key] = contrast_check(failures, node, 4.5, f"dark DEFECT {key}")
    check(
        failures,
        len(link_samples) >= 3,
        f"dark DEFECT disclosure/link evidence incomplete: {list(link_samples)}",
    )
    report["defect_dark_links"] = link_samples
    screenshots(page, SHOTS, "repair_v4__defect_links__dark__1440x900")

    page.goto(BASE + ROUTES["defect_registry"] + "?status=REGISTERED")
    theme(page, "light")
    journal_switch = visible(page, '[data-defect-view="journal"]')
    if journal_switch:
        journal_switch.click()
    status = visible(page, '[data-defect-view-panel="journal"] [data-status="REGISTERED"] .defect-status')
    if status:
        status_metrics = node_metrics(status)
        check(
            failures,
            status_metrics["white_space"] == "nowrap"
            and status_metrics["word_break"] in {"normal", "keep-all"},
            f"registered DEFECT chip can break inside word: {status_metrics}",
        )
        report["defect_registered_chip"] = status_metrics
    else:
        failures.append("registered status chip not found in approved DEFECT journal fixture")
    screenshots(page, SHOTS, "repair_v4__defect_journal_registered__light__1440x900")

    page.goto(BASE + defect_detail)
    theme(page, "light")
    detail_status = need(page, ".defect-da-status")
    status_code = detail_status.get_attribute("data-status") or ""
    canonical = detail_status.evaluate(
        """node => { const s=getComputedStyle(node); return {
            color:s.color, background:s.backgroundColor,
            registered:getComputedStyle(document.documentElement).getPropertyValue('--da-status-registered').trim(),
            progress:getComputedStyle(document.documentElement).getPropertyValue('--da-status-progress').trim(),
            resolved:getComputedStyle(document.documentElement).getPropertyValue('--da-status-resolved').trim(),
            closed:getComputedStyle(document.documentElement).getPropertyValue('--da-status-closed').trim(),
        }; }"""
    )
    page.goto(BASE + ROUTES["operational_documents"])
    theme(page, "light")
    opdoc = visible(page, f'[data-domain-status="DEFECT"][data-status="{status_code}"]')
    check(
        failures,
        bool(opdoc),
        f"same DEFECT state {status_code} not represented in Operational Documents fixture",
    )
    cross_view = {"status": status_code, "detail": canonical}
    if opdoc:
        cross_view["operational_documents"] = opdoc.evaluate(
            """node => { const s=getComputedStyle(node); return {color:s.color, background:s.backgroundColor}; }"""
        )
    report["defect_cross_view_status"] = cross_view
    screenshots(page, SHOTS, "repair_v4__defect_status_opdocs__light__1440x900")


def opj_evidence(
    page: Page, failures: list[str], report: dict[str, object]
) -> None:
    set_viewport(page, WIDE)
    page.goto(BASE + ROUTES["draft_workspace"])
    theme(page, "dark")
    need(page, "[data-open-view-drawer]").click()
    drawer = need(page, "[data-view-drawer]")
    need(page, '[data-page-width-choice="full"]').click()
    page.wait_for_function(
        "()=>document.querySelector('[data-draft-workspace]')?.dataset.pageWidth==='full'"
    )
    need(page, '[data-view-mode="spread"]').click()
    page.wait_for_function(
        "()=>document.querySelector('[data-draft-workspace]')?.dataset.viewMode==='spread'"
    )

    card = drawer.locator(".opj-drawer-card:visible").first
    summary = card.locator("summary").first
    icon = summary.locator(".opj-drawer-chevron .ui-icon").first
    use = icon.locator("use").first
    check(failures, card.count() and summary.count() and icon.count() and use.count(), "OPJ disclosure SVG structure missing")
    href = use.get_attribute("href") if use.count() else ""
    check(
        failures,
        bool(href and href.endswith("#icon-chevron-right")),
        f"OPJ disclosure does not use canonical chevron SVG: {href}",
    )
    expanded = bool(card.evaluate("node => node.open")) if card.count() else False
    check(failures, expanded, "representative OPJ view-settings disclosure is not expanded initially")
    report["opj_disclosure_expanded"] = {
        "open": expanded,
        "href": href,
        "icons": icon_audit(failures, page, "OPJ expanded drawer"),
    }
    screenshots(page, SHOTS, "repair_v4__opj_drawer_expanded__dark__2560x1440")
    if summary.count():
        summary.click()
        collapsed = not bool(card.evaluate("node => node.open"))
        check(failures, collapsed, "OPJ disclosure did not collapse")
        report["opj_disclosure_collapsed"] = {"open": not collapsed, "href": href}
        screenshots(page, SHOTS, "repair_v4__opj_drawer_collapsed__dark__2560x1440")
        summary.hover()
        screenshots(page, SHOTS, "repair_v4__opj_drawer_hover__dark__2560x1440")
        summary.focus()
        screenshots(page, SHOTS, "repair_v4__opj_drawer_focus__dark__2560x1440")

    need(page, "[data-close-view-drawer]").click()
    workspace = need(page, "[data-draft-workspace]")
    workspace_metrics = node_metrics(workspace)
    check(
        failures,
        workspace_metrics["box"]["width"] >= 1800,
        f"OPJ full width underuses 2560 viewport: {workspace_metrics['box']['width']}px",
    )
    report["opj_wide_spread"] = {
        "workspace": workspace_metrics,
        "document_width": assert_page_width(failures, page, "OPJ full spread 2560"),
    }

    disabled = visible(page, ".draft-row-action:disabled")
    enabled = visible(page, ".draft-row-action:not(:disabled)")
    toolbar = {}
    if disabled:
        metrics = node_metrics(disabled)
        check(failures, metrics["opacity"] >= 0.95, f"OPJ disabled action faded: {metrics}")
        toolbar["disabled"] = {
            "metrics": metrics,
            "contrast": contrast_check(failures, disabled, 3.0, "OPJ disabled action dark"),
        }
    if enabled:
        toolbar["enabled"] = {
            "metrics": node_metrics(enabled),
            "contrast": contrast_check(failures, enabled, 3.0, "OPJ enabled action dark"),
        }
    report["opj_toolbar"] = toolbar
    screenshots(page, SHOTS, "repair_v4__opj_spread_toolbar__dark__2560x1440")

    marker, host, synthetic = ensure_marker(page)
    marker_metrics = node_metrics(marker)
    host_metrics = node_metrics(host)
    check(
        failures,
        marker_metrics["box"]["left"] >= host_metrics["box"]["left"] - 1
        and marker_metrics["box"]["right"] <= host_metrics["box"]["right"] + 1,
        f"OPJ marker clips outside pictogram column: marker={marker_metrics['box']} host={host_metrics['box']}",
    )
    marker.focus()
    popover = need(page, ".opj-marker-popover.is-floating")
    tooltip_metrics = node_metrics(popover)
    check(
        failures,
        tooltip_metrics["box"]["left"] >= 8
        and tooltip_metrics["box"]["right"] <= WIDE["width"] - 8
        and tooltip_metrics["box"]["top"] >= 8
        and tooltip_metrics["box"]["bottom"] <= WIDE["height"] - 8,
        f"OPJ tooltip leaves viewport: {tooltip_metrics['box']}",
    )
    tooltip_text = popover.locator("strong").first
    tooltip_contrast = contrast_check(
        failures,
        tooltip_text if tooltip_text.count() else popover,
        4.5,
        "dark OPJ pictogram tooltip",
    )
    report["opj_marker"] = {
        "synthetic_fixture": synthetic,
        "marker": marker_metrics,
        "host": host_metrics,
        "tooltip": tooltip_metrics,
        "tooltip_contrast": tooltip_contrast,
    }
    screenshots(page, SHOTS, "repair_v4__opj_marker_tooltip__dark__2560x1440")

    theme(page, "light")
    screenshots(page, SHOTS, "repair_v4__opj_spread_toolbar__light__2560x1440")

    set_viewport(page, MOBILE)
    page.goto(BASE + ROUTES["draft_workspace"])
    theme(page, "dark")
    report["opj_mobile"] = assert_page_width(failures, page, "OPJ mobile")
    screenshots(page, SHOTS, "repair_v4__opj__dark__390x844")


def relation_evidence(
    page: Page,
    equipment_detail: str | None,
    dispatching_detail: str | None,
    failures: list[str],
    report: dict[str, object],
) -> None:
    set_viewport(page, DESKTOP)
    if equipment_detail:
        page.goto(BASE + equipment_detail)
        theme(page, "dark")
        relation = visible(page, ".equipment-relation-list a")
        relation_report: dict[str, object] = {"present": bool(relation)}
        if relation:
            relation_report["contrast"] = contrast_check(
                failures, relation, 4.5, "active equipment relation dark"
            )
            relation.hover()
        report["equipment_relations"] = relation_report
        screenshots(page, SHOTS, "repair_v4__equipment_relations__dark__1440x900")

    if dispatching_detail:
        page.goto(BASE + dispatching_detail)
        theme(page, "dark")
        management = visible(page, ".management-function-card .authority-kind")
        supervision = visible(page, ".supervision-function-card .authority-kind")
        check(
            failures,
            bool(management and supervision),
            "dispatching fixture lacks both management and supervision assignments",
        )
        dispatch_report = {}
        if management and supervision:
            m = node_metrics(management)
            s = node_metrics(supervision)
            check(
                failures,
                (m["background"], m["color"], m["border"])
                != (s["background"], s["color"], s["border"]),
                f"management/supervision assignments remain visually indistinguishable: {m} {s}",
            )
            dispatch_report = {"management": m, "supervision": s}
        dispatch_report["icons"] = icon_audit(failures, page, "dispatching detail")
        report["dispatching_assignments"] = dispatch_report
        screenshots(page, SHOTS, "repair_v4__dispatching_assignments__dark__1440x900")


def account_mobile_evidence(
    page: Page, failures: list[str], report: dict[str, object]
) -> None:
    set_viewport(page, DESKTOP)
    page.goto(BASE + ROUTES["account_settings"])
    theme(page, "dark")
    form = need(page, ".interface-settings-form")
    form.locator('button[type="submit"]').click()
    need(page, ".interface-settings-form")
    muted = visible(page, ".interface-settings-card .ux-muted")
    micro = None
    if muted:
        metrics = node_metrics(muted)
        check(
            failures,
            metrics["font_size"] >= MIN_SECONDARY_FONT_PX,
            f"account supporting text too small: {metrics['font_size']}px",
        )
        micro = contrast_check(failures, muted, 4.5, "account supporting text dark")
    report["account_preference_save"] = {
        "url": page.url,
        "microtext_contrast": micro,
        "icons": icon_audit(failures, page, "account"),
    }
    screenshots(page, SHOTS, "repair_v4__account_after_save__dark__1440x900")

    mobile_routes = {
        "home": ROUTES["home"],
        "generic_registry": ROUTES["operational_documents"],
        "defect": ROUTES["defect_registry"],
        "account": ROUTES["account_settings"],
        "opj": ROUTES["draft_workspace"],
    }
    states = {}
    for name, path in mobile_routes.items():
        set_viewport(page, MOBILE)
        page.goto(BASE + path)
        theme(page, "light")
        states[name] = assert_page_width(failures, page, f"mobile {name}")
        screenshots(page, SHOTS, f"repair_v4__mobile_{name}__light__390x844")
    report["mobile_regression"] = states


def main() -> None:
    password = os.getenv("EOD_BROWSER_PASSWORD", "").strip()
    if not password:
        raise AssertionError("EOD_BROWSER_PASSWORD must be an ephemeral test credential")

    OUT.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "meta": {
            "base_url": BASE,
            "scope": "UX-PLATFORM-FOUNDATION-001 Repair v4 bounded owner-walkthrough matrix",
            "wide": WIDE,
            "desktop": DESKTOP,
            "tablet": TABLET,
            "mobile": MOBILE,
        }
    }
    failures: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        public_evidence(browser, failures, report)

        page = browser.new_page(viewport=DESKTOP)
        runtime_errors = bind_runtime_errors(page)
        login(page, password, runtime_errors)
        discover_opj(page)
        assert_no_runtime_errors(runtime_errors, "OPJ route discovery")

        equipment_detail = discover_first(
            page, ROUTES["equipment"], r"/equipment/items/[0-9a-f-]{36}/"
        )
        dispatching_detail = discover_first(
            page, ROUTES["dispatching"], r"/dispatching/equipment/[0-9a-f-]{36}/"
        )
        defect_detail = discover_first(
            page, ROUTES["defect_registry"], r"/operations/defects/[0-9a-f-]{36}/"
        )
        workplace_detail = discover_first(
            page, ROUTES["workplace_docs"], r"/workplace-documentation/\d+/"
        )
        report["meta"]["routes"] = {
            "registered_opj": ROUTES["registered_opj"],
            "draft_workspace": ROUTES["draft_workspace"],
            "equipment_detail": equipment_detail,
            "dispatching_detail": dispatching_detail,
            "defect_detail": defect_detail,
            "workplace_detail": workplace_detail,
        }

        import_and_grid_evidence(page, failures, report)
        organization_workplace_evidence(page, workplace_detail, failures, report)
        defect_evidence(page, defect_detail, failures, report)
        opj_evidence(page, failures, report)
        relation_evidence(
            page, equipment_detail, dispatching_detail, failures, report
        )
        account_mobile_evidence(page, failures, report)

        report["runtime_errors"] = runtime_error_snapshot(runtime_errors)
        check(
            failures,
            not report["runtime_errors"]["console_errors"]
            and not report["runtime_errors"]["page_errors"],
            f"browser runtime errors during Repair v4: {report['runtime_errors']}",
        )
        browser.close()

    report["meta"]["screenshot_files"] = len(list(SHOTS.glob("*.png")))
    report["failures"] = failures
    report["verdict"] = "PASS" if not failures else "FAIL"
    report_path = OUT / "computed-styles.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Repair v4 focused browser evidence: {report['verdict']}")
    for failure in failures:
        print(f"REPAIR_V4_FAILURE: {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
