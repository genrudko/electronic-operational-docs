(() => {
    "use strict";

    const TREE_SELECTOR = "select[data-defect-tree-select]";
    const DATE_TIME_SELECTOR = "input[data-defect-datetime]";

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

    function setExpanded(toggle, children, expanded) {
        toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        toggle.textContent = expanded ? "−" : "+";
        children.hidden = !expanded;
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

        const primary = element("strong", "", item.primary);
        const secondary = element("small", "", item.secondary);
        button.append(primary, secondary);

        button.addEventListener("click", () => {
            select.value = item.value;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            syncControl();
            close();
        });
        return button;
    }

    function makeEquipmentNode(item, itemMap, select, close, syncControl, visited) {
        const node = element("div", "defect-tree-node");
        if (visited.has(item.id)) return node;
        visited.add(item.id);

        const childrenItems = item.children
            .map((id) => itemMap.get(id))
            .filter(Boolean)
            .sort((a, b) => a.primary.localeCompare(b.primary, "ru"));

        const line = element("div", "defect-tree-node-line");
        let children = null;
        if (childrenItems.length) {
            const toggle = element("button", "defect-tree-branch-toggle", "+");
            toggle.type = "button";
            toggle.setAttribute("aria-expanded", "false");
            toggle.setAttribute("aria-label", `Развернуть ${item.primary}`);
            children = element("div", "defect-tree-children");
            children.hidden = true;
            toggle.addEventListener("click", () => {
                setExpanded(
                    toggle,
                    children,
                    toggle.getAttribute("aria-expanded") !== "true",
                );
            });
            line.appendChild(toggle);
        } else {
            line.appendChild(element("span", "defect-tree-branch-spacer"));
        }

        line.appendChild(makeOptionButton(item, select, close, syncControl));
        node.appendChild(line);

        const descendantSearch = [];
        if (children) {
            childrenItems.forEach((child) => {
                const childNode = makeEquipmentNode(
                    child,
                    itemMap,
                    select,
                    close,
                    syncControl,
                    new Set(visited),
                );
                descendantSearch.push(childNode.dataset.subtreeSearch || "");
                children.appendChild(childNode);
            });
            node.appendChild(children);
        }
        node.dataset.ownSearch = item.search;
        node.dataset.subtreeSearch = normalize(
            `${item.search} ${descendantSearch.join(" ")}`,
        );
        return node;
    }

    function buildEquipmentTree(items, select, close, syncControl) {
        const root = element("div", "defect-tree-content");
        const sites = new Map();

        items.forEach((item) => {
            const siteKey = item.siteId || item.site || "other";
            if (!sites.has(siteKey)) {
                sites.set(siteKey, {
                    name: item.site || "Без энергообъекта",
                    items: [],
                });
            }
            sites.get(siteKey).items.push(item);
        });

        [...sites.values()]
            .sort((a, b) => a.name.localeCompare(b.name, "ru"))
            .forEach((site) => {
                const group = element("details", "defect-tree-group");
                group.open = true;
                group.dataset.search = normalize(site.name);
                const summary = element("summary", "", site.name);
                const body = element("div", "defect-tree-group-body");
                const itemMap = new Map(site.items.map((item) => [item.id, item]));

                site.items.forEach((item) => {
                    item.children = [];
                });
                site.items.forEach((item) => {
                    if (item.parent && itemMap.has(item.parent) && item.parent !== item.id) {
                        itemMap.get(item.parent).children.push(item.id);
                    }
                });

                const roots = site.items
                    .filter((item) => !item.parent || !itemMap.has(item.parent))
                    .sort((a, b) => a.primary.localeCompare(b.primary, "ru"));
                roots.forEach((item) => {
                    body.appendChild(
                        makeEquipmentNode(
                            item,
                            itemMap,
                            select,
                            close,
                            syncControl,
                            new Set(),
                        ),
                    );
                });
                group.append(summary, body);
                root.appendChild(group);
            });
        return root;
    }

    function buildPersonnelTree(items, select, close, syncControl) {
        const root = element("div", "defect-tree-content");
        const divisions = new Map();

        items.forEach((item) => {
            const key = item.divisionId || item.division || "other";
            if (!divisions.has(key)) {
                divisions.set(key, {
                    name: item.division || "Без подразделения",
                    positions: new Map(),
                });
            }
            const division = divisions.get(key);
            const positionKey = item.positionId || item.position || "other";
            if (!division.positions.has(positionKey)) {
                division.positions.set(positionKey, {
                    name: item.position || "Должность не указана",
                    items: [],
                });
            }
            division.positions.get(positionKey).items.push(item);
        });

        [...divisions.values()]
            .sort((a, b) => a.name.localeCompare(b.name, "ru"))
            .forEach((division) => {
                const group = element("details", "defect-tree-group");
                group.open = true;
                group.dataset.search = normalize(division.name);
                const summary = element("summary", "", division.name);
                const body = element("div", "defect-tree-group-body");

                [...division.positions.values()]
                    .sort((a, b) => a.name.localeCompare(b.name, "ru"))
                    .forEach((position) => {
                        const positionNode = element("details", "defect-tree-position");
                        positionNode.open = true;
                        positionNode.dataset.search = normalize(position.name);
                        const positionSummary = element(
                            "summary",
                            "",
                            position.name,
                        );
                        const options = element("div", "defect-tree-position-options");
                        position.items
                            .sort((a, b) => a.primary.localeCompare(b.primary, "ru"))
                            .forEach((item) => {
                                options.appendChild(
                                    makeOptionButton(
                                        item,
                                        select,
                                        close,
                                        syncControl,
                                    ),
                                );
                            });
                        positionNode.append(positionSummary, options);
                        body.appendChild(positionNode);
                    });
                group.append(summary, body);
                root.appendChild(group);
            });
        return root;
    }

    function filterTree(wrapper, query) {
        const normalizedQuery = normalize(query);
        const options = [...wrapper.querySelectorAll(".defect-tree-option")];

        options.forEach((option) => {
            option.hidden = Boolean(
                normalizedQuery && !option.dataset.search.includes(normalizedQuery),
            );
        });

        [...wrapper.querySelectorAll(".defect-tree-node")]
            .reverse()
            .forEach((node) => {
                const visible = !normalizedQuery
                    || node.dataset.subtreeSearch.includes(normalizedQuery);
                node.hidden = !visible;
                if (normalizedQuery && visible) {
                    const toggle = node.querySelector(
                        ":scope > .defect-tree-node-line > .defect-tree-branch-toggle",
                    );
                    const children = node.querySelector(
                        ":scope > .defect-tree-children",
                    );
                    if (toggle && children) setExpanded(toggle, children, true);
                }
            });

        [...wrapper.querySelectorAll(".defect-tree-position")].forEach((position) => {
            const visible = [...position.querySelectorAll(".defect-tree-option")]
                .some((option) => !option.hidden);
            position.hidden = !visible;
            if (normalizedQuery && visible) position.open = true;
        });

        [...wrapper.querySelectorAll(".defect-tree-group")].forEach((group) => {
            const visible = [...group.querySelectorAll(".defect-tree-option")]
                .some((option) => !option.hidden);
            group.hidden = !visible;
            if (normalizedQuery && visible) group.open = true;
        });

        const empty = wrapper.querySelector("[data-defect-tree-empty]");
        if (empty) empty.hidden = options.some((option) => !option.hidden);
    }

    function initTreeSelect(select, index) {
        if (select.dataset.treeEnhanced === "true") return;
        select.dataset.treeEnhanced = "true";

        const kind = select.dataset.defectTreeSelect;
        const options = [...select.options].filter((option) => option.value);
        const items = options.map((option) => {
            const label = option.textContent.trim();
            const code = option.dataset.treeCode || "";
            const position = option.dataset.treePosition || "";
            const type = option.dataset.treeType || "";
            const workplace = option.dataset.treeWorkplace || "";
            return {
                value: option.value,
                id: option.dataset.treeId || option.value,
                parent: option.dataset.treeParent || "",
                siteId: option.dataset.treeSiteId || "",
                site: option.dataset.treeSite || "",
                divisionId: option.dataset.treeDivisionId || "",
                division: option.dataset.treeDivision || "",
                positionId: option.dataset.treePositionId || "",
                position,
                primary: label,
                secondary: kind === "equipment"
                    ? [type, code].filter(Boolean).join(" · ")
                    : [position, workplace].filter(Boolean).join(" · "),
                search: normalize(
                    [
                        label,
                        code,
                        type,
                        option.dataset.treeSite,
                        option.dataset.treeDivision,
                        position,
                        workplace,
                    ].filter(Boolean).join(" "),
                ),
                children: [],
            };
        });

        const wrapper = element(
            "div",
            `defect-tree-selector defect-tree-selector--${kind}`,
        );
        const control = element("div", "defect-tree-control");
        const input = element("input", "defect-tree-input");
        input.type = "search";
        input.autocomplete = "off";
        input.spellcheck = false;
        input.id = `${select.id || `defect-tree-${index}`}-search`;
        input.placeholder = select.dataset.treePlaceholder
            || (kind === "equipment"
                ? "Введите код или название оборудования"
                : "Введите Ф.И.О. или должность");
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
            element(
                "strong",
                "",
                kind === "equipment" ? "Дерево оборудования" : "Персонал по должностям",
            ),
            element(
                "small",
                "",
                kind === "equipment"
                    ? "Энергообъект → оборудование"
                    : "Подразделение → должность → сотрудник",
            ),
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

        const content = kind === "equipment"
            ? buildEquipmentTree(items, select, close, syncControl)
            : buildPersonnelTree(items, select, close, syncControl);
        panelBody.append(content, empty);
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
            filterTree(wrapper, input.value === input.dataset.selectedLabel ? "" : input.value);
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

    function digitsMask(value, groups, separator) {
        const digits = String(value || "").replace(/\D/g, "").slice(
            0,
            groups.reduce((sum, group) => sum + group, 0),
        );
        const chunks = [];
        let cursor = 0;
        groups.forEach((size) => {
            if (cursor < digits.length) {
                chunks.push(digits.slice(cursor, cursor + size));
                cursor += size;
            }
        });
        return chunks.join(separator);
    }

    function parseDate(value) {
        const match = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(value);
        if (!match) return null;
        const day = Number(match[1]);
        const month = Number(match[2]);
        const year = Number(match[3]);
        const probe = new Date(year, month - 1, day);
        if (
            probe.getFullYear() !== year
            || probe.getMonth() !== month - 1
            || probe.getDate() !== day
        ) return null;
        return {
            day: match[1],
            month: match[2],
            year: match[3],
        };
    }

    function parseTime(value) {
        const match = /^(\d{2}):(\d{2})$/.exec(value);
        if (!match) return null;
        const hour = Number(match[1]);
        const minute = Number(match[2]);
        if (hour > 23 || minute > 59) return null;
        return { hour: match[1], minute: match[2] };
    }

    function serverNowFactory() {
        const trust = document.querySelector("[data-defect-time-trust]");
        const epoch = Number(trust?.dataset.serverEpoch) * 1000;
        const loadedAt = performance.now();
        if (!Number.isFinite(epoch)) return () => new Date();
        return () => new Date(epoch + (performance.now() - loadedAt));
    }

    function initMaskedDateTime(native, index, now) {
        if (native.dataset.repair3Enhanced === "true") return;
        native.dataset.repair3Enhanced = "true";

        let sibling = native.nextElementSibling;
        while (sibling && sibling.classList.contains("defect-datetime-control")) {
            const next = sibling.nextElementSibling;
            sibling.remove();
            sibling = next;
        }

        const wrapper = element("div", "defect-manual-datetime");
        const dateLabel = element("label", "defect-manual-datetime-part");
        const dateCaption = element("span", "", "Дата");
        const dateInput = element("input", "defect-manual-date");
        dateInput.type = "text";
        dateInput.inputMode = "numeric";
        dateInput.autocomplete = "off";
        dateInput.placeholder = "ДД.ММ.ГГГГ";
        dateInput.maxLength = 10;
        dateInput.id = `${native.id || `defect-datetime-${index}`}-date`;
        dateLabel.htmlFor = dateInput.id;
        dateLabel.append(dateCaption, dateInput);

        const timeLabel = element("label", "defect-manual-datetime-part");
        const timeCaption = element("span", "", "Время (МСК)");
        const timeInput = element("input", "defect-manual-time");
        timeInput.type = "text";
        timeInput.inputMode = "numeric";
        timeInput.autocomplete = "off";
        timeInput.placeholder = "ЧЧ:ММ";
        timeInput.maxLength = 5;
        timeInput.id = `${native.id || `defect-datetime-${index}`}-time`;
        timeLabel.htmlFor = timeInput.id;
        timeLabel.append(timeCaption, timeInput);

        const warning = element(
            "small",
            "defect-manual-datetime-error",
            "Проверьте дату и время.",
        );
        warning.hidden = true;

        const initial = String(native.value || "");
        const [initialDate = "", initialTime = ""] = initial.split("T");
        if (/^\d{4}-\d{2}-\d{2}$/.test(initialDate)) {
            const [year, month, day] = initialDate.split("-");
            dateInput.value = `${day}.${month}.${year}`;
        }
        timeInput.value = initialTime.slice(0, 5);

        const setValidity = (show) => {
            const dateValid = Boolean(parseDate(dateInput.value));
            const timeValid = Boolean(parseTime(timeInput.value));
            const invalid = show && (!dateValid || !timeValid);
            dateInput.classList.toggle("is-invalid", invalid && !dateValid);
            timeInput.classList.toggle("is-invalid", invalid && !timeValid);
            dateInput.setAttribute("aria-invalid", invalid && !dateValid ? "true" : "false");
            timeInput.setAttribute("aria-invalid", invalid && !timeValid ? "true" : "false");
            warning.hidden = !invalid;
            return dateValid && timeValid;
        };

        const syncNative = (showErrors = false) => {
            const date = parseDate(dateInput.value);
            const time = parseTime(timeInput.value);
            const nextValue = date && time
                ? `${date.year}-${date.month}-${date.day}T${time.hour}:${time.minute}`
                : "";
            if (native.value !== nextValue) {
                native.value = nextValue;
                native.dispatchEvent(new Event("input", { bubbles: true }));
                native.dispatchEvent(new Event("change", { bubbles: true }));
            }
            setValidity(showErrors);
        };

        dateInput.addEventListener("input", () => {
            dateInput.value = digitsMask(dateInput.value, [2, 2, 4], ".");
            syncNative(false);
        });
        timeInput.addEventListener("input", () => {
            timeInput.value = digitsMask(timeInput.value, [2, 2], ":");
            syncNative(false);
        });
        dateInput.addEventListener("blur", () => syncNative(true));
        timeInput.addEventListener("blur", () => syncNative(true));

        wrapper.append(dateLabel, timeLabel);
        if (native.dataset.allowServerNow === "true") {
            const nowButton = element("button", "defect-manual-now", "Системное время");
            nowButton.type = "button";
            nowButton.addEventListener("click", () => {
                const current = now();
                dateInput.value = new Intl.DateTimeFormat("ru-RU", {
                    timeZone: "Europe/Moscow",
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                }).format(current);
                timeInput.value = new Intl.DateTimeFormat("ru-RU", {
                    timeZone: "Europe/Moscow",
                    hour: "2-digit",
                    minute: "2-digit",
                    hourCycle: "h23",
                }).format(current);
                syncNative(false);
            });
            wrapper.appendChild(nowButton);
        }
        wrapper.appendChild(warning);

        native.classList.add("defect-datetime-native--repair3");
        native.insertAdjacentElement("afterend", wrapper);
        syncNative(false);
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(TREE_SELECTOR).forEach(initTreeSelect);
        const now = serverNowFactory();
        document.querySelectorAll(DATE_TIME_SELECTOR).forEach(
            (native, index) => initMaskedDateTime(native, index, now),
        );
    });
})();
