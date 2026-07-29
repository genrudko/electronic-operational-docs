(() => {
    "use strict";

    const shell = document.querySelector("[data-direction-a-shell]");
    if (!shell) {
        return;
    }

    const sidebar = shell.querySelector("[data-direction-a-sidebar]");
    const scrim = shell.querySelector("[data-direction-a-scrim]");
    const toggle = shell.querySelector("[data-direction-a-toggle]");

    function setNavigationOpen(open) {
        document.body.classList.toggle("da-nav-open", open);
        if (scrim) {
            scrim.hidden = !open;
        }
        if (toggle) {
            toggle.setAttribute("aria-expanded", String(open));
        }
        if (sidebar) {
            sidebar.setAttribute("aria-hidden", open ? "false" : "true");
        }
    }

    toggle?.addEventListener("click", () => {
        setNavigationOpen(!document.body.classList.contains("da-nav-open"));
    });
    scrim?.addEventListener("click", () => setNavigationOpen(false));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && document.body.classList.contains("da-nav-open")) {
            setNavigationOpen(false);
            toggle?.focus();
        }
    });
    window.addEventListener("resize", () => {
        if (window.matchMedia("(min-width: 981px)").matches) {
            setNavigationOpen(false);
            sidebar?.removeAttribute("aria-hidden");
        }
    });

    document.body.classList.add("da-active");
})();
