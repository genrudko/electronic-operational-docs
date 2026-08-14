(() => {
    const root = document.querySelector("[data-authority-page]");
    if (!root) return;

    const tabs = [...root.querySelectorAll("[data-authority-view]")];
    const panels = [...root.querySelectorAll("[data-authority-panel]")];
    const workspace = root.querySelector("[data-authority-workspace]");
    const toolbar = root.querySelector(".authority-toolbar");
    const search = root.querySelector("[data-authority-search]");
    const category = root.querySelector("[data-authority-category]");
    const group = root.querySelector("[data-authority-group]");
    const right = root.querySelector("[data-authority-right]");
    const noResults = root.querySelector("[data-authority-no-results]");
    const treeItems = [...root.querySelectorAll("[data-division-filter]")];
    const matrixRows = [...root.querySelectorAll("[data-matrix-row]")];
    const holderRows = [...root.querySelectorAll("[data-holder-row]")];
    const matrixSections = [...root.querySelectorAll("[data-division-section]")];
    const collapsers = [...root.querySelectorAll("[data-collapse-division]")];
    const expandAll = root.querySelector("[data-expand-all]");
    const supportedViews = tabs.map((item) => item.dataset.authorityView);
    const serverView = root.dataset.initialView || "matrix";
    let activeView = supportedViews.includes(serverView) ? serverView : "matrix";
    let selectedDivision = "";
    let conditionalOnly = false;
    const collapsed = new Set();

    root.querySelectorAll(".authority-abbreviation-legend").forEach((item) => item.remove());

    const normalize = (value) => (value || "")
        .toLocaleLowerCase("ru-RU")
        .replaceAll("ё", "е")
        .replace(/\s+/g, " ")
        .trim();

    const pathIncludes = (path, id) => !id || (path || "").split(" ").includes(id);
    const queryMatches = (row) => {
        const query = normalize(search?.value);
        return !query || normalize(row.dataset.search).includes(query);
    };

    const matrixMatch = (row) => queryMatches(row)
        && (!category?.value || row.dataset.category === category.value)
        && (!group?.value || row.dataset.group === group.value)
        && pathIncludes(row.dataset.divisionPath, selectedDivision);

    const holderMatch = (row) => matrixMatch(row)
        && (!right?.value || row.dataset.rightCode === right.value)
        && (!conditionalOnly || row.dataset.condition === "conditional");

    const syncExpandAllControl = () => {
        if (!expandAll) return;
        const allExpanded = collapsed.size === 0;
        expandAll.setAttribute("aria-expanded", String(allExpanded));
        const action = allExpanded ? "Свернуть всё" : "Развернуть всё";
        expandAll.setAttribute("aria-label", `${action} подразделения`);
        expandAll.title = action;
        const label = expandAll.querySelector("[data-expand-all-label]");
        if (label) label.textContent = action;
        expandAll.classList.toggle("is-collapsed", !allExpanded);
    };

    const applyFilters = () => {
        let visible = 0;
        if (activeView === "matrix") {
            matrixRows.forEach((row) => {
                const section = row.closest("[data-division-section]");
                const hiddenByCollapse = section
                    && collapsed.has(section.dataset.divisionSection);
                const show = matrixMatch(row) && !hiddenByCollapse;
                row.hidden = !show;
                if (show) visible += 1;
            });
            matrixSections.forEach((section) => {
                const rows = [...section.querySelectorAll("[data-matrix-row]")];
                section.hidden = !rows.some(matrixMatch)
                    || !pathIncludes(section.dataset.divisionPath, selectedDivision);
            });
        } else if (activeView === "holders") {
            holderRows.forEach((row) => {
                const show = holderMatch(row);
                row.hidden = !show;
                if (show) visible += 1;
            });
        } else {
            const panel = panels.find((item) => item.dataset.authorityPanel === activeView);
            const rows = panel ? [...panel.querySelectorAll("[data-authority-row]")] : [];
            rows.forEach((row) => {
                const show = queryMatches(row);
                row.hidden = !show;
                if (show) visible += 1;
            });
        }
        if (noResults) noResults.classList.toggle("is-visible", visible === 0);
    };

    const syncUrlView = (view) => {
        const url = new URL(window.location.href);
        url.searchParams.set("view", view);
        window.history.replaceState(null, "", url);
    };

    const activateView = (view, { syncUrl = false } = {}) => {
        activeView = supportedViews.includes(view) ? view : "matrix";
        tabs.forEach((tab) => tab.setAttribute(
            "aria-pressed",
            String(tab.dataset.authorityView === activeView),
        ));
        panels.forEach((panel) => {
            panel.hidden = panel.dataset.authorityPanel !== activeView;
        });
        if (workspace) workspace.hidden = !["matrix", "holders"].includes(activeView);
        if (toolbar) toolbar.dataset.activeView = activeView;
        root.querySelectorAll("[data-filter-for]").forEach((field) => {
            field.hidden = !field.dataset.filterFor.split(" ").includes(activeView);
        });
        if (syncUrl) syncUrlView(activeView);
        applyFilters();
    };

    tabs.forEach((tab) => tab.addEventListener("click", () => {
        conditionalOnly = false;
        activateView(tab.dataset.authorityView, { syncUrl: true });
    }));

    root.querySelectorAll("[data-summary-view]").forEach((button) => {
        button.addEventListener("click", () => {
            conditionalOnly = button.dataset.summaryCondition === "true";
            activateView(button.dataset.summaryView, { syncUrl: true });
        });
    });

    [search, category, group, right].forEach((field) => {
        field?.addEventListener(field === search ? "input" : "change", applyFilters);
    });

    treeItems.forEach((button) => button.addEventListener("click", () => {
        selectedDivision = button.dataset.divisionFilter || "";
        treeItems.forEach((item) => item.classList.toggle("is-active", item === button));
        collapsed.clear();
        collapsers.forEach((item) => item.setAttribute("aria-expanded", "true"));
        syncExpandAllControl();
        applyFilters();
    }));

    collapsers.forEach((button) => button.addEventListener("click", () => {
        const id = button.dataset.collapseDivision;
        if (collapsed.has(id)) collapsed.delete(id);
        else collapsed.add(id);
        button.setAttribute("aria-expanded", String(!collapsed.has(id)));
        syncExpandAllControl();
        applyFilters();
    }));

    expandAll?.addEventListener("click", () => {
        if (collapsed.size === 0) {
            collapsers.forEach((button) => {
                const id = button.dataset.collapseDivision;
                if (id) collapsed.add(id);
                button.setAttribute("aria-expanded", "false");
            });
        } else {
            collapsed.clear();
            collapsers.forEach((button) => button.setAttribute("aria-expanded", "true"));
        }
        syncExpandAllControl();
        applyFilters();
    });

    root.querySelectorAll("[data-focus-right]").forEach((button) => {
        button.addEventListener("click", () => {
            const code = button.dataset.focusRight;
            root.querySelectorAll(".is-focused").forEach((item) => item.classList.remove("is-focused"));
            button.closest("th")?.classList.add("is-focused");
            root.querySelectorAll(`[data-right-cell="${code}"]`).forEach((cell) => cell.classList.add("is-focused"));
            if (right) right.value = code;
        });
    });

    // Conditional rights use one bounded overlay controller. CSS still owns the
    // visual language; JS owns active-state exclusivity and viewport placement.
    const conditionOwners = [...root.querySelectorAll(
        ".authority-right-cell.is-conditional > a",
    )];
    let activeConditionOwner = null;
    let lastPointerType = "keyboard";
    let placementFrame = 0;

    const conditionPopover = (owner) => owner?.querySelector(".authority-condition-popover");

    const resetPopoverPlacement = (popover) => {
        if (!popover) return;
        popover.style.removeProperty("position");
        popover.style.removeProperty("inset");
        popover.style.removeProperty("top");
        popover.style.removeProperty("right");
        popover.style.removeProperty("bottom");
        popover.style.removeProperty("left");
        popover.style.removeProperty("transform");
        popover.style.removeProperty("max-width");
        popover.style.removeProperty("max-height");
        popover.style.removeProperty("overflow-y");
        popover.style.removeProperty("pointer-events");
        popover.style.removeProperty("visibility");
        popover.style.removeProperty("z-index");
    };

    const closeCondition = (owner = activeConditionOwner) => {
        if (!owner) return;
        const popover = conditionPopover(owner);
        if (popover) {
            popover.style.display = "none";
            resetPopoverPlacement(popover);
        }
        owner.setAttribute("aria-expanded", "false");
        owner.classList.remove("is-condition-active");
        if (activeConditionOwner === owner) activeConditionOwner = null;
    };

    const placeConditionPopover = (owner) => {
        const popover = conditionPopover(owner);
        if (!popover || activeConditionOwner !== owner) return;

        const viewportMargin = 16;
        const targetGap = 8;
        const target = owner.getBoundingClientRect();

        popover.style.position = "fixed";
        popover.style.inset = "auto";
        popover.style.transform = "none";
        popover.style.maxWidth = "min(24rem, calc(100vw - 2rem))";
        popover.style.maxHeight = "calc(100vh - 2rem)";
        popover.style.overflowY = "auto";
        popover.style.pointerEvents = "none";
        popover.style.zIndex = "1000";
        popover.style.visibility = "hidden";
        popover.style.display = "grid";

        const box = popover.getBoundingClientRect();
        let left = target.left + (target.width - box.width) / 2;
        left = Math.max(viewportMargin, Math.min(
            left,
            window.innerWidth - box.width - viewportMargin,
        ));

        let top = target.bottom + targetGap;
        if (top + box.height > window.innerHeight - viewportMargin) {
            top = target.top - targetGap - box.height;
        }
        top = Math.max(viewportMargin, Math.min(
            top,
            window.innerHeight - box.height - viewportMargin,
        ));

        popover.style.left = `${Math.round(left)}px`;
        popover.style.top = `${Math.round(top)}px`;
        popover.style.visibility = "visible";
    };

    const openCondition = (owner) => {
        const popover = conditionPopover(owner);
        if (!popover) return;
        if (activeConditionOwner && activeConditionOwner !== owner) {
            closeCondition(activeConditionOwner);
        }
        activeConditionOwner = owner;
        owner.setAttribute("aria-expanded", "true");
        owner.classList.add("is-condition-active");
        placeConditionPopover(owner);
    };

    const scheduleConditionPlacement = () => {
        if (!activeConditionOwner || placementFrame) return;
        placementFrame = window.requestAnimationFrame(() => {
            placementFrame = 0;
            if (activeConditionOwner) placeConditionPopover(activeConditionOwner);
        });
    };

    conditionOwners.forEach((owner, index) => {
        const popover = conditionPopover(owner);
        if (!popover) return;

        // Inline display ownership deliberately defeats independent :hover /
        // :focus-visible display rules, so only the controller can reveal one.
        popover.style.display = "none";
        if (!popover.id) popover.id = `authority-condition-${index + 1}`;
        owner.setAttribute("aria-describedby", popover.id);
        owner.setAttribute("aria-expanded", "false");

        owner.addEventListener("mouseenter", () => openCondition(owner));
        owner.addEventListener("mouseleave", () => {
            if (document.activeElement !== owner) closeCondition(owner);
        });
        owner.addEventListener("focus", () => {
            if (lastPointerType !== "touch" && lastPointerType !== "pen") {
                openCondition(owner);
            }
        });
        owner.addEventListener("blur", () => closeCondition(owner));
        owner.addEventListener("click", (event) => {
            if (lastPointerType !== "touch" && lastPointerType !== "pen") return;
            if (activeConditionOwner !== owner) {
                event.preventDefault();
                openCondition(owner);
                return;
            }
            // A second tap follows the existing link and leaves no sticky ghost.
            closeCondition(owner);
        });
    });

    root.addEventListener("pointerdown", (event) => {
        lastPointerType = event.pointerType || "mouse";
        if (activeConditionOwner && !activeConditionOwner.contains(event.target)) {
            closeCondition(activeConditionOwner);
        }
    }, true);

    root.addEventListener("keydown", (event) => {
        lastPointerType = "keyboard";
        if (event.key === "Escape" && activeConditionOwner) {
            const owner = activeConditionOwner;
            closeCondition(owner);
            owner.focus({ preventScroll: true });
        }
    }, true);

    window.addEventListener("resize", scheduleConditionPlacement);
    window.addEventListener("scroll", scheduleConditionPlacement, true);

    // The server owns the initial panel, selected tab and scoped contact data.
    // JavaScript begins from that exact state and only enhances later interaction.
    syncExpandAllControl();
    if (toolbar) toolbar.dataset.activeView = activeView;
    applyFilters();
})();
