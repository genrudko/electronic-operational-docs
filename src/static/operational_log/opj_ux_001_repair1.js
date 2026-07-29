(() => {
    "use strict";

    if (!document.body.classList.contains("opj-direction-a")) {
        return;
    }

    function text(node) {
        return (node?.textContent || "").trim();
    }

    function compactTopbar() {
        const copy = document.querySelector(".eod-da-topbar-copy");
        if (!copy) {
            return;
        }
        const label = copy.querySelector("span");
        const value = copy.querySelector("strong");
        const workplace = (
            text(document.querySelector(".journal-workplace"))
            || text(document.querySelector(".shift-book-meta-period"))
            || "Электронная оперативная документация"
        );
        if (label) {
            label.textContent = "Рабочее место";
        }
        if (value) {
            value.textContent = workplace;
        }
    }

    function compactBoundary() {
        const boundary = document.querySelector("[data-opj-work-boundary]");
        if (!boundary || boundary.dataset.opjRepairCompact === "true") {
            return;
        }
        const copy = boundary.querySelector("div");
        const title = copy?.querySelector("strong");
        const description = copy?.querySelector("p");
        const chip = boundary.querySelector(".opj-boundary-chip");
        if (title) {
            title.textContent = "Рабочий черновик";
        }
        if (description) {
            description.textContent = "Записи текущей смены";
        }
        if (chip) {
            chip.textContent = "Автосохранение";
        }
        boundary.dataset.opjRepairCompact = "true";
    }

    function collapseRegisteredContext() {
        const context = document.querySelector("[data-opj-registered-context]");
        if (!context || context.dataset.opjRepairCompact === "true") {
            return;
        }
        context.open = false;
        context.dataset.opjRepairCompact = "true";
    }

    function applyRepair() {
        compactTopbar();
        compactBoundary();
        collapseRegisteredContext();
    }

    applyRepair();

    const observer = new MutationObserver(() => {
        applyRepair();
        if (
            document.querySelector("[data-opj-work-boundary][data-opj-repair-compact='true']")
            && document.querySelector("[data-opj-registered-context][data-opj-repair-compact='true']")
        ) {
            observer.disconnect();
        }
    });
    observer.observe(document.documentElement, {childList: true, subtree: true});
})();
