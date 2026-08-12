#!/usr/bin/env python3
"""Focused owner-walkthrough visual evidence for UX-PLATFORM Repair v4.

This is intentionally a representative matrix, not the historical route x theme
x viewport combinatorial harness. It verifies the concrete UX-VIS defects and
writes screenshots plus machine-readable rendered-state evidence.
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
BASELINE = runpy.run_path(str(HERE / "run.py"), run_name="eod_browser_helpers")
BASE = os.getenv("EOD_BROWSER_BASE_URL", "http://127.0.0.1:8766").rstrip("/")
OUT = Path(os.getenv("EOD_BROWSER_EVIDENCE", "artifacts/browser-theme"))
SHOTS = OUT / "screenshots"

WIDE = {"width": 2560, "height": 1440}
DESKTOP = {"width": 1440, "height": 900}
TABLET = {"width": 1024, "height": 768}
MOBILE = {"width": 390, "height": 844}

need = BASELINE["need"]
theme = BASELINE["theme"]
document_width = BASELINE["document_width"]
mask_public_demo_password = BASELINE["mask_public_demo_password"]


def screenshot(page: Page, name: str, *, full_page: bool = True) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=SHOTS / f"{name}.png", full_page=full_page)


def metrics(node: Locator) -> dict[str, object]:
    return node.evaluate(
        r"""node => {
            const s = getComputedStyle(node);
            const r = node.getBoundingClientRect();
            return {
                text: (node.innerText || node.textContent || '').replace(/\s+/g, ' ').trim(),
                color: s.color,
                background: s.backgroundColor,
                border: s.borderColor,
                opacity: Number.parseFloat(s.opacity || '1'),
                fontSize: Number.parseFloat(s.fontSize || '0'),
                whiteSpace: s.whiteSpace,
                wordBreak: s.wordBreak,
                overflowWrap: s.overflowWrap,
                textOverflow: s.textOverflow,
                overflowX: s.overflowX,
                scrollWidth: node.scrollWidth,
                clientWidth: node.clientWidth,
                box: {x:r.x, y:r.y, left:r.left, top:r.top, right:r.right,
                      bottom:r.bottom, width:r.width, height:r.height},
            };
        }"""
    )


def visible(page: Page, selector: str) -> Locator | None:
    node = page.locator(f"{selector}:visible").first
    return node if node.count() else None


def check(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def check_width(page: Page, failures: list[str], name: str) -> dict[str, int]:
    state = document_width(page)
    check(
        failures,
        state["scrollWidth"] <= state["innerWidth"] + 2,
        f"document-level horizontal overflow {name}: {state}",
    )
    return state


def contrast(node: Locator) -> dict[str, object]:
    return node.evaluate(
        r"""node => {
            const parse = value => {
                const m = value.match(/rgba?\(([^)]+)\)/i);
                if (!m) return null;
                const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
                return {r:p[0], g:p[1], b:p[2], a:p.length > 3 ? p[3] : 1};
            };
            const c = v => {
                const n = v / 255;
                return n <= .04045 ? n / 12.92 : Math.pow((n + .055) / 1.055, 2.4);
            };
            const lum = rgb => .2126*c(rgb.r) + .7152*c(rgb.g) + .0722*c(rgb.b);
            const fgCss = getComputedStyle(node).color;
            const fg = parse(fgCss);
            let current = node;
            let bgCss = '';
            let bg = null;
            while (current) {
                bgCss = getComputedStyle(current).backgroundColor;
                const candidate = parse(bgCss);
                if (candidate && candidate.a >= .98) { bg = candidate; break; }
                current = current.parentElement;
            }
            if (!bg) {
                bgCss = getComputedStyle(document.documentElement).backgroundColor;
                bg = parse(bgCss) || {r:255,g:255,b:255,a:1};
            }
            const a = lum(fg), b = lum(bg);
            const ratio = (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
            return {foreground:fgCss, background:bgCss, ratio:Math.round(ratio*100)/100};
        }"""
    )


def check_contrast(
    failures: list[str], node: Locator, minimum: float, name: str
) -> dict[str, object]:
    sample = contrast(node)
    check(
        failures,
        float(sample["ratio"]) >= minimum,
        f"contrast below {minimum} for {name}: {sample}",
    )
    return sample


def check_no_ellipsis(
    failures: list[str], node: Locator, name: str
) -> dict[str, object]:
    state = metrics(node)
    clipped = (
        state["scrollWidth"] > state["clientWidth"] + 1
        and state["whiteSpace"] in {"nowrap", "pre"}
        and state["overflowX"] in {"hidden", "clip"}
    )
    check(
        failures,
        state["textOverflow"] != "ellipsis" and not clipped,
        f"critical value silently truncated {name}: {state}",
    )
    return state


def audit_icons(page: Page, failures: list[str], name: str) -> dict[str, object]:
    raw_carets = page.locator("button:visible, summary:visible, [role=button]:visible").evaluate_all(
        r"""nodes => nodes.map(node => ({
            text:(node.textContent||'').replace(/\s+/g,' ').trim(),
            aria:node.getAttribute('aria-label')||''
        })).filter(item => ['^','v','>','<'].includes(item.text))"""
    )
    check(failures, not raw_carets, f"raw caret UI fallback on {name}: {raw_carets}")

    broken = []
    icons = page.locator("button svg:visible, a svg:visible, summary svg:visible")
    for index in range(min(icons.count(), 80)):
        icon = icons.nth(index)
        state = metrics(icon)
        hrefs = icon.locator("use").evaluate_all(
            "nodes => nodes.map(n => n.getAttribute('href') || n.getAttribute('xlink:href') || '')"
        )
        if state["box"]["width"] <= 0 or state["box"]["height"] <= 0 or any(not h for h in hrefs):
            broken.append({"metrics": state, "hrefs": hrefs})
    check(failures, not broken, f"broken owner-visible SVG icons on {name}: {broken}")
    return {"rawCarets": raw_carets, "iconsAudited": min(icons.count(), 80), "broken": broken}


def login(page: Page, password: str) -> None:
    page.goto(BASE + "/accounts/login/")
    need(page, "input[name=username]").fill(os.getenv("EOD_BROWSER_USERNAME", "operator.demo"))
    need(page, "input[name=password]").fill(password)
    need(page, "button[type=submit]").click()
    need(page, "[data-direction-a-shell]")


def first_href(page: Page, route: str, pattern: str) -> str | None:
    page.goto(BASE + route)
    hrefs = page.locator("a[href]").evaluate_all(
        "nodes => nodes.map(n => new URL(n.href).pathname)"
    )
    return next((href for href in hrefs if re.fullmatch(pattern, href)), None)


def discover_routes(page: Page) -> dict[str, str | None]:
    page.goto(BASE + "/operations/journal/")
    opj_hrefs = page.locator('a[href*="/operations/journal/"]').evaluate_all(
        "nodes => nodes.map(n => new URL(n.href).pathname)"
    )
    registered = next(
        (href for href in opj_hrefs if re.fullmatch(r"/operations/journal/\d+/", href)),
        None,
    )
    draft = None
    if registered:
        page.goto(BASE + registered)
        shift = page.locator('a[href*="/shift/"]').first
        if shift.count():
            draft = urlparse(shift.get_attribute("href") or "").path

    page.goto(BASE + "/operations/defects/?status=REGISTERED")
    row = page.locator('[data-defect-row-link][data-status="REGISTERED"]').first
    defect = None
    if row.count():
        defect = urlparse(row.get_attribute("data-detail-url") or "").path or None
    if defect is None:
        defect = first_href(page, "/operations/defects/", r"/operations/defects/[0-9a-f-]{36}/")

    return {
        "registered_opj": registered,
        "draft_opj": draft,
        "defect": defect,
        "workplace": first_href(page, "/workplace-documentation/", r"/workplace-documentation/\d+/"),
        "equipment": first_href(page, "/equipment/", r"/equipment/items/[0-9a-f-]{36}/"),
        "dispatching": first_href(page, "/dispatching/", r"/dispatching/equipment/[0-9a-f-]{36}/"),
    }


def public_states(browser, failures: list[str], report: dict[str, object]) -> None:
    context = browser.new_context(viewport=WIDE)
    page = context.new_page()
    page.goto(BASE + "/")
    theme(page, "light")
    main = need(page, "main.ux-public-home-page")
    state = metrics(main)
    check(
        failures,
        state["box"]["width"] >= 1200,
        f"public home too narrow at 2560px: {state['box']}",
    )
    report["publicHomeWide"] = {
        "main": state,
        "width": check_width(page, failures, "public home wide"),
        "icons": audit_icons(page, failures, "public home"),
    }
    screenshot(page, "public_home__light__2560")

    page.set_viewport_size(DESKTOP)
    page.goto(BASE + "/accounts/login/")
    theme(page, "light")
    credential = visible(page, "[data-development-demo-password]")
    credential_state: dict[str, object] = {"present": bool(credential)}
    if credential:
        css = credential.evaluate(
            """node => {const s=getComputedStyle(node); return {
                fontFamily:s.fontFamily, whiteSpace:s.whiteSpace,
                overflowWrap:s.overflowWrap, wordBreak:s.wordBreak};}"""
        )
        credential_state["style"] = css
        check(
            failures,
            "mono" in css["fontFamily"].lower() or "consolas" in css["fontFamily"].lower(),
            f"Development credential not rendered as technical monospace value: {css}",
        )
        check(
            failures,
            css["whiteSpace"] in {"pre-wrap", "break-spaces"},
            f"Development credential wrapping remains ambiguous: {css}",
        )
    report["developmentCredential"] = credential_state
    mask_public_demo_password(page)
    screenshot(page, "login_development__light__1440")

    page.set_viewport_size(MOBILE)
    page.goto(BASE + "/accounts/login/")
    theme(page, "dark")
    mask_public_demo_password(page)
    report["mobileLogin"] = check_width(page, failures, "mobile login")
    screenshot(page, "login__dark__390")
    context.close()


def import_and_structured(page: Page, failures: list[str], report: dict[str, object]) -> None:
    page.set_viewport_size(WIDE)
    page.goto(BASE + "/imports/")
    theme(page, "light")
    heading = need(page, ".ux-page-header-balanced h1")
    heading_state = metrics(heading)
    check(
        failures,
        heading_state["box"]["width"] >= 320,
        f"Import heading still squeezed on wide desktop: {heading_state['box']}",
    )
    readable = page.locator(".ux-profile-strip .ux-readable-value:visible")
    values = [check_no_ellipsis(failures, readable.nth(i), f"import summary {i}") for i in range(readable.count())]
    report["importsWide"] = {
        "heading": heading_state,
        "values": values,
        "width": check_width(page, failures, "imports wide"),
    }
    screenshot(page, "imports__light__2560")
    theme(page, "dark")
    screenshot(page, "imports__dark__2560")

    page.set_viewport_size(TABLET)
    report["importsTablet"] = check_width(page, failures, "imports tablet")
    screenshot(page, "imports__dark__1024")

    page.set_viewport_size(WIDE)
    page.goto(BASE + "/operational-documents/")
    theme(page, "light")
    cards = page.locator(".document-summary .ux-stat:visible")
    check(failures, cards.count() == 4, f"Structured Journals expected 4 summary cards, got {cards.count()}")
    tops = [round(metrics(cards.nth(i))["box"]["top"], 1) for i in range(cards.count())]
    check(failures, not tops or max(tops)-min(tops) <= 2, f"wide summary grid is not 4 columns: {tops}")
    report["structuredWide"] = {"tops": tops}
    screenshot(page, "structured_journals__light__2560")

    page.set_viewport_size(TABLET)
    cards = page.locator(".document-summary .ux-stat:visible")
    tablet_tops = [round(metrics(cards.nth(i))["box"]["top"], 1) for i in range(cards.count())]
    check(failures, len(set(tablet_tops)) == 2, f"tablet summary grid is not 2x2: {tablet_tops}")
    report["structuredTablet"] = {"tops": tablet_tops}
    screenshot(page, "structured_journals__light__1024")


def organization_and_workplace(
    page: Page,
    routes: dict[str, str | None],
    failures: list[str],
    report: dict[str, object],
) -> None:
    page.set_viewport_size(WIDE)
    page.goto(BASE + "/organization/")
    theme(page, "light")
    selector = need(page, "#personnel-organization")
    selected = selector.locator("option:checked").inner_text().strip()
    selector_state = metrics(selector)
    check(failures, selector_state["box"]["width"] >= 280, f"organization selector too narrow: {selector_state['box']}")
    current_user = need(page, ".da-user")
    full_name = need(page, ".da-user-copy strong").inner_text().strip()
    title = current_user.get_attribute("title") or ""
    check(failures, not full_name or full_name in title, f"full sidebar identity unavailable: {full_name!r} / {title!r}")
    report["organizationWide"] = {
        "selected": selected,
        "selector": selector_state,
        "currentUserTitle": title,
        "width": check_width(page, failures, "organization wide"),
    }
    screenshot(page, "organization__light__2560")

    workplace = routes["workplace"]
    check(failures, bool(workplace), "representative Workplace Documentation detail route missing")
    if not workplace:
        return
    page.set_viewport_size(DESKTOP)
    page.goto(BASE + workplace)
    theme(page, "light")
    stack = visible(page, ".da-table tbody tr .ux-cell-stack")
    check(failures, bool(stack), "Workplace Documentation position row missing")
    if stack:
        primary = stack.locator(".ux-cell-primary").first
        code = stack.locator(".ux-technical-chip").first
        check(failures, primary.count() > 0 and code.count() > 0, "workplace label/code semantic separation missing")
        if primary.count() and code.count():
            a, b = metrics(primary)["box"], metrics(code)["box"]
            check(failures, b["top"] >= a["bottom"]-1, f"workplace label/code collision: {a} / {b}")
    applicability = visible(page, ".da-table tbody tr td:nth-child(3) .ux-cell-stack")
    if applicability:
        primary = applicability.locator(".ux-cell-primary").first
        secondary = applicability.locator(".ux-cell-secondary").first
        if primary.count() and secondary.count():
            a, b = metrics(primary)["box"], metrics(secondary)["box"]
            check(failures, b["top"] >= a["bottom"]-1, f"applicability text collision: {a} / {b}")
    report["workplaceDocs"] = {"width": check_width(page, failures, "workplace desktop")}
    screenshot(page, "workplace_docs__light__1440")
    theme(page, "dark")
    screenshot(page, "workplace_docs__dark__1440")
    page.set_viewport_size(MOBILE)
    report["workplaceMobile"] = check_width(page, failures, "workplace mobile")
    screenshot(page, "workplace_docs__dark__390")


def defect_states(
    page: Page,
    routes: dict[str, str | None],
    failures: list[str],
    report: dict[str, object],
) -> None:
    defect = routes["defect"]
    check(failures, bool(defect), "representative DEFECT detail route missing")
    if not defect:
        return
    page.set_viewport_size(DESKTOP)
    page.goto(BASE + defect)
    theme(page, "light")
    lifecycle = need(page, ".defect-lifecycle")
    current = lifecycle.get_attribute("data-current-status") or ""
    future = []
    for i in range(page.locator(".defect-lifecycle li:visible").count()):
        item = page.locator(".defect-lifecycle li:visible").nth(i)
        step = item.get_attribute("data-step") or ""
        if step == current:
            continue
        state = metrics(item)
        check(failures, state["opacity"] >= .95, f"future DEFECT step faded by opacity: {step} {state['opacity']}")
        sample = {"step": step, "state": state}
        title = item.locator("strong").first
        subtitle = item.locator("small").first
        if title.count():
            sample["titleContrast"] = check_contrast(failures, title, 4.5, f"future DEFECT {step} title")
        if subtitle.count():
            sample["subtitleContrast"] = check_contrast(failures, subtitle, 4.5, f"future DEFECT {step} subtitle")
        future.append(sample)
    report["defectFutureLifecycle"] = {"current": current, "future": future}
    screenshot(page, "defect_lifecycle__light__1440")

    theme(page, "dark")
    links = {}
    for key, selector in {
        "back": ".defect-da-back-link",
        "source": ".defect-da-aside-card summary",
        "history": ".defect-da-detail details > summary",
    }.items():
        node = visible(page, selector)
        if node:
            links[key] = check_contrast(failures, node, 4.5, f"dark DEFECT {key}")
    check(failures, len(links) >= 3, f"dark DEFECT link/disclosure evidence incomplete: {list(links)}")
    report["defectDarkLinks"] = links
    screenshot(page, "defect_links__dark__1440")

    page.goto(BASE + "/operations/defects/?status=REGISTERED")
    theme(page, "light")
    switch = visible(page, '[data-defect-view="journal"]')
    if switch:
        switch.click()
    chip = visible(page, '[data-defect-view-panel="journal"] [data-status="REGISTERED"] .defect-status')
    check(failures, bool(chip), "REGISTERED status chip missing in approved DEFECT journal")
    if chip:
        state = metrics(chip)
        check(
            failures,
            state["whiteSpace"] == "nowrap" and state["wordBreak"] in {"normal", "keep-all"},
            f"REGISTERED chip can break inside word: {state}",
        )
        report["defectRegisteredChip"] = state
    screenshot(page, "defect_journal_registered__light__1440")
    theme(page, "dark")
    screenshot(page, "defect_journal_registered__dark__1440")

    page.goto(BASE + defect)
    theme(page, "light")
    detail_status = need(page, ".defect-da-status")
    status = detail_status.get_attribute("data-status") or ""
    detail_style = {"status": status, "style": metrics(detail_status)}
    page.goto(BASE + "/operational-documents/")
    theme(page, "light")
    opdoc = visible(page, f'[data-domain-status="DEFECT"][data-status="{status}"]')
    check(failures, bool(opdoc), f"same DEFECT state {status} missing from Operational Documents")
    report["defectCrossView"] = {
        "detail": detail_style,
        "operationalDocuments": metrics(opdoc) if opdoc else None,
    }
    screenshot(page, "defect_status_operational_documents__light__1440")


def ensure_marker(page: Page) -> tuple[Locator, Locator, bool]:
    host = page.locator(".draft-ledger-visas:visible").first
    if not host.count():
        raise AssertionError("OPJ browser fixture has no visible pictogram column")
    marker = host.locator("[data-opj-marker]:visible").first
    if marker.count():
        return marker, host, False
    host.evaluate(
        r"""host => {
            const marker=document.createElement('span');
            marker.className='draft-normative-marker opj-normative-marker is-pz_install';
            marker.tabIndex=0;
            marker.dataset.opjMarker=''; marker.dataset.markerKind='pz_install';
            marker.dataset.markerNumber='109'; marker.dataset.markerCount='1';
            marker.dataset.markerLabel='Проверочная нормативная отметка';
            marker.setAttribute('aria-label','Проверочная нормативная отметка, №109');
            marker.innerHTML='<span class="draft-normative-marker-top">ПЗ</span><span class="draft-normative-marker-bolt" aria-hidden="true">ϟ</span><span class="draft-normative-marker-bottom">№109</span><i class="draft-normative-marker-cross" aria-hidden="true"></i>';
            host.append(marker); window.__EOD_OPJ_MARKER_REFRESH_00612__?.();
        }"""
    )
    marker = host.locator("[data-opj-marker]:visible").first
    marker.wait_for(state="visible")
    return marker, host, True


def opj_states(
    page: Page,
    routes: dict[str, str | None],
    failures: list[str],
    report: dict[str, object],
) -> None:
    draft = routes["draft_opj"]
    check(failures, bool(draft), "representative OPJ draft workspace route missing")
    if not draft:
        return
    page.set_viewport_size(WIDE)
    page.goto(BASE + draft)
    theme(page, "dark")
    need(page, "[data-open-view-drawer]").click()
    drawer = need(page, "[data-view-drawer]")
    need(page, '[data-page-width-choice="full"]').click()
    page.wait_for_function("()=>document.querySelector('[data-draft-workspace]')?.dataset.pageWidth==='full'")
    need(page, '[data-view-mode="spread"]').click()
    page.wait_for_function("()=>document.querySelector('[data-draft-workspace]')?.dataset.viewMode==='spread'")

    card = drawer.locator(".opj-drawer-card:visible").first
    summary = card.locator("summary").first
    icon = summary.locator(".opj-drawer-chevron .ui-icon").first
    use = icon.locator("use").first
    href = use.get_attribute("href") if use.count() else ""
    check(failures, bool(href and href.endswith("#icon-chevron-right")), f"OPJ disclosure not canonical SVG: {href}")
    check(failures, bool(card.evaluate("node=>node.open")), "OPJ disclosure expected expanded state missing")
    report["opjDisclosureExpanded"] = {"href": href, "icons": audit_icons(page, failures, "OPJ drawer")}
    screenshot(page, "opj_view_settings_expanded__dark__2560", full_page=False)
    summary.click()
    check(failures, not bool(card.evaluate("node=>node.open")), "OPJ disclosure did not collapse")
    screenshot(page, "opj_view_settings_collapsed__dark__2560", full_page=False)
    summary.hover()
    screenshot(page, "opj_view_settings_hover__dark__2560", full_page=False)
    summary.focus()
    screenshot(page, "opj_view_settings_focus__dark__2560", full_page=False)

    close_control = page.locator("[data-close-view-drawer]").first
    check(failures, close_control.count() > 0, "OPJ drawer close state control missing from DOM")
    if close_control.count():
        close_control.evaluate("node=>node.click()")
        page.wait_for_function("()=>document.querySelector('[data-view-drawer]')?.hidden===true")

    workspace = need(page, "[data-draft-workspace]")
    workspace_state = metrics(workspace)
    check(failures, workspace_state["box"]["width"] >= 1800, f"OPJ full width still compressed at 2560: {workspace_state['box']}")
    report["opjWideSpread"] = {"workspace": workspace_state, "width": check_width(page, failures, "OPJ wide spread")}

    toolbar = {}
    disabled = visible(page, ".draft-row-action:disabled")
    enabled = visible(page, ".draft-row-action:not(:disabled)")
    check(failures, bool(disabled), "OPJ disabled row action fixture missing")
    check(failures, bool(enabled), "OPJ enabled row action fixture missing")
    if disabled:
        state = metrics(disabled)
        check(failures, state["opacity"] >= .95, f"OPJ disabled action hidden by opacity: {state}")
        toolbar["disabled"] = {"state": state, "contrast": check_contrast(failures, disabled, 3.0, "OPJ disabled action")}
    if enabled:
        toolbar["enabled"] = {"state": metrics(enabled), "contrast": check_contrast(failures, enabled, 3.0, "OPJ enabled action")}
    report["opjToolbar"] = toolbar
    screenshot(page, "opj_spread_toolbar__dark__2560")

    marker, host, synthetic = ensure_marker(page)
    marker_state, host_state = metrics(marker), metrics(host)
    check(
        failures,
        marker_state["box"]["left"] >= host_state["box"]["left"]-1
        and marker_state["box"]["right"] <= host_state["box"]["right"]+1,
        f"OPJ pictogram clips outside column: {marker_state['box']} / {host_state['box']}",
    )
    marker.focus()
    popover = need(page, ".opj-marker-popover.is-floating")
    popover_state = metrics(popover)
    check(
        failures,
        popover_state["box"]["left"] >= 8 and popover_state["box"]["right"] <= WIDE["width"]-8
        and popover_state["box"]["top"] >= 8 and popover_state["box"]["bottom"] <= WIDE["height"]-8,
        f"OPJ tooltip escapes viewport: {popover_state['box']}",
    )
    tooltip_text = popover.locator("strong").first
    report["opjTooltip"] = {
        "syntheticFixture": synthetic,
        "marker": marker_state,
        "host": host_state,
        "popover": popover_state,
        "contrast": check_contrast(failures, tooltip_text if tooltip_text.count() else popover, 4.5, "dark OPJ pictogram tooltip"),
    }
    screenshot(page, "opj_pictogram_tooltip__dark__2560", full_page=False)

    theme(page, "light")
    screenshot(page, "opj_spread_toolbar__light__2560")
    page.set_viewport_size(MOBILE)
    page.goto(BASE + draft)
    theme(page, "dark")
    report["opjMobile"] = check_width(page, failures, "OPJ mobile")
    screenshot(page, "opj__dark__390")


def equipment_dispatching(
    page: Page,
    routes: dict[str, str | None],
    failures: list[str],
    report: dict[str, object],
) -> None:
    page.set_viewport_size(DESKTOP)
    if routes["equipment"]:
        page.goto(BASE + routes["equipment"])
        theme(page, "dark")
        relation = visible(page, ".equipment-relation-list a")
        relation_state: dict[str, object] = {"present": bool(relation)}
        if relation:
            relation_state["contrast"] = check_contrast(failures, relation, 4.5, "active equipment relation")
            relation.hover()
        report["equipmentRelations"] = relation_state
        screenshot(page, "equipment_relations__dark__1440")

    if routes["dispatching"]:
        page.goto(BASE + routes["dispatching"])
        theme(page, "dark")
        management = visible(page, ".management-function-card .authority-kind")
        supervision = visible(page, ".supervision-function-card .authority-kind")
        check(failures, bool(management and supervision), "dispatching fixture lacks management + supervision assignments")
        data: dict[str, object] = {}
        if management and supervision:
            m, s = metrics(management), metrics(supervision)
            check(
                failures,
                (m["background"], m["color"], m["border"]) != (s["background"], s["color"], s["border"]),
                f"dispatching management/supervision visually indistinguishable: {m} / {s}",
            )
            data = {"management": m, "supervision": s}
        data["icons"] = audit_icons(page, failures, "dispatching detail")
        report["dispatchingAssignments"] = data
        screenshot(page, "dispatching_assignments__dark__1440")


def account_and_mobile(
    page: Page,
    routes: dict[str, str | None],
    failures: list[str],
    report: dict[str, object],
) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(BASE + "/accounts/me/")
    theme(page, "dark")
    form = need(page, ".interface-settings-form")
    theme_select = form.locator('select[name="theme"]').first
    if theme_select.count():
        current = theme_select.input_value()
        options = theme_select.locator("option").evaluate_all("nodes=>nodes.map(n=>n.value)")
        target = next((value for value in ("light", "dark", "system") if value in options and value != current), current)
        theme_select.select_option(target)
    form.locator('button[type="submit"]').first.click()
    need(page, ".interface-settings-form")
    muted = visible(page, ".interface-settings-card .ux-muted")
    micro = None
    if muted:
        state = metrics(muted)
        check(failures, state["fontSize"] >= 11, f"account supporting text too small: {state}")
        micro = check_contrast(failures, muted, 4.5, "account supporting text")
    report["accountPreferenceSave"] = {
        "url": page.url,
        "microtextContrast": micro,
        "icons": audit_icons(page, failures, "account"),
    }
    screenshot(page, "account_after_preference_save__1440")

    mobile_routes = {
        "home": "/",
        "generic_registry": "/operational-documents/",
        "defect": "/operations/defects/",
        "account": "/accounts/me/",
    }
    if routes["draft_opj"]:
        mobile_routes["opj"] = routes["draft_opj"]
    states = {}
    for name, route in mobile_routes.items():
        page.set_viewport_size(MOBILE)
        page.goto(BASE + route)
        theme(page, "light")
        states[name] = check_width(page, failures, f"mobile {name}")
        screenshot(page, f"mobile_{name}__light__390")
    report["mobileRegression"] = states


def main() -> None:
    password = os.getenv("EOD_BROWSER_PASSWORD", "").strip()
    if not password:
        raise AssertionError("EOD_BROWSER_PASSWORD must be an ephemeral test credential")
    OUT.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    report: dict[str, object] = {
        "meta": {
            "scope": "UX-PLATFORM-FOUNDATION-001 Repair v4 representative evidence",
            "baseUrl": BASE,
            "viewports": {"wide": WIDE, "desktop": DESKTOP, "tablet": TABLET, "mobile": MOBILE},
        }
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        public_states(browser, failures, report)
        page = browser.new_page(viewport=DESKTOP)
        login(page, password)
        routes = discover_routes(page)
        report["meta"]["routes"] = routes

        import_and_structured(page, failures, report)
        organization_and_workplace(page, routes, failures, report)
        defect_states(page, routes, failures, report)
        opj_states(page, routes, failures, report)
        equipment_dispatching(page, routes, failures, report)
        account_and_mobile(page, routes, failures, report)
        browser.close()

    report["meta"]["screenshotCount"] = len(list(SHOTS.glob("*.png")))
    report["failures"] = failures
    report["verdict"] = "PASS" if not failures else "FAIL"
    (OUT / "computed-styles.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Repair v4 focused browser evidence: {report['verdict']}")
    for failure in failures:
        print(f"REPAIR_V4_FAILURE: {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
