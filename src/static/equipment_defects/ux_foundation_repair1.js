(() => {
    "use strict";

    const VIEW_STORAGE_KEY = "eod-defect-registry-view";

    function initRegistryViewSwitch() {
        const switcher = document.querySelector("[data-defect-view-switch]");
        if (!switcher) return;

        const buttons = [...switcher.querySelectorAll("[data-defect-view]")];
        const panels = [...document.querySelectorAll("[data-defect-view-panel]")];
        if (!buttons.length || !panels.length) return;

        const allowed = new Set(buttons.map((button) => button.dataset.defectView));
        const stored = window.sessionStorage.getItem(VIEW_STORAGE_KEY);
        const initial = allowed.has(stored) ? stored : "work";

        const apply = (view) => {
            if (!allowed.has(view)) return;

            buttons.forEach((button) => {
                const active = button.dataset.defectView === view;
                button.setAttribute("aria-pressed", active ? "true" : "false");
                button.classList.toggle("is-active", active);
            });

            panels.forEach((panel) => {
                const active = panel.dataset.defectViewPanel === view;
                panel.hidden = !active;
                panel.classList.toggle("is-active", active);
            });

            window.sessionStorage.setItem(VIEW_STORAGE_KEY, view);
        };

        buttons.forEach((button) => {
            button.addEventListener("click", () => apply(button.dataset.defectView));
        });

        apply(initial);
    }

    function initFilterDismissal() {
        const drawer = document.querySelector(".defect-filter-drawer");
        if (!drawer) return;

        document.addEventListener("click", (event) => {
            if (!drawer.open || drawer.contains(event.target)) return;
            drawer.open = false;
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && drawer.open) {
                drawer.open = false;
                drawer.querySelector("summary")?.focus();
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        initRegistryViewSwitch();
        initFilterDismissal();
    });
})();
