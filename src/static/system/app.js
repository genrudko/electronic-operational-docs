(() => {
    "use strict";

    const selector = "details.help-tip";
    const tips = Array.from(document.querySelectorAll(selector));
    let activeTip = null;

    function summaryFor(tip) {
        return tip.querySelector(":scope > summary");
    }

    function panelFor(tip) {
        return tip.querySelector(":scope > div");
    }

    function setExpanded(tip, expanded) {
        const summary = summaryFor(tip);
        if (summary) {
            summary.setAttribute("aria-expanded", expanded ? "true" : "false");
        }
    }

    function closeTip(tip, restoreFocus = false) {
        if (!tip) {
            return;
        }
        const summary = summaryFor(tip);
        tip.open = false;
        setExpanded(tip, false);
        if (activeTip === tip) {
            activeTip = null;
        }
        if (restoreFocus && summary) {
            summary.focus();
        }
    }

    function closeOtherTips(current) {
        for (const tip of tips) {
            if (tip !== current && tip.open) {
                closeTip(tip);
            }
        }
    }

    function positionTip(tip) {
        if (!tip || !tip.open) {
            return;
        }
        const summary = summaryFor(tip);
        const panel = panelFor(tip);
        if (!summary || !panel) {
            return;
        }

        panel.style.removeProperty("left");
        panel.style.removeProperty("right");
        panel.style.removeProperty("top");
        panel.style.removeProperty("bottom");
        panel.style.removeProperty("width");
        tip.dataset.placement = "";

        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        if (viewportWidth <= 760) {
            tip.dataset.placement = "bottom-sheet";
            return;
        }

        const margin = 16;
        const gap = 12;
        const preferredWidth = Math.min(360, viewportWidth - margin * 2);
        panel.style.width = `${preferredWidth}px`;

        const anchor = summary.getBoundingClientRect();
        const panelRect = panel.getBoundingClientRect();
        let left = anchor.right + gap;
        let placement = "right";

        if (left + panelRect.width > viewportWidth - margin) {
            left = anchor.left - panelRect.width - gap;
            placement = "left";
        }
        if (left < margin) {
            left = Math.min(
                Math.max(anchor.left, margin),
                viewportWidth - panelRect.width - margin,
            );
            placement = "below";
        }

        let top = anchor.top - 10;
        if (top + panelRect.height > viewportHeight - margin) {
            top = viewportHeight - panelRect.height - margin;
        }
        if (top < margin) {
            top = margin;
        }

        panel.style.left = `${Math.round(left)}px`;
        panel.style.top = `${Math.round(top)}px`;
        tip.dataset.placement = placement;
    }

    tips.forEach((tip, index) => {
        const summary = summaryFor(tip);
        const panel = panelFor(tip);
        if (!summary || !panel) {
            return;
        }

        const panelId = panel.id || `context-help-${index + 1}`;
        panel.id = panelId;
        panel.setAttribute("role", "tooltip");
        summary.setAttribute("aria-controls", panelId);
        summary.setAttribute("aria-haspopup", "true");
        setExpanded(tip, tip.open);

        tip.addEventListener("toggle", () => {
            if (tip.open) {
                closeOtherTips(tip);
                activeTip = tip;
                setExpanded(tip, true);
                window.requestAnimationFrame(() => positionTip(tip));
            } else {
                setExpanded(tip, false);
                if (activeTip === tip) {
                    activeTip = null;
                }
            }
        });
    });

    document.addEventListener("pointerdown", (event) => {
        if (activeTip && !activeTip.contains(event.target)) {
            closeTip(activeTip);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && activeTip) {
            event.preventDefault();
            closeTip(activeTip, true);
        }
    });

    window.addEventListener("resize", () => positionTip(activeTip));
    window.addEventListener(
        "scroll",
        () => positionTip(activeTip),
        { passive: true },
    );
})();

