(() => {
    const root = document.querySelector("[data-authority-page]");
    if (!root) return;

    const tabs = [...root.querySelectorAll("[data-authority-view]")];
    const panels = [...root.querySelectorAll("[data-authority-panel]")];
    const workspace = root.querySelector("[data-authority-workspace]");
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
    const supportedViews = tabs.map((item) => item.dataset.authorityView);
    let activeView = "matrix";
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

    const activateView = (view) => {
        activeView = supportedViews.includes(view) ? view : "matrix";
        tabs.forEach((tab) => tab.setAttribute(
            "aria-pressed",
            String(tab.dataset.authorityView === activeView),
        ));
        panels.forEach((panel) => {
            panel.hidden = panel.dataset.authorityPanel !== activeView;
        });
        if (workspace) workspace.hidden = !["matrix", "holders"].includes(activeView);
        root.querySelectorAll("[data-filter-for]").forEach((field) => {
            field.hidden = !field.dataset.filterFor.split(" ").includes(activeView);
        });
        history.replaceState(null, "", `#${activeView}`);
        applyFilters();
    };

    tabs.forEach((tab) => tab.addEventListener("click", () => {
        conditionalOnly = false;
        activateView(tab.dataset.authorityView);
    }));

    root.querySelectorAll("[data-summary-view]").forEach((button) => {
        button.addEventListener("click", () => {
            conditionalOnly = button.dataset.summaryCondition === "true";
            activateView(button.dataset.summaryView);
        });
    });

    [search, category, group, right].forEach((field) => {
        field?.addEventListener(field === search ? "input" : "change", applyFilters);
    });

    treeItems.forEach((button) => button.addEventListener("click", () => {
        selectedDivision = button.dataset.divisionFilter || "";
        treeItems.forEach((item) => item.classList.toggle("is-active", item === button));
        collapsed.clear();
        collapsers.forEach((item) => {
            item.setAttribute("aria-expanded", "true");
            item.textContent = "▾";
        });
        applyFilters();
    }));

    collapsers.forEach((button) => button.addEventListener("click", () => {
        const id = button.dataset.collapseDivision;
        if (collapsed.has(id)) collapsed.delete(id);
        else collapsed.add(id);
        const expanded = !collapsed.has(id);
        button.setAttribute("aria-expanded", String(expanded));
        button.textContent = expanded ? "▾" : "▸";
        applyFilters();
    }));

    root.querySelector("[data-expand-all]")?.addEventListener("click", () => {
        collapsed.clear();
        collapsers.forEach((button) => {
            button.setAttribute("aria-expanded", "true");
            button.textContent = "▾";
        });
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

    const initial = window.location.hash.slice(1);
    activateView(supportedViews.includes(initial) ? initial : "matrix");
})();
