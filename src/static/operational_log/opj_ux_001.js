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

    function sanitizeRegisteredTable(table) {
        const clone = table.cloneNode(true);
        clone.querySelectorAll("[id]").forEach((node) => node.removeAttribute("id"));
        clone.querySelectorAll("form, button, dialog, .screen-only").forEach(
            (node) => node.remove(),
        );
        clone.classList.add("da-table");
        return clone;
    }

    function ensureRegisteredContext() {
        const workspace = main.querySelector("[data-draft-workspace]");
        if (!workspace) {
            return null;
        }
        let context = main.querySelector("[data-opj-registered-context]");
        if (context) {
            return context;
        }
        context = element("details", "opj-registered-context da-panel-flat");
        context.dataset.opjRegisteredContext = "";
        const summary = element("summary");
        const heading = element("span", "opj-registered-context-heading");
        heading.append(
            element("span", "da-chip", "Только чтение"),
            element("strong", "", "Зарегистрированные записи"),
        );
        summary.append(
            heading,
            element("span", "opj-registered-context-meta", "Загрузка…"),
        );
        context.append(
            summary,
            element(
                "div",
                "opj-registered-context-body",
                "Загрузка зарегистрированного журнала…",
            ),
        );
        workspace.before(context);
        return context;
    }

    async function loadRegisteredContext() {
        const url = detailUrl();
        const context = ensureRegisteredContext();
        if (!url || !context || context.dataset.opjRegisteredLoaded === "true") {
            return;
        }
        context.dataset.opjRegisteredLoaded = "true";
        context.classList.add("is-loading");
        context.open = false;

        const body = context.querySelector(".opj-registered-context-body");
        const meta = context.querySelector(".opj-registered-context-meta");
        if (!body || !meta) {
            return;
        }

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
                element(
                    "span",
                    "",
                    "Хронологический контекст зарегистрированного журнала",
                ),
            );
            const fullLink = element(
                "a",
                "da-button is-secondary is-compact",
                "Открыть утверждённую форму",
            );
            fullLink.href = url;
            note.append(fullLink);
            const wrap = element("div", "opj-registered-table-wrap da-table-wrap");
            wrap.append(table);
            body.replaceChildren(note, wrap);
            meta.textContent = `${count} ${count === 1 ? "запись" : "записей"}`;
        } catch (_error) {
            const fallback = element("div", "opj-registered-context-note");
            fallback.append(
                element("span", "", "Не удалось загрузить зарегистрированные записи"),
            );
            const link = element(
                "a",
                "da-button is-secondary is-compact",
                "Открыть журнал",
            );
            link.href = url;
            fallback.append(link);
            body.replaceChildren(fallback);
            meta.textContent = "Открыть отдельно";
        } finally {
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
            .sort(
                (left, right) => String(right.label || "").length
                    - String(left.label || "").length,
            )
            .find((item) => nodeText.includes(String(item.label || ""))) || null;
    }

    function enhanceEquipmentHierarchy() {
        const picker = document.querySelector("[data-reference-picker]");
        const results = picker?.querySelector("[data-reference-results]");
        const equipmentTab = picker?.querySelector(
            '[data-reference-kind-option="equipment"]',
        );
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
            const sourceItems = Array.isArray(catalog.equipment)
                ? catalog.equipment
                : [];
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

    function adoptSharedPrimitives() {
        main.querySelectorAll(".journal-workspace-actions").forEach(
            (node) => node.classList.add("da-actions"),
        );
        main.querySelectorAll(".button.secondary").forEach(
            (node) => node.classList.add("da-button", "is-secondary"),
        );
        main.querySelectorAll(".approved-journal-table, .journal-registry-table").forEach(
            (node) => node.classList.add("da-table"),
        );
        main.querySelectorAll(".table-wrap, .approved-journal-table-wrap").forEach(
            (node) => node.classList.add("da-table-wrap"),
        );
        main.querySelectorAll("dialog").forEach(
            (node) => node.classList.add("da-overlay"),
        );
    }

    adoptSharedPrimitives();
    void loadRegisteredContext();
    enhanceEquipmentHierarchy();
})();
