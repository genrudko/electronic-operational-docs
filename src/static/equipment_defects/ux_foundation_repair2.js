(() => {
    "use strict";

    const SORT_STORAGE_KEY = "eod-defect-sort";
    const VIEW_STORAGE_KEY = "eod-defect-registry-view";

    function storageGet(storage, key) {
        try {
            return storage.getItem(key);
        } catch (_error) {
            return null;
        }
    }

    function storageSet(storage, key, value) {
        try {
            storage.setItem(key, value);
        } catch (_error) {
            // The interface remains functional when browser storage is unavailable.
        }
    }

    function initPersistentSorting() {
        const select = document.querySelector("[data-defect-sort]");
        if (!select) return;

        const allowed = new Set([...select.options].map((option) => option.value));
        const persistentValue = storageGet(window.localStorage, SORT_STORAGE_KEY);
        const sessionValue = storageGet(window.sessionStorage, SORT_STORAGE_KEY);
        const initial = allowed.has(persistentValue)
            ? persistentValue
            : allowed.has(sessionValue)
                ? sessionValue
                : select.value;

        if (allowed.has(initial)) {
            select.value = initial;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            storageSet(window.localStorage, SORT_STORAGE_KEY, initial);
        }

        select.addEventListener("change", () => {
            storageSet(window.localStorage, SORT_STORAGE_KEY, select.value);
        });
    }

    function initPersistentRegistryView() {
        const switcher = document.querySelector("[data-defect-view-switch]");
        if (!switcher) return;

        const buttons = [...switcher.querySelectorAll("[data-defect-view]")];
        const allowed = new Set(buttons.map((button) => button.dataset.defectView));
        const persistentValue = storageGet(window.localStorage, VIEW_STORAGE_KEY);
        const sessionValue = storageGet(window.sessionStorage, VIEW_STORAGE_KEY);
        const initial = allowed.has(persistentValue)
            ? persistentValue
            : allowed.has(sessionValue)
                ? sessionValue
                : "work";

        const applyPersistent = (value) => {
            if (!allowed.has(value)) return;
            const button = buttons.find((candidate) => candidate.dataset.defectView === value);
            if (button && button.getAttribute("aria-pressed") !== "true") {
                button.click();
            }
            storageSet(window.localStorage, VIEW_STORAGE_KEY, value);
        };

        buttons.forEach((button) => {
            button.addEventListener("click", () => {
                storageSet(window.localStorage, VIEW_STORAGE_KEY, button.dataset.defectView);
            });
        });

        applyPersistent(initial);
    }

    function initDirectionAShell() {
        const toggle = document.querySelector("[data-defect-shell-toggle]");
        const sidebar = document.querySelector("[data-defect-shell-sidebar]");
        const scrim = document.querySelector("[data-defect-shell-scrim]");
        if (!toggle || !sidebar || !scrim) return;

        const setOpen = (open) => {
            sidebar.classList.toggle("is-open", open);
            scrim.hidden = !open;
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
            document.documentElement.classList.toggle("defect-shell-open", open);
        };

        toggle.addEventListener("click", () => {
            setOpen(!sidebar.classList.contains("is-open"));
        });
        scrim.addEventListener("click", () => setOpen(false));
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && sidebar.classList.contains("is-open")) {
                setOpen(false);
                toggle.focus();
            }
        });
        window.matchMedia("(min-width: 861px)").addEventListener("change", (event) => {
            if (event.matches) setOpen(false);
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        initPersistentSorting();
        initPersistentRegistryView();
        initDirectionAShell();
    });
})();
