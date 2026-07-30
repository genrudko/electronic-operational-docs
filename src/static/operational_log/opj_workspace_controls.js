(() => {
    "use strict";

    const workspace = document.querySelector(
        '[data-draft-workspace][data-opj-presentation-mode="single-spread"]',
    );
    if (!workspace) {
        return;
    }

    const secondaryPage = workspace.querySelector('[data-page-shell="right"]');
    const drawer = workspace.querySelector("[data-view-drawer]");
    const drawerTriggers = Array.from(
        workspace.querySelectorAll("[data-open-view-drawer]"),
    );
    let returnFocus = null;

    function syncPresentationState() {
        if (!secondaryPage) {
            return;
        }
        const spread = workspace.dataset.viewMode === "spread";
        secondaryPage.hidden = !spread;
        secondaryPage.setAttribute("aria-hidden", String(!spread));
    }

    function syncDrawerState() {
        if (!drawer) {
            return;
        }
        const open = !drawer.hidden;
        drawerTriggers.forEach((trigger) => {
            trigger.setAttribute("aria-expanded", String(open));
        });
        drawer.setAttribute("aria-hidden", String(!open));
        if (open) {
            returnFocus = document.activeElement;
            drawer.querySelector("[data-close-view-drawer]")?.focus({
                preventScroll: true,
            });
        } else if (returnFocus?.isConnected) {
            returnFocus.focus({preventScroll: true});
            returnFocus = null;
        }
    }

    if (drawer) {
        if (!drawer.id) {
            drawer.id = "opj-workspace-settings";
        }
        drawerTriggers.forEach((trigger) => {
            trigger.setAttribute("aria-controls", drawer.id);
            trigger.setAttribute("aria-haspopup", "dialog");
        });

        new MutationObserver(syncDrawerState).observe(drawer, {
            attributes: true,
            attributeFilter: ["hidden"],
        });

        document.addEventListener("pointerdown", (event) => {
            if (
                drawer.hidden
                || drawer.contains(event.target)
                || drawerTriggers.some((trigger) => trigger.contains(event.target))
            ) {
                return;
            }
            workspace.querySelector("[data-close-view-drawer]")?.click();
        });
    }

    new MutationObserver(syncPresentationState).observe(workspace, {
        attributes: true,
        attributeFilter: ["data-view-mode"],
    });

    syncPresentationState();
    syncDrawerState();
})();
