(() => {
    "use strict";

    document.addEventListener("click", (event) => {
        const link = event.target.closest?.(
            '[data-entry-actions-menu] a[role="menuitem"]',
        );
        if (!link) return;

        window.EODOPJNavigation?.allowOnce();
        const menu = link.closest("[data-entry-actions-menu]");
        if (menu) {
            menu.hidden = true;
            menu.classList.remove("is-floating");
        }
        document.querySelectorAll("[data-entry-actions-toggle]").forEach(
            (button) => button.setAttribute("aria-expanded", "false"),
        );
    }, true);
})();