(() => {
    "use strict";

    const root = document.querySelector("[data-equipment-selector]");
    if (!root) {
        return;
    }

    const endpoint = root.dataset.endpoint;
    const dialog = root.querySelector("[data-equipment-dialog]");
    const openButton = root.querySelector("[data-equipment-selector-open]");
    const closeButtons = root.querySelectorAll("[data-equipment-dialog-close]");
    const applyButton = root.querySelector("[data-equipment-apply]");
    const clearButton = root.querySelector("[data-equipment-clear]");
    const hiddenContainer = root.querySelector("[data-equipment-hidden-inputs]");
    const selectedList = root.querySelector("[data-equipment-selected-list]");
    const dialogSelected = root.querySelector("[data-equipment-dialog-selected]");
    const selectedCount = root.querySelector("[data-equipment-selected-count]");
    const dialogSelectedCount = root.querySelector(
        "[data-equipment-dialog-selected-count]",
    );
    const searchInput = root.querySelector("[data-equipment-search]");
    const siteSelect = root.querySelector("[data-equipment-site]");
    const typeSelect = root.querySelector("[data-equipment-type]");
    const categoryList = root.querySelector("[data-equipment-categories]");
    const results = root.querySelector("[data-equipment-results]");
    const totalLabel = root.querySelector("[data-equipment-result-total]");
    const loadingLabel = root.querySelector("[data-equipment-loading]");
    const loadMoreButton = root.querySelector("[data-equipment-load-more]");
    const initialElement = document.getElementById("equipment-selector-initial");

    const selected = new Map();
    let currentPage = 1;
    let selectedCategory = "";
    let filtersLoaded = false;
    let searchTimer = null;
    let requestSerial = 0;

    function parseInitial() {
        if (!initialElement) {
            return;
        }
        try {
            const rows = JSON.parse(initialElement.textContent);
            for (const row of rows) {
                selected.set(String(row.id), row);
            }
        } catch (error) {
            console.error("Не удалось прочитать исходный выбор оборудования.", error);
        }
    }

    function createHiddenInput(id) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "equipment_assets";
        input.value = id;
        return input;
    }

    function syncHiddenInputs() {
        hiddenContainer.replaceChildren();
        for (const id of selected.keys()) {
            hiddenContainer.append(createHiddenInput(id));
        }
    }

    function selectionCard(item, compact = false) {
        const card = document.createElement("article");
        card.className = compact
            ? "equipment-picked-card compact"
            : "equipment-picked-card";

        const body = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = item.display_name;
        const meta = document.createElement("small");
        meta.textContent = `${item.code} · ${item.type_name} · ${item.site_name}`;
        body.append(title, meta);

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "equipment-remove-button";
        remove.textContent = "Убрать";
        remove.setAttribute(
            "aria-label",
            `Убрать оборудование ${item.display_name}`,
        );
        remove.addEventListener("click", () => {
            selected.delete(String(item.id));
            renderSelection();
            renderResultsSelectionState();
        });

        card.append(body, remove);
        return card;
    }

    function renderSelection() {
        selectedList.replaceChildren();
        dialogSelected.replaceChildren();

        if (!selected.size) {
            const empty = document.createElement("p");
            empty.className = "muted";
            empty.textContent = "Оборудование пока не выбрано.";
            selectedList.append(empty);

            const dialogEmpty = empty.cloneNode(true);
            dialogSelected.append(dialogEmpty);
        } else {
            for (const item of selected.values()) {
                selectedList.append(selectionCard(item));
                dialogSelected.append(selectionCard(item, true));
            }
        }

        selectedCount.textContent = String(selected.size);
        dialogSelectedCount.textContent = String(selected.size);
        syncHiddenInputs();
    }

    function toggleSelection(item) {
        const key = String(item.id);
        if (selected.has(key)) {
            selected.delete(key);
        } else {
            selected.set(key, item);
        }
        renderSelection();
        renderResultsSelectionState();
    }

    function resultCard(item) {
        const card = document.createElement("article");
        card.className = "equipment-result-card";
        card.dataset.equipmentId = String(item.id);

        const content = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = item.display_name;
        const technical = document.createElement("span");
        technical.textContent = item.technical_name;
        const meta = document.createElement("small");
        meta.textContent = `${item.code} · ${item.type_name} · ${item.site_name}`;
        const path = document.createElement("small");
        path.className = "equipment-result-path";
        path.textContent = item.hierarchy_path;
        content.append(title, technical, meta, path);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "button secondary equipment-result-toggle";
        button.addEventListener("click", () => toggleSelection(item));

        card.append(content, button);
        return card;
    }

    function renderResultsSelectionState() {
        for (const card of results.querySelectorAll("[data-equipment-id]")) {
            const button = card.querySelector(".equipment-result-toggle");
            const isSelected = selected.has(card.dataset.equipmentId);
            card.classList.toggle("selected", isSelected);
            button.textContent = isSelected ? "Убрать" : "Выбрать";
            button.setAttribute("aria-pressed", isSelected ? "true" : "false");
        }
    }

    function fillSelect(select, rows, allLabel, valueKey = "code") {
        const current = select.value;
        select.replaceChildren();
        const all = document.createElement("option");
        all.value = "";
        all.textContent = allLabel;
        select.append(all);
        for (const row of rows) {
            const option = document.createElement("option");
            option.value = row[valueKey];
            option.textContent = row.name;
            select.append(option);
        }
        if ([...select.options].some((option) => option.value === current)) {
            select.value = current;
        }
    }

    function renderCategories(rows) {
        categoryList.replaceChildren();

        const all = document.createElement("button");
        all.type = "button";
        all.className = "equipment-category-button";
        all.dataset.category = "";
        all.textContent = "Все категории";
        categoryList.append(all);

        for (const row of rows) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "equipment-category-button";
            button.dataset.category = row.code;
            button.textContent = row.name;
            categoryList.append(button);
        }

        for (const button of categoryList.querySelectorAll("button")) {
            const active = button.dataset.category === selectedCategory;
            button.classList.toggle("active", active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
            button.addEventListener("click", () => {
                selectedCategory = button.dataset.category;
                for (const item of categoryList.querySelectorAll("button")) {
                    const selectedNow = item === button;
                    item.classList.toggle("active", selectedNow);
                    item.setAttribute(
                        "aria-pressed",
                        selectedNow ? "true" : "false",
                    );
                }
                filterTypes();
                loadPage(true);
            });
        }
    }

    let allTypes = [];

    function filterTypes() {
        const rows = selectedCategory
            ? allTypes.filter((row) => row.category === selectedCategory)
            : allTypes;
        fillSelect(typeSelect, rows, "Все виды");
    }

    function loadFilters(filters) {
        if (filtersLoaded) {
            return;
        }
        fillSelect(siteSelect, filters.sites, "Все энергообъекты");
        allTypes = filters.types;
        renderCategories(filters.categories);
        filterTypes();
        filtersLoaded = true;
    }

    async function loadPage(reset) {
        if (reset) {
            currentPage = 1;
        }

        const serial = ++requestSerial;
        loadingLabel.hidden = false;
        loadMoreButton.hidden = true;

        const parameters = new URLSearchParams({
            q: searchInput.value.trim(),
            site: siteSelect.value,
            category: selectedCategory,
            type: typeSelect.value,
            page: String(currentPage),
        });

        try {
            const response = await fetch(`${endpoint}?${parameters}`, {
                headers: {"X-Requested-With": "XMLHttpRequest"},
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const payload = await response.json();
            if (serial !== requestSerial) {
                return;
            }

            loadFilters(payload.filters);
            if (reset) {
                results.replaceChildren();
            }
            for (const item of payload.items) {
                results.append(resultCard(item));
            }
            if (!payload.items.length && reset) {
                const empty = document.createElement("p");
                empty.className = "muted";
                empty.textContent = "По заданным условиям оборудование не найдено.";
                results.append(empty);
            }
            totalLabel.textContent = `Найдено: ${payload.total}`;
            loadMoreButton.hidden = !payload.has_more;
            renderResultsSelectionState();
        } catch (error) {
            if (serial === requestSerial) {
                results.replaceChildren();
                const failure = document.createElement("p");
                failure.className = "field-error";
                failure.textContent =
                    "Не удалось загрузить оборудование. Повторите попытку.";
                results.append(failure);
                console.error(error);
            }
        } finally {
            if (serial === requestSerial) {
                loadingLabel.hidden = true;
            }
        }
    }

    function openDialog() {
        if (typeof dialog.showModal === "function") {
            dialog.showModal();
        } else {
            dialog.setAttribute("open", "");
        }
        loadPage(true);
        window.requestAnimationFrame(() => searchInput.focus());
    }

    function closeDialog() {
        if (typeof dialog.close === "function") {
            dialog.close();
        } else {
            dialog.removeAttribute("open");
        }
    }

    parseInitial();
    renderSelection();

    openButton.addEventListener("click", openDialog);
    closeButtons.forEach((button) => {
        button.addEventListener("click", closeDialog);
    });
    applyButton.addEventListener("click", closeDialog);
    clearButton.addEventListener("click", () => {
        selected.clear();
        renderSelection();
        renderResultsSelectionState();
    });
    loadMoreButton.addEventListener("click", () => {
        currentPage += 1;
        loadPage(false);
    });
    siteSelect.addEventListener("change", () => loadPage(true));
    typeSelect.addEventListener("change", () => loadPage(true));
    searchInput.addEventListener("input", () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => loadPage(true), 280);
    });
})();(() => {
    "use strict";

    const toggle = document.querySelector("[data-nav-toggle]");
    const navigation = document.querySelector("[data-main-navigation]");
    if (toggle && navigation) {
        toggle.addEventListener("click", () => {
            const open = navigation.classList.toggle("open");
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
        });
    }

    const menus = Array.from(document.querySelectorAll("details.nav-menu"));
    for (const menu of menus) {
        menu.addEventListener("toggle", () => {
            if (!menu.open) {
                return;
            }
            for (const other of menus) {
                if (other !== menu) {
                    other.open = false;
                }
            }
        });
    }
    document.addEventListener("pointerdown", (event) => {
        for (const menu of menus) {
            if (menu.open && !menu.contains(event.target)) {
                menu.open = false;
            }
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            for (const menu of menus) {
                menu.open = false;
            }
        }
    });
})();
