(() => {
    "use strict";

    let confirmedNavigation = false;

    window.EODOPJNavigation = Object.freeze({
        allowOnce() {
            confirmedNavigation = true;
        },
    });

    window.addEventListener("beforeunload", (event) => {
        if (!confirmedNavigation) return;
        event.stopImmediatePropagation();
    }, true);
})();
