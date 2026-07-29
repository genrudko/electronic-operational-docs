(() => {
    "use strict";

    const path = window.location.pathname;
    if (!path.startsWith("/operations/journal/")) {
        return;
    }

    const main = document.querySelector("main");
    if (!main) {
        return;
    }

    function element(tag, className = "", text = "") {
        const node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text) {
            node.textContent = text;
        }
        return node;
    }

    function detailUrl() {
        if (path.includes("/shift/")) {
            return path.replace("/shift/", "/");
        }
        return /^\/operations\/journal\/\d+\/$/.test(path) ? path : null;
    }

    function addWorkBoundary() {
        const workspace = main.querySelector("[data-draft-workspace]");
        if (!workspace || main.querySelector("[data-opj-work-boundary]")) {
            return;
        }
        const boundary = element("section", "opj-work-boundary da-alert");
        boundary.dataset.opjWorkBoundary = "";
        const copy = element("div");
        copy.append(
            element("strong", "", "Рабочий черновик"),
            element("p", "", "Записи текущей смены сохраняются автоматически"),
        );
        boundary.append(copy, element("span", "opj-boundary-chip da-status is-success", "Автосохранение"));
        workspace.before(boundary);
    }

    function renameRegisteredAction() {
        const link = main.querySelector(".draft-clean-copy-action");
        if (!link) {
            return;
        }
        link.textContent = "Зарегистрированный журнал";
        link.title = "Открыть зарегистрированные записи по утверждённой форме";
        link.setAttribute("aria-label", link.title);
        link.classList.add("da-button", "is-secondary", "is-compact");
    }

    function sanitizeRegisteredTable(table) {
        const clone = table.cloneNode(true);
        clone.querySelectorAll("[id]").forEach((node) => node.removeAttribute("id"));
        clone.querySelectorAll("form, button").forEach((node) => node.remove());
        clone.classList.add("da-table");
        return clone;
    }

    async function addRegisteredContext() {
        const workspace = main.querySelector("[data-draft-workspace]");
        const url = detailUrl();
        if (!workspace || !url || main.querySelector("[data-opj-registered-context]")) {
            return;
        }

        const context = element("details", "opj-registered-context da-panel-flat is-loading");
        context.dataset.opjRegisteredContext = "";
        context.open = false;
        const summary = element("summary");
        const heading = element("span", "opj-registered-context-heading");
        heading.append(
            element("span", "da-chip", "Только чтение"),
            element("strong", "", "Зарегистрированные записи"),
        );
        const meta = element("span", "opj-registered-context-meta", "Загрузка…");
        summary.append(heading, meta);
        const body = element(
            "div",
            "opj-registered-context-body",
            "Загрузка зарегистрированного журнала…",
        );
        context.append(summary, body);
        const boundary = main.querySelector("[data-opj-work-boundary]");
        (boundary || workspace).before(context);

        try {
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: {"X-Requested-With": "XMLHttpRequest"},
            });
            if (!response.ok) {
                throw new Error(`registered_context_${response.status}`);
            }
            const parsed = new DOMParser().parseFromString(
                await response.text(),
                "text/html",
            );
            const sourceTable = parsed.querySelector(".approved-journal-table");
            if (!sourceTable) {
                throw new Error("registered_table_missing");
            }
            const table = sanitizeRegisteredTable(sourceTable);
            const count = table.querySelectorAll("tbody tr").length;
            const note = element("div", "opj-registered-context-note");
            note.append(
                element("span", "", "Хронологический read-only контекст зарегистрированного журнала"),
            );
            const fullLink = element("a", "da-button is-secondary is-compact", "Открыть форму");
            fullLink.href = url;
            note.append(fullLink);
            const wrap = element("div", "opj-registered-table-wrap da-table-wrap");
            wrap.append(table);
            body.replaceChildren(note, wrap);
            meta.textContent = `${count} ${count === 1 ? "запись" : "записей"}`;
            context.classList.remove("is-loading");
        } catch (_error) {
            const fallback = element("div", "opj-registered-context-note");
            fallback.append(element("span", "", "Не удалось встроить зарегистрированные записи"));
            const link = element("a", "da-button is-secondary is-compact", "Открыть журнал");
            link.href = url;
            fallback.append(link);
            body.replaceChildren(fallback);
            meta.textContent = "Открыть отдельно";
            context.classList.remove("is-loading");
        }
    }

    function parseCatalog() {
        const node = document.getElementById("draft-semantic-reference-catalog");
        if (!node) {
            return {};
        }
        try {
            return JSON.parse(node.textContent || "{}");
        } catch (_error) {
            return {};
        }
    }

    function equipmentIdentity(item) {
        const values = String(item.meta || "")
            .split("·")
            .map((value) => value.trim())
            .filter(Boolean);
        return {
            site: values[0] || "Без энергообъекта",
            type: values[1] || "Оборудование",
        };
    }

    function matchEquipment(node, items) {
        const reference = (
            node.dataset.reference
            || node.dataset.referenceValue
            || node.getAttribute("data-reference")
            || ""
        );
        const exact = reference
            ? items.find((item) => item.reference === reference)
            : null;
        if (exact) {
            return exact;
        }
        const nodeText = (node.textContent || "").trim();
        return [...items]
            .sort((left, right) => String(right.label || "").length - String(left.label || "").length)
            .find((item) => nodeText.includes(String(item.label || ""))) || null;
    }

    function enhanceEquipmentHierarchy() {
        const picker = document.querySelector("[data-reference-picker]");
        const results = picker?.querySelector("[data-reference-results]");
        const equipmentTab = picker?.querySelector('[data-reference-kind-option="equipment"]');
        if (!picker || !results || !equipmentTab) {
            return;
        }

        let catalog = parseCatalog();
        let grouping = false;
        let observer = null;

        const regroup = () => {
            if (grouping || equipmentTab.getAttribute("aria-pressed") !== "true") {
                return;
            }
            const sourceItems = Array.isArray(catalog.equipment) ? catalog.equipment : [];
            const candidates = Array.from(results.children).filter(
                (node) => !node.classList.contains("opj-reference-tree"),
            );
            if (!sourceItems.length || !candidates.length) {
                return;
            }
            const mapped = candidates
                .map((node) => ({node, item: matchEquipment(node, sourceItems)}))
                .filter((row) => row.item);
            if (!mapped.length || mapped.length !== candidates.length) {
                return;
            }

            grouping = true;
            observer?.disconnect();
            const tree = element("div", "opj-reference-tree da-hierarchy");
            tree.dataset.opjEquipmentHierarchy = "";
            const sites = new Map();
            mapped.forEach(({node, item}) => {
                const identity = equipmentIdentity(item);
                if (!sites.has(identity.site)) {
                    sites.set(identity.site, new Map());
                }
                const types = sites.get(identity.site);
                if (!types.has(identity.type)) {
                    types.set(identity.type, []);
                }
                types.get(identity.type).push(node);
            });
            sites.forEach((types, site) => {
                const siteGroup = element(
                    "details",
                    "opj-reference-tree-site da-hierarchy-group",
                );
                siteGroup.open = true;
                siteGroup.append(element("summary", "", site));
                types.forEach((nodes, type) => {
                    const typeGroup = element("div", "opj-reference-tree-type");
                    typeGroup.append(element("strong", "", type), ...nodes);
                    siteGroup.append(typeGroup);
                });
                tree.append(siteGroup);
            });
            results.replaceChildren(tree);
            results.dataset.opjHierarchy = "equipment";
            observer?.observe(results, {childList: true});
            grouping = false;
        };

        observer = new MutationObserver(() => window.requestAnimationFrame(regroup));
        observer.observe(results, {childList: true});
        picker.addEventListener("click", () => window.requestAnimationFrame(regroup));
        picker.querySelector("[data-reference-search]")?.addEventListener(
            "input",
            () => window.requestAnimationFrame(regroup),
        );
        document.querySelector("[data-draft-workspace]")?.addEventListener(
            "eod:reference-catalog-updated",
            (event) => {
                catalog = event.detail?.catalog || parseCatalog();
            },
        );
        window.requestAnimationFrame(regroup);
    }

    function applySharedPrimitiveClasses() {
        main.querySelectorAll(".page-heading, .journal-workspace-bar, .shift-book-header").forEach(
            (node) => node.classList.add("da-page-header"),
        );
        main.querySelector(".shift-book-header")?.classList.add("da-page-header-compact");
        main.querySelectorAll(".journal-workspace-actions").forEach(
            (node) => node.classList.add("da-actions"),
        );
        main.querySelectorAll(".journal-workspace-actions .button, .draft-command-actions .button").forEach(
            (node) => node.classList.add("da-button"),
        );
        main.querySelectorAll(".button.secondary").forEach(
            (node) => node.classList.add("is-secondary"),
        );
        main.querySelectorAll(".profile-card, .paged-draft-workspace").forEach(
            (node) => node.classList.add("da-panel"),
        );
        main.querySelectorAll(".draft-view-switch").forEach(
            (node) => node.classList.add("da-segmented"),
        );
        main.querySelectorAll(".draft-command-search input, .draft-command-search select").forEach(
            (node) => node.classList.add("da-field"),
        );
        main.querySelectorAll("dialog").forEach((node) => node.classList.add("da-overlay"));
        main.querySelectorAll(".approved-journal-table, .journal-registry-table").forEach(
            (node) => node.classList.add("da-table"),
        );
        main.querySelectorAll(".table-wrap, .approved-journal-table-wrap").forEach(
            (node) => node.classList.add("da-table-wrap"),
        );
    }

    applySharedPrimitiveClasses();
    renameRegisteredAction();
    addWorkBoundary();
    void addRegisteredContext();
    enhanceEquipmentHierarchy();
})();
