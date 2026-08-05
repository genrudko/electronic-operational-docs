(() => {
    "use strict";

    const workspace = document.querySelector("[data-draft-workspace]");
    if (!workspace) {
        return;
    }

    /* Compatibility only: older cached templates may still carry the guard
     * class contract. Reveal synchronously; never wait for DOM mutations,
     * animation frames or a fallback timer. */
    workspace.dataset.opjFirstPaintGuard = "disabled";
    workspace.classList.add("is-opj-first-paint-ready");
})();