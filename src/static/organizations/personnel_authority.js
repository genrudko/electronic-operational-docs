(() => {
    const root = document.querySelector("[data-authority-page]");
    if (!root) {
        return;
    }

    const tabs = [...root.querySelectorAll("[data-authority-view]")];
    const panels = [...root.querySelectorAll("[data-authority-panel]")];
    const searchInput = root.querySelector("[data-authority-search]");
    const stateSelect = root.querySelector("[data-authority-state]");
    const emptyMessage = root.querySelector("[data-authority-no-results]");

    root.dataset.authorityEnhanced = "true";

    const normalized = (value) => (value || "")
        .toLocaleLowerCase("ru-RU")
        .replaceAll("ё", "е")
        .replace(/\s+/g, " ")
        .trim();

    const activeViewFromHash = () => {
        const value = window.location.hash.replace("#", "");
        return panels.some((panel) => panel.dataset.authorityPanel === value)
            ? value
            : "rights";
    };

    const applyFilters = () => {
        const activePanel = panels.find((panel) => !panel.hidden);
        if (!activePanel) {
            return;
        }

        const query = normalized(searchInput?.value);
        const state = stateSelect?.value || "";
        const rows = [...activePanel.querySelectorAll("[data-authority-row]")];
        let visibleCount = 0;

        rows.forEach((row) => {
            const matchesQuery = !query || normalized(row.dataset.search).includes(query);
            const matchesState = !state || row.dataset.state === state;
            const visible = matchesQuery && matchesState;
            row.hidden = !visible;
            if (visible) {
                visibleCount += 1;
            }
        });

        if (emptyMessage) {
            emptyMessage.classList.toggle("is-visible", rows.length > 0 && visibleCount === 0);
        }
    };

    const activateView = (view, updateHash = true) => {
        tabs.forEach((tab) => {
            tab.setAttribute("aria-pressed", String(tab.dataset.authorityView === view));
        });
        panels.forEach((panel) => {
            panel.hidden = panel.dataset.authorityPanel !== view;
        });

        if (stateSelect) {
            [...stateSelect.options].forEach((option) => {
                const views = (option.dataset.views || "rights external checks").split(" ");
                option.hidden = !views.includes(view);
            });
            if (stateSelect.selectedOptions[0]?.hidden) {
                stateSelect.value = "";
            }
        }

        if (updateHash) {
            history.replaceState(null, "", `#${view}`);
        }
        applyFilters();
    };

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => activateView(tab.dataset.authorityView));
    });
    searchInput?.addEventListener("input", applyFilters);
    stateSelect?.addEventListener("change", applyFilters);
    window.addEventListener("hashchange", () => activateView(activeViewFromHash(), false));

    activateView(activeViewFromHash(), false);
})();
