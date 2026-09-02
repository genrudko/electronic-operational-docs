(() => {
    "use strict";

    const shell = document.querySelector("[data-direction-a-shell]");
    const mobileQuery = window.matchMedia("(max-width: 980px)");

    if (shell) {
        const sidebar = shell.querySelector("[data-direction-a-sidebar]");
        const scrim = shell.querySelector("[data-direction-a-scrim]");
        const toggle = shell.querySelector("[data-direction-a-toggle]");

        function setNavigationOpen(open, { restoreFocus = false } = {}) {
            const mobile = mobileQuery.matches;
            const shouldOpen = mobile && open;
            document.body.classList.toggle("da-nav-open", shouldOpen);
            if (scrim) {
                scrim.hidden = !shouldOpen;
            }
            if (toggle) {
                toggle.setAttribute("aria-expanded", String(shouldOpen));
            }
            if (sidebar) {
                if (mobile) {
                    sidebar.setAttribute("aria-hidden", String(!shouldOpen));
                } else {
                    sidebar.removeAttribute("aria-hidden");
                }
            }
            if (restoreFocus) {
                toggle?.focus();
            }
        }

        toggle?.addEventListener("click", () => {
            setNavigationOpen(!document.body.classList.contains("da-nav-open"));
        });
        scrim?.addEventListener("click", () => setNavigationOpen(false, { restoreFocus: true }));
        mobileQuery.addEventListener?.("change", () => setNavigationOpen(false));
        setNavigationOpen(false);

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && document.body.classList.contains("da-nav-open")) {
                setNavigationOpen(false, { restoreFocus: true });
            }
        });
    }

    function closeMenu(container, { restoreFocus = false } = {}) {
        const trigger = container.querySelector("[data-ux-menu-trigger]");
        const panel = container.querySelector("[data-ux-menu-panel]");
        if (!panel) {
            return;
        }
        panel.hidden = true;
        trigger?.setAttribute("aria-expanded", "false");
        if (restoreFocus) {
            trigger?.focus();
        }
    }

    document.querySelectorAll("[data-ux-menu]").forEach((container) => {
        const trigger = container.querySelector("[data-ux-menu-trigger]");
        const panel = container.querySelector("[data-ux-menu-panel]");
        if (!trigger || !panel) {
            return;
        }
        panel.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
        trigger.addEventListener("click", () => {
            const opening = panel.hidden;
            document.querySelectorAll("[data-ux-menu]").forEach((other) => {
                if (other !== container) {
                    closeMenu(other);
                }
            });
            panel.hidden = !opening;
            trigger.setAttribute("aria-expanded", String(opening));
            if (opening) {
                panel.querySelector("a, button, [tabindex]:not([tabindex='-1'])")?.focus();
            }
        });
    });

    document.addEventListener("pointerdown", (event) => {
        document.querySelectorAll("[data-ux-menu]").forEach((container) => {
            if (!container.contains(event.target)) {
                closeMenu(container);
            }
        });
    });

    document.querySelectorAll("[data-ux-tabs]").forEach((tablist) => {
        const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'));
        if (!tabs.length) {
            return;
        }
        tablist.addEventListener("keydown", (event) => {
            if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
                return;
            }
            const current = tabs.indexOf(document.activeElement);
            if (current < 0) {
                return;
            }
            event.preventDefault();
            let next = current;
            if (event.key === "Home") {
                next = 0;
            } else if (event.key === "End") {
                next = tabs.length - 1;
            } else if (event.key === "ArrowRight") {
                next = (current + 1) % tabs.length;
            } else {
                next = (current - 1 + tabs.length) % tabs.length;
            }
            tabs[next].focus();
        });
    });

    const focusOrigins = new WeakMap();

    document.querySelectorAll("[data-ux-dialog-open]").forEach((trigger) => {
        trigger.addEventListener("click", () => {
            const selector = trigger.getAttribute("data-ux-dialog-open");
            const dialog = selector ? document.querySelector(selector) : null;
            if (!(dialog instanceof HTMLDialogElement)) {
                return;
            }
            focusOrigins.set(dialog, trigger);
            dialog.showModal();
            dialog.querySelector("[autofocus], button, a, input, select, textarea, [tabindex]:not([tabindex='-1'])")?.focus();
        });
    });

    document.querySelectorAll("[data-ux-dialog-close]").forEach((trigger) => {
        trigger.addEventListener("click", () => {
            const dialog = trigger.closest("dialog");
            if (dialog instanceof HTMLDialogElement) {
                dialog.close();
            }
        });
    });

    document.querySelectorAll("dialog").forEach((dialog) => {
        dialog.addEventListener("close", () => focusOrigins.get(dialog)?.focus());
    });

    function setDrawer(drawer, open, trigger = null) {
        if (!drawer) {
            return;
        }
        drawer.hidden = !open;
        drawer.setAttribute("aria-hidden", String(!open));
        if (open && trigger) {
            focusOrigins.set(drawer, trigger);
            drawer.querySelector("[autofocus], button, a, input, select, textarea, [tabindex]:not([tabindex='-1'])")?.focus();
        } else if (!open) {
            focusOrigins.get(drawer)?.focus();
        }
    }

    document.querySelectorAll("[data-ux-drawer-open]").forEach((trigger) => {
        trigger.addEventListener("click", () => {
            const selector = trigger.getAttribute("data-ux-drawer-open");
            setDrawer(selector ? document.querySelector(selector) : null, true, trigger);
        });
    });

    document.querySelectorAll("[data-ux-drawer-close]").forEach((trigger) => {
        trigger.addEventListener("click", () => setDrawer(trigger.closest("[data-ux-drawer]"), false));
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }
        document.querySelectorAll("[data-ux-menu]").forEach((container) => closeMenu(container, { restoreFocus: true }));
        const openDrawer = document.querySelector("[data-ux-drawer]:not([hidden])");
        if (openDrawer) {
            setDrawer(openDrawer, false);
        }
    });

    document.body.classList.add("da-active");
})();
