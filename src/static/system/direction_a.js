(() => {
    "use strict";

    const path = window.location.pathname;
    const originalTopbar = document.querySelector("body > .topbar");
    const main = document.querySelector("body > main");
    const iconsUrl = "/static/system/icons.svg";

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

    function text(node, fallback = "") {
        return (node?.textContent || fallback).trim();
    }

    function hrefFor(label, fallback) {
        const candidate = Array.from(originalTopbar?.querySelectorAll("a") || []).find(
            (link) => text(link) === label,
        );
        return candidate?.href || fallback;
    }

    function userIdentity() {
        const name = text(originalTopbar?.querySelector(".user-menu-label"), "Пользователь");
        const role = text(
            originalTopbar?.querySelector(".user-menu-identity span"),
            "Оперативный персонал",
        );
        const initial = text(
            originalTopbar?.querySelector(".user-avatar"),
            name.slice(0, 1) || "П",
        );
        return {name, role, initial};
    }

    function currentTitle() {
        return text(
            main?.querySelector("h1"),
            document.title.split("·")[0] || "Электронная оперативная документация",
        );
    }

    function currentContext() {
        return text(
            main?.querySelector(".shift-book-meta-period"),
            text(
                main?.querySelector(".journal-workplace"),
                path === "/"
                    ? "Рабочее пространство"
                    : "Электронная оперативная документация",
            ),
        );
    }

    function isOperationalJournal() {
        return path.startsWith("/operations/journal/");
    }

    function activeArea() {
        if (isOperationalJournal()) {
            return "operational-log";
        }
        if (path.startsWith("/operations/defects/")) {
            return "equipment-defects";
        }
        if (path === "/") {
            return "home";
        }
        return "";
    }

    function navLink(label, fallback, iconName, area, child = false) {
        const link = element("a", child ? "da-nav-child" : "");
        link.href = hrefFor(label, fallback);
        if (activeArea() === area) {
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
        const group = element("section", "da-nav-group");
        const heading = element("div", "da-nav-group-title");
        heading.append(icon(iconName), element("span", "", title));
        group.append(heading, ...links);
        return group;
    }

    function buildSidebar() {
        const identity = userIdentity();
        const sidebar = element("aside", "da-sidebar");
        sidebar.id = "direction-a-sidebar";
        sidebar.dataset.directionASidebar = "";

        const brand = element("a", "da-brand");
        brand.href = hrefFor("Главная", "/");
        brand.append(element("span", "da-brand-mark", "ЭОД"));
        const brandCopy = element("span", "da-brand-copy");
        brandCopy.append(
            element("strong", "", "ЭОД"),
            element("small", "", "Оперативная документация"),
        );
        brand.append(brandCopy);

        const context = element("section", "da-context");
        context.setAttribute("aria-label", "Рабочий контекст");
        context.append(
            element(
                "span",
                "",
                isOperationalJournal()
                    ? (path.includes("/shift/") ? "Рабочая смена" : "Оперативный журнал")
                    : "Рабочее место",
            ),
            element("strong", "", currentTitle()),
            element("small", "", currentContext()),
        );

        const navigation = element("nav", "da-navigation");
        navigation.setAttribute("aria-label", "Навигация ЭОД");
        navigation.append(
            navLink("Рабочий стол", "/", "home", "home"),
            navGroup("Оперативная документация", "document", [
                navLink(
                    "Оперативный журнал",
                    "/operations/journal/",
                    "document",
                    "operational-log",
                    true,
                ),
            ]),
            navGroup("Журналы", "journal", [
                navLink(
                    "Журнал дефектов",
                    "/operations/defects/",
                    "journal",
                    "equipment-defects",
                    true,
                ),
                navLink(
                    "Оперативные документы",
                    "/operational-documents/",
                    "journal",
                    "",
                    true,
                ),
            ]),
            navLink("Документы", "/documents/", "document", ""),
            navLink("Оборудование", "/equipment/", "equipment", ""),
            navLink("Управление и ведение", "/dispatching/", "management", ""),
            navGroup("Справочники и данные", "directory", [
                navLink(
                    "Организация и персонал",
                    "/organization/",
                    "directory",
                    "",
                    true,
                ),
                navLink(
                    "Перечни документации",
                    "/workplace-documentation/",
                    "document",
                    "",
                    true,
                ),
                navLink("Импорт данных", "/imports/", "directory", "", true),
            ]),
        );

        const user = element("a", "da-user");
        user.href = hrefFor("Учётная запись и интерфейс", "/accounts/me/");
        user.append(element("span", "da-user-avatar", identity.initial));
        const copy = element("span", "da-user-copy");
        copy.append(
            element("strong", "", identity.name),
            element("small", "", identity.role),
        );
        user.append(copy, icon("settings"));

        sidebar.append(brand, context, navigation, user);
        return sidebar;
    }

    function topbarAction(href, label, iconName, className = "") {
        const link = element("a", className);
        link.href = href;
        link.title = label;
        link.append(icon(iconName), element("span", "visually-hidden", label));
        return link;
    }

    function buildLogoutAction() {
        const source = originalTopbar?.querySelector(".user-menu form");
        if (!source) {
            return null;
        }
        const form = source.cloneNode(true);
        form.querySelector("button")?.classList.add("da-icon-button");
        const button = form.querySelector("button");
        if (button) {
            button.replaceChildren(icon("logout"), element("span", "visually-hidden", "Выйти"));
            button.title = "Выйти";
        }
        return form;
    }

    function detailUrl() {
        if (!isOperationalJournal()) {
            return null;
        }
        if (path.includes("/shift/")) {
            return path.replace("/shift/", "/");
        }
        return /^\/operations\/journal\/\d+\/$/.test(path) ? path : null;
    }

    function workspaceUrl() {
        if (!isOperationalJournal()) {
            return null;
        }
        const match = path.match(/^\/operations\/journal\/(\d+)\/(?:shift\/)?$/);
        return match ? `/operations/journal/${match[1]}/shift/` : null;
    }

    function buildTopbar() {
        const topbar = element("header", "da-topbar");
        topbar.dataset.directionATopbar = "";
        const mainArea = element("div", "da-topbar-main");
        const menuButton = element("button", "da-menu-button");
        menuButton.type = "button";
        menuButton.dataset.directionAMenuToggle = "";
        menuButton.setAttribute("aria-label", "Открыть навигацию");
        menuButton.setAttribute("aria-controls", "direction-a-sidebar");
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.append(icon("menu"));

        const workplace = element("div", "da-workplace");
        workplace.append(
            element("span", "", "Рабочее место"),
            element("strong", "", currentContext()),
        );
        mainArea.append(menuButton, workplace);

        const tools = element("div", "da-topbar-tools");
        const date = element("span", "da-topbar-value");
        date.dataset.directionADate = "";
        date.append(icon("document"), element("span", "", ""));
        const time = element("span", "da-topbar-value");
        time.dataset.directionATime = "";
        time.append(icon("history"), element("span", "", ""));
        tools.append(
            date,
            time,
            topbarAction("/_health/", "Проверка состояния", "info"),
            topbarAction(
                hrefFor("Учётная запись и интерфейс", "/accounts/me/"),
                "Настройки пользователя",
                "user",
            ),
        );
        const logout = buildLogoutAction();
        if (logout) {
            tools.append(logout);
        }

        if (isOperationalJournal()) {
            const registered = detailUrl();
            const workspace = workspaceUrl();
            if (path.includes("/shift/") && registered) {
                const link = element("a", "da-button is-secondary is-compact", "Зарегистрированный журнал");
                link.href = registered;
                tools.prepend(link);
            } else if (workspace && !path.endsWith("/shift/")) {
                const link = element("a", "da-button is-compact", "Рабочая смена");
                link.href = workspace;
                tools.prepend(link);
            }
        }

        topbar.append(mainArea, tools);
        return topbar;
    }

    function updateClock(root = document) {
        const now = new Date();
        const date = root.querySelector("[data-direction-a-date] span:last-child");
        const time = root.querySelector("[data-direction-a-time] span:last-child");
        if (date) {
            date.textContent = new Intl.DateTimeFormat("ru-RU", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
            }).format(now);
        }
        if (time) {
            time.textContent = new Intl.DateTimeFormat("ru-RU", {
                hour: "2-digit",
                minute: "2-digit",
            }).format(now);
        }
    }

    function bindMobileNavigation(shell, scrim) {
        const toggle = shell.querySelector("[data-direction-a-menu-toggle]");
        const setOpen = (open) => {
            document.body.classList.toggle("da-nav-open", open);
            scrim.hidden = !open;
            toggle?.setAttribute("aria-expanded", String(open));
        };
        toggle?.addEventListener("click", () => {
            setOpen(!document.body.classList.contains("da-nav-open"));
        });
        scrim.addEventListener("click", () => setOpen(false));
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && document.body.classList.contains("da-nav-open")) {
                setOpen(false);
            }
        });
    }

    function buildGeneratedShell() {
        if (!main || !originalTopbar || document.querySelector("[data-direction-a-shell]")) {
            return;
        }
        if (!(isOperationalJournal() || path === "/")) {
            return;
        }
        if (!originalTopbar.querySelector(".user-menu")) {
            return;
        }

        const shell = element("div", "da-shell");
        shell.dataset.directionAShell = "";
        shell.dataset.directionAGenerated = "true";
        const stage = element("div", "da-stage");
        const content = element("div", "da-content");
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

        const scrim = element("button", "da-sidebar-scrim");
        scrim.type = "button";
        scrim.hidden = true;
        scrim.dataset.directionAScrim = "";
        scrim.setAttribute("aria-label", "Закрыть навигацию");
        document.body.append(scrim);

        document.body.classList.add("da-active");
        if (isOperationalJournal()) {
            document.body.classList.add("opj-direction-a");
        } else if (path === "/") {
            document.body.classList.add("home-direction-a");
        }
        bindMobileNavigation(shell, scrim);
        updateClock(shell);
        window.setInterval(() => updateClock(shell), 30000);
    }

    function addClasses(selector, ...classes) {
        document.querySelectorAll(selector).forEach((node) => node.classList.add(...classes));
    }

    function adoptServerRenderedShell() {
        const shell = document.querySelector(".defect-da-shell");
        if (!shell) {
            return;
        }
        shell.classList.add("da-shell");
        shell.dataset.directionAShell = "";
        addClasses(".defect-da-stage", "da-stage");
        addClasses(".defect-da-sidebar", "da-sidebar");
        addClasses(".defect-da-brand", "da-brand");
        addClasses(".defect-da-brand-mark", "da-brand-mark");
        addClasses(".defect-da-brand-copy", "da-brand-copy");
        addClasses(".defect-da-shift", "da-context");
        addClasses(".defect-da-navigation", "da-navigation");
        addClasses(".defect-da-nav-group", "da-nav-group");
        addClasses(".defect-da-nav-group-title", "da-nav-group-title");
        addClasses(".defect-da-nav-child", "da-nav-child");
        addClasses(".defect-da-user", "da-user");
        addClasses(".defect-da-user-avatar", "da-user-avatar");
        addClasses(".defect-da-topbar", "da-topbar");
        addClasses(".defect-da-menu-button", "da-menu-button");
        addClasses(".defect-da-workplace", "da-workplace");
        addClasses(".defect-da-topbar-tools", "da-topbar-tools");
        addClasses(".defect-da-topbar-value", "da-topbar-value");
        addClasses(".defect-da-page", "da-page");
        addClasses(".defect-da-page-header", "da-page-header");
        addClasses(".defect-module-actions", "da-actions");
        addClasses(".defect-button", "da-button");
        addClasses(".defect-button.secondary", "is-secondary");
        addClasses(".defect-command-center", "da-panel-flat");
        addClasses(".defect-view-switch", "da-segmented");
        addClasses(".defect-field", "da-field");
        addClasses(".defect-status", "da-status");
        addClasses(".defect-register-wrap", "da-table-wrap");
        addClasses(".defect-register", "da-table");
        addClasses(".defect-da-sidebar-scrim", "da-sidebar-scrim");
        document.body.classList.add("da-active", "defect-direction-a");
    }

    adoptServerRenderedShell();
    buildGeneratedShell();
})();
