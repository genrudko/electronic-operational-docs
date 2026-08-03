(() => {
    "use strict";

    if (window.__EOD_OPJ_ACTION_REPAIR_V2__) return;
    window.__EOD_OPJ_ACTION_REPAIR_V2__ = true;

    let activeMenu = null;
    let activeTrigger = null;

    function closeMenu() {
        if (activeMenu) {
            activeMenu.hidden = true;
            activeMenu.classList.remove("is-floating", "opj-action-portal");
            activeMenu.style.removeProperty("position");
            activeMenu.style.removeProperty("left");
            activeMenu.style.removeProperty("top");
            activeMenu.style.removeProperty("width");
            activeMenu.style.removeProperty("z-index");
        }
        if (activeTrigger) activeTrigger.setAttribute("aria-expanded", "false");
        activeMenu = null;
        activeTrigger = null;
    }

    function placeMenu(trigger, menu) {
        const rect = trigger.getBoundingClientRect();
        const margin = 12;
        const width = Math.min(310, window.innerWidth - margin * 2);
        menu.hidden = false;
        menu.classList.add("is-floating", "opj-action-portal");
        menu.style.position = "fixed";
        menu.style.width = `${width}px`;
        menu.style.zIndex = "500";
        menu.style.visibility = "hidden";
        const measured = menu.getBoundingClientRect();
        let left = rect.right - width;
        left = Math.max(margin, Math.min(left, window.innerWidth - width - margin));
        let top = rect.bottom + 6;
        if (top + measured.height > window.innerHeight - margin) {
            top = Math.max(margin, rect.top - measured.height - 6);
        }
        menu.style.left = `${Math.round(left)}px`;
        menu.style.top = `${Math.round(top)}px`;
        menu.style.visibility = "";
    }

    function toggleMenu(trigger) {
        const owner = trigger.closest("[data-entry-actions]");
        const menu = owner?.querySelector("[data-entry-actions-menu]");
        if (!menu) return false;
        if (activeTrigger === trigger && !menu.hidden) {
            closeMenu();
            return true;
        }
        closeMenu();
        activeTrigger = trigger;
        activeMenu = menu;
        trigger.setAttribute("aria-expanded", "true");
        placeMenu(trigger, menu);
        return true;
    }

    document.addEventListener("click", (event) => {
        const trigger = event.target.closest?.("[data-entry-actions-toggle]");
        if (trigger) {
            event.preventDefault();
            event.stopImmediatePropagation();
            toggleMenu(trigger);
            return;
        }

        if (activeMenu && activeMenu.contains(event.target)) {
            const actionable = event.target.closest("button, a[href]");
            if (actionable) {
                // Let the existing lifecycle handler process correction,
                // cancellation and history commands. Links remain native.
                window.setTimeout(closeMenu, 0);
            }
            return;
        }

        if (activeMenu) closeMenu();
    }, true);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && activeMenu) {
            event.preventDefault();
            const trigger = activeTrigger;
            closeMenu();
            trigger?.focus({preventScroll: true});
        }
    });

    window.addEventListener("resize", closeMenu);
    document.addEventListener("scroll", closeMenu, true);
})();
