(() => {
    "use strict";

    const SELECTOR = 'select[data-defect-tree-select="workplace"]';

    function normalize(value) {
        return String(value || "")
            .toLocaleLowerCase("ru-RU")
            .replaceAll("ё", "е")
            .replace(/\s+/g, " ")
            .trim();
    }

    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function makeOptionButton(item, select, close, syncControl) {
        const button = element("button", "defect-tree-option");
        button.type = "button";
        button.setAttribute("role", "option");
        button.dataset.value = item.value;
        button.dataset.search = item.search;
        button.setAttribute(
            "aria-selected",
            select.value === item.value ? "true" : "false",
        );
        button.append(
            element("strong", "", item.label),
            element("small", "", [item.code, item.organization].filter(Boolean).join(" · ")),
        );
        button.addEventListener("click", () => {
            select.value = item.value;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            syncControl();
            close();
        });
        return button;
    }

    function createDivisionNode(id, name) {
        return {
            id,
            name: name || "Без подразделения",
            parentId: "",
            children: new Map(),
            items: [],
        };
    }

    function buildHierarchy(items) {
        const divisions = new Map();
        const rootItems = [];

        items.forEach((item) => {
            if (!item.divisionId) {
                rootItems.push(item);
                return;
            }
            if (!divisions.has(item.divisionId)) {
                divisions.set(
                    item.divisionId,
                    createDivisionNode(item.divisionId, item.division),
                );
            }
            const division = divisions.get(item.divisionId);
            division.parentId = item.divisionParentId || division.parentId;
            division.items.push(item);

            if (item.divisionParentId && !divisions.has(item.divisionParentId)) {
                divisions.set(
                    item.divisionParentId,
                    createDivisionNode(item.divisionParentId, item.divisionParentName),
                );
            }
        });

        const roots = [];
        divisions.forEach((division) => {
            const parent = division.parentId && divisions.get(division.parentId);
            if (parent && parent !== division) parent.children.set(division.id, division);
            else roots.push(division);
        });

        return { roots, rootItems };
    }

    function renderDivision(division, select, close, syncControl, visited = new Set()) {
        if (visited.has(division.id)) return document.createDocumentFragment();
        const nextVisited = new Set(visited);
        nextVisited.add(division.id);

        const details = element("details", "defect-tree-workplace-division");
        details.open = true;
        details.appendChild(element("summary", "", division.name));
        const body = element("div", "defect-tree-workplace-body");

        [...division.children.values()]
            .sort((a, b) => a.name.localeCompare(b.name, "ru"))
            .forEach((child) => {
                body.appendChild(
                    renderDivision(child, select, close, syncControl, nextVisited),
                );
            });

        division.items
            .sort((a, b) => a.label.localeCompare(b.label, "ru"))
            .forEach((item) => {
                body.appendChild(makeOptionButton(item, select, close, syncControl));
            });

        details.appendChild(body);
        return details;
    }

    function buildTree(items, select, close, syncControl) {
        const root = element("div", "defect-tree-content");
        const organizations = new Map();

        items.forEach((item) => {
            const key = item.organization || "Организация";
            if (!organizations.has(key)) organizations.set(key, []);
            organizations.get(key).push(item);
        });

        [...organizations.entries()]
            .sort(([a], [b]) => a.localeCompare(b, "ru"))
            .forEach(([organization, organizationItems]) => {
                const group = element("details", "defect-tree-group");
                group.open = true;
                group.appendChild(element("summary", "", organization));
                const body = element("div", "defect-tree-group-body");
                const hierarchy = buildHierarchy(organizationItems);

                hierarchy.roots
                    .sort((a, b) => a.name.localeCompare(b.name, "ru"))
                    .forEach((division) => {
                        body.appendChild(
                            renderDivision(division, select, close, syncControl),
                        );
                    });

                if (hierarchy.rootItems.length) {
                    const ungrouped = createDivisionNode("ungrouped", "Без подразделения");
                    ungrouped.items = hierarchy.rootItems;
                    body.appendChild(
                        renderDivision(ungrouped, select, close, syncControl),
                    );
                }

                group.appendChild(body);
                root.appendChild(group);
            });
        return root;
    }

    function filterTree(wrapper, query) {
        const needle = normalize(query);
        const options = [...wrapper.querySelectorAll(".defect-tree-option")];
        options.forEach((option) => {
            option.hidden = Boolean(needle && !option.dataset.search.includes(needle));
        });

        [...wrapper.querySelectorAll(".defect-tree-workplace-division")]
            .reverse()
            .forEach((division) => {
                const visible = [...division.querySelectorAll(".defect-tree-option")]
                    .some((option) => !option.hidden);
                division.hidden = !visible;
                if (needle && visible) division.open = true;
            });

        [...wrapper.querySelectorAll(".defect-tree-group")].forEach((group) => {
            const visible = [...group.querySelectorAll(".defect-tree-option")]
                .some((option) => !option.hidden);
            group.hidden = !visible;
            if (needle && visible) group.open = true;
        });

        const empty = wrapper.querySelector("[data-defect-tree-empty]");
        if (empty) empty.hidden = options.some((option) => !option.hidden);
    }

    function initWorkplaceTree(select, index) {
        if (select.dataset.treeEnhanced === "true") return;
        select.dataset.treeEnhanced = "true";

        const items = [...select.options]
            .filter((option) => option.value)
            .map((option) => ({
                value: option.value,
                label: option.textContent.trim(),
                code: option.dataset.treeCode || "",
                organization: option.dataset.treeOrganization || "Организация",
                divisionId: option.dataset.treeDivisionId || "",
                division: option.dataset.treeDivision || "",
                divisionParentId: option.dataset.treeDivisionParent || "",
                divisionParentName: option.dataset.treeDivisionParentName || "",
                search: normalize([
                    option.textContent,
                    option.dataset.treeCode,
                    option.dataset.treeOrganization,
                    option.dataset.treeDivision,
                    option.dataset.treeDivisionParentName,
                ].filter(Boolean).join(" ")),
            }));

        const wrapper = element(
            "div",
            "defect-tree-selector defect-tree-selector--workplace",
        );
        const control = element("div", "defect-tree-control");
        const input = element("input", "defect-tree-input");
        input.type = "search";
        input.autocomplete = "off";
        input.spellcheck = false;
        input.id = `${select.id || `defect-workplace-${index}`}-search`;
        input.placeholder = select.dataset.treePlaceholder
            || "Введите подразделение или рабочее место";
        input.setAttribute("role", "combobox");
        input.setAttribute("aria-autocomplete", "list");
        input.setAttribute("aria-expanded", "false");

        const clear = element("button", "defect-tree-clear", "×");
        clear.type = "button";
        clear.setAttribute("aria-label", "Очистить выбор");

        const panel = element("div", "defect-tree-panel");
        panel.hidden = true;
        panel.id = `${input.id}-panel`;
        panel.setAttribute("role", "listbox");
        input.setAttribute("aria-controls", panel.id);

        const panelHeader = element("div", "defect-tree-panel-header");
        panelHeader.append(
            element("strong", "", "Дерево рабочих мест"),
            element("small", "", "Подразделение → рабочее место"),
        );
        const panelBody = element("div", "defect-tree-panel-body");
        const empty = element(
            "div",
            "defect-tree-empty",
            "По введённому тексту ничего не найдено.",
        );
        empty.dataset.defectTreeEmpty = "true";
        empty.hidden = true;

        const close = () => {
            panel.hidden = true;
            input.setAttribute("aria-expanded", "false");
            wrapper.classList.remove("is-open");
            syncControl();
        };

        const syncControl = () => {
            const selected = select.selectedOptions[0];
            const label = selected && selected.value
                ? selected.textContent.trim()
                : "";
            input.dataset.selectedLabel = label;
            input.value = label;
            clear.hidden = !label;
            wrapper.querySelectorAll(".defect-tree-option").forEach((option) => {
                option.setAttribute(
                    "aria-selected",
                    option.dataset.value === select.value ? "true" : "false",
                );
            });
            filterTree(wrapper, "");
        };

        panelBody.append(buildTree(items, select, close, syncControl), empty);
        panel.append(panelHeader, panelBody);
        control.append(input, clear);
        wrapper.append(control, panel);
        select.insertAdjacentElement("afterend", wrapper);
        select.classList.add("defect-native-select--enhanced");
        select.tabIndex = -1;
        select.setAttribute("aria-hidden", "true");

        const label = document.querySelector(`label[for="${CSS.escape(select.id)}"]`);
        if (label) label.htmlFor = input.id;

        const open = () => {
            panel.hidden = false;
            input.setAttribute("aria-expanded", "true");
            wrapper.classList.add("is-open");
            filterTree(
                wrapper,
                input.value === input.dataset.selectedLabel ? "" : input.value,
            );
        };

        input.addEventListener("focus", open);
        input.addEventListener("click", open);
        input.addEventListener("input", () => {
            open();
            filterTree(wrapper, input.value);
        });
        input.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                event.preventDefault();
                close();
                input.blur();
            } else if (event.key === "ArrowDown") {
                const first = [...wrapper.querySelectorAll(".defect-tree-option")]
                    .find((option) => !option.hidden);
                if (first) {
                    event.preventDefault();
                    first.focus();
                }
            } else if (event.key === "Enter" && !panel.hidden) {
                const visible = [...wrapper.querySelectorAll(".defect-tree-option")]
                    .filter((option) => !option.hidden);
                if (visible.length === 1) {
                    event.preventDefault();
                    visible[0].click();
                }
            }
        });

        clear.addEventListener("click", () => {
            select.value = "";
            select.dispatchEvent(new Event("change", { bubbles: true }));
            syncControl();
            input.focus();
            open();
        });
        select.addEventListener("change", syncControl);
        document.addEventListener("pointerdown", (event) => {
            if (!wrapper.contains(event.target)) close();
        });
        select.form?.addEventListener("submit", syncControl);
        syncControl();
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(SELECTOR).forEach(initWorkplaceTree);
    });
})();