(() => {
    "use strict";

    const workspace = document.querySelector("[data-draft-workspace]");
    if (!workspace || workspace.dataset.opjFirstPaintGuard === "true") {
        return;
    }
    workspace.dataset.opjFirstPaintGuard = "true";

    let observer = null;
    let fallbackTimer = null;

    function finalPagesAreMaterialized() {
        return Array.from(workspace.querySelectorAll("[data-page-body]"))
            .some((body) => body.childElementCount > 0);
    }

    function reveal() {
        if (!finalPagesAreMaterialized()) {
            return false;
        }
        workspace.classList.add("is-opj-first-paint-ready");
        observer?.disconnect();
        if (fallbackTimer) {
            window.clearTimeout(fallbackTimer);
            fallbackTimer = null;
        }
        return true;
    }

    observer = new MutationObserver(reveal);
    observer.observe(workspace, {childList: true, subtree: true});

    if (!reveal()) {
        window.requestAnimationFrame(reveal);
    }

    fallbackTimer = window.setTimeout(() => {
        workspace.classList.add("is-opj-first-paint-ready");
        observer?.disconnect();
    }, 2500);
})();