(() => {
    "use strict";

    const path = window.location.pathname;
    if (!path.startsWith("/operations/journal/")) {
        return;
    }

    const main = document.querySelector("main");
    const originalTopbar = document.querySelector("body > .topbar");
    if (!main || document.querySelector("[data-opj-direction-a-shell]")) {
        return;
    }

    const iconsUrl = "/static/system/icons.svg";
    const userName = (
        originalTopbar?.querySelector(".user-menu-label")?.textContent
        || "Пользователь"
    ).trim();
    const userRole = (
        originalTopbar?.querySelector(".user-menu-identity span")?.textContent
        || "Оперативный персонал"
    ).trim();
    const userInitial = (
        originalTopbar?.querySelector(".user-avatar")?.textContent
        || userName.slice(0, 1)
        || "П"
    ).trim();

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

    function icon(name) {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.classList.add("ui-icon");
        svg.setAttribute("aria-hidden", "true");
        const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
        use.setAttribute("href", `${iconsUrl}#icon-${name}`);
        svg.append(use);
        return svg;
    }

    function hrefFor(label, fallback) {
        const link = Array.from(originalTopbar?.querySelectorAll("a") || []).find(
            (candidate) => candidate.textContent.trim() === label,
        );
        return link?.href || fallback;
    }

    function navLink(label, fallback, iconName, active = false, child = false) {
        const link = element("a", child ? "eod-da-nav-child" : "");
        link.href = hrefFor(label, fallback);
        if (active) {
            link.classList.add("is-active");
            link.setAttribute("aria-current", "page");
        }
        if (!child) {
            link.append(icon(iconName));
        }
        link.append(element("span", "", label));
        return link;
    }

    function navGroup(title, iconName, links) {
        const group = element("section", "eod-da-nav-group");
        const heading = element("div", "eod-da-nav-group-title");
        heading.append(icon(iconName), element("span", "", title));
        group.append(heading, ...links);
        return group;
    }

    function currentTitle() {
        return (
            main.querySelector("h1")?.textContent
            || document.title.split("·")[0]
            || "Оперативный журнал"
        ).trim();
    }

    function currentContext() {
        return (
            main.querySelector(".shift-book-meta-period")?.textContent
            || main.querySelector(".journal-workplace")?.textContent
            || "Рабочий контур оперативного журнала"
        ).trim();
    }

    function detailUrl() {
        if (path.includes("/shift/")) {
            return path.replace("/shift/", "/");
        }
        return /^\/operations\/journal\/\d+\/$/.test(path) ? path : null;
    }

    function workspaceUrl() {
        const match = path.match(/^\/operations\/journal\/(\d+)\/(?:shift\/)?$/);
        return match ? `/operations/journal/${match[1]}/shift/` : null;
    }

    function buildSidebar() {
        const sidebar = element("aside", "eod-da-sidebar");
        sidebar.id = "eod-direction-a-sidebar";
        sidebar.dataset.opjDirectionASidebar = "";

        const brand = element("a", "eod-da-brand");
        brand.href = hrefFor("Главная", "/");
        brand.append(element("span", "eod-da-brand-mark", "ЭОД"));
        const brandCopy = element("span", "eod-da-brand-copy");
        brandCopy.append(
            element("strong", "", "ЭОД"),
            element("small", "", "Оперативная документация"),
        );
        brand.append(brandCopy);

        const context = element("section", "eod-da-context");
        context.setAttribute("aria-label", "Рабочий контекст");
        context.append(
            element("span", "", path.includes("/shift/") ? "Рабочая смена" : "Оперативный журнал"),
            element("strong", "", currentTitle()),
            element("small", "", currentContext()),
        );

        const navigation = element("nav", "eod-da-navigation");
        navigation.setAttribute("aria-label", "Навигация ЭОД");
        navigation.append(
            navLink("Главная", "/", "home"),
            navGroup("Оперативная документация", "document", [
                navLink("Оперативный журнал", "/operations/journal/", "document", true, true),
            ]),
            navGroup("Журналы", "journal", [
                navLink("Журнал дефектов", "/operations/defects/", "journal", false, true),
                navLink("Оперативные документы", "/operational-documents/", "journal", false, true),
            ]),
            navLink("Документы", "/documents/", "document"),
            navLink("Оборудование", "/equipment/", "equipment"),
            navLink("Управление и ведение", "/dispatching/", "management"),
            navGroup("Справочники и данные", "directory", [
                navLink("Организация и персонал", "/organization/", "directory", false, true),
                navLink("Перечни документации", "/workplace-documentation/", "directory", false, true),
                navLink("Импорт данных", "/imports/", "directory", false, true),
            ]),
        );

        const user = element("a", "eod-da-user");
        user.href = hrefFor("Учётная запись и интерфейс", "/accounts/me/");
        user.append(element("span", "eod-da-user-avatar", userInitial));
        const userCopy = element("span", "eod-da-user-copy");
        userCopy.append(
            element("strong", "", userName),
            element("small", "", userRole),
        );
        user.append(userCopy, icon("settings"));

        sidebar.append(brand, context, navigation, user);
        return sidebar;
    }

    function buildTopbar() {
        const topbar = element("header", "eod-da-topbar");
        const mainArea = element("div", "eod-da-topbar-main");
        const menuButton = element("button", "eod-da-menu-button");
        menuButton.type = "button";
        menuButton.dataset.opjMenuToggle = "";
        menuButton.setAttribute("aria-label", "Открыть навигацию");
        menuButton.setAttribute("aria-controls", "eod-direction-a-sidebar");
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.append(icon("menu"));

        const copy = element("div", "eod-da-topbar-copy");
        copy.append(
            element("span", "", path.includes("/shift/") ? "Рабочая область смены" : "Оперативная документация"),
            element("strong", "", currentTitle()),
        );
        mainArea.append(menuButton, copy);

        const actions = element("div", "eod-da-topbar-actions");
        const registered = detailUrl();
        const workspace = workspaceUrl();
        if (path.includes("/shift/") && registered) {
            const link = element("a", "", "Зарегистрированный журнал");
            link.href = registered;
            actions.append(link);
        } else if (workspace && !path.endsWith("/shift/")) {
            const link = element("a", "is-primary", "Рабочая смена");
            link.href = workspace;
            actions.append(link);
        }
        topbar.append(mainArea, actions);
        return topbar;
    }

    function activateShell() {
        const shell = element("div", "eod-da-shell");
        shell.dataset.opjDirectionAShell = "";
        const stage = element("div", "eod-da-stage");
        const content = element("div", "eod-da-content");
        const messages = document.querySelector("body > .messages");
        shell.append(buildSidebar());
        stage.append(buildTopbar());
        if (messages) {
            content.append(messages);
        }
        content.append(main);
        stage.append(content);
        shell.append(stage);
        document.body.insertBefore(shell, document.body.firstChild);

        const scrim = element("button", "eod-da-sidebar-scrim");
        scrim.type = "button";
        scrim.hidden = true;
        scrim.dataset.opjMenuScrim = "";
        scrim.setAttribute("aria-label", "Закрыть навигацию");
        document.body.append(scrim);
        document.body.classList.add("eod-da-active", "opj-direction-a");

        const toggle = shell.querySelector("[data-opj-menu-toggle]");
        const setOpen = (open) => {
            document.body.classList.toggle("eod-da-nav-open", open);
            scrim.hidden = !open;
            toggle?.setAttribute("aria-expanded", String(open));
        };
        toggle?.addEventListener("click", () => {
            setOpen(!document.body.classList.contains("eod-da-nav-open"));
        });
        scrim.addEventListener("click", () => setOpen(false));
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && document.body.classList.contains("eod-da-nav-open")) {
                setOpen(false);
            }
        });
    }

    function addWorkBoundary() {
        const workspace = main.querySelector("[data-draft-workspace]");
        if (!workspace || main.querySelector("[data-opj-work-boundary]")) {
            return;
        }
        const boundary = element("section", "opj-work-boundary");
        boundary.dataset.opjWorkBoundary = "";
        const copy = element("div");
        copy.append(
            element("strong", "", "Рабочий черновик текущей смены"),
            element(
                "p",
                "",
                "Черновые записи сохраняются отдельно от зарегистрированного журнала. Регистрация, передача и закрытие смены в OPJ-UX-001 не выполняются.",
            ),
        );
        boundary.append(copy, element("span", "opj-boundary-chip", "Автосохранение активно"));
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
    }

    function sanitizeRegisteredTable(table) {
        const clone = table.cloneNode(true);
        clone.querySelectorAll("[id]").forEach((node) => node.removeAttribute("id"));
        clone.querySelectorAll("form, button").forEach((node) => node.remove());
        return clone;
    }

    async function addRegisteredContext() {
        const workspace = main.querySelector("[data-draft-workspace]");
        const url = detailUrl();
        if (!workspace || !url || main.querySelector("[data-opj-registered-context]")) {
            return;
        }

        const context = element("details", "opj-registered-context is-loading");
        context.dataset.opjRegisteredContext = "";
        context.open = true;
        const summary = element("summary");
        const heading = element("span", "opj-registered-context-heading");
        heading.append(
            element("span", "", "Только чтение"),
            element("strong", "", "Зарегистрированные записи"),
        );
        const meta = element("span", "opj-registered-context-meta", "Загрузка…");
        summary.append(heading, meta);
        const body = element("div", "opj-registered-context-body", "Загрузка зарегистрированного журнала…");
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
                element("span", "", "Записи показаны в хронологическом порядке и не редактируются из рабочей области."),
            );
            const fullLink = element("a", "", "Открыть утверждённую форму");
            fullLink.href = url;
            note.append(fullLink);
            const wrap = element("div", "opj-registered-table-wrap");
            wrap.append(table);
            body.replaceChildren(note, wrap);
            meta.textContent = `${count} ${count === 1 ? "запись" : "записей"}`;
            context.classList.remove("is-loading");
        } catch (_error) {
            const fallback = element("div", "opj-registered-context-note");
            fallback.append(element("span", "", "Не удалось встроить зарегистрированные записи."));
            const link = element("a", "", "Открыть журнал");
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
        const text = (node.textContent || "").trim();
        return [...items]
            .sort((left, right) => String(right.label || "").length - String(left.label || "").length)
            .find((item) => text.includes(String(item.label || ""))) || null;
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
            const tree = element("div", "opj-reference-tree");
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
                const siteGroup = element("details", "opj-reference-tree-site");
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

    activateShell();
    renameRegisteredAction();
    addWorkBoundary();
    void addRegisteredContext();
    enhanceEquipmentHierarchy();
})();
