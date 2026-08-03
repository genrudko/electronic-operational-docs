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
            activeMenu.style.removeProperty("visibility");
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

    function replaceReferencedNumber(node, numberMap) {
        if (!node) return;
        const value = node.textContent || "";
        node.textContent = value.replace(/(запис(?:и|ь)\s*№\s*)(\d+)/gi, (match, prefix, oldNumber) => {
            return `${prefix}${numberMap.get(oldNumber) || oldNumber}`;
        });
    }

    function renumberVisibleJournal() {
        const numberMap = new Map();
        const screenRows = Array.from(document.querySelectorAll(".approved-journal-row"));
        screenRows.forEach((row, index) => {
            const numberNode = row.querySelector(".approved-journal-date-time small");
            const oldNumber = String(row.dataset.journalNumber || "").trim();
            const newNumber = String(index + 1);
            if (oldNumber) numberMap.set(oldNumber, newNumber);
            row.dataset.journalNumber = newNumber;
            if (numberNode) numberNode.textContent = `№ ${newNumber}`;
            row.querySelectorAll("[data-entry-label]").forEach((node) => {
                node.dataset.entryLabel = (node.dataset.entryLabel || "").replace(
                    /Запись №\s*\d+/,
                    `Запись № ${newNumber}`,
                );
            });
        });

        const printRows = Array.from(document.querySelectorAll(
            ".approved-journal-print-table tbody tr:not(:has(.journal-print-empty))",
        ));
        printRows.forEach((row, index) => {
            const numberNode = row.querySelector(".journal-print-number");
            if (!numberNode) return;
            const match = (numberNode.textContent || "").match(/\d+/);
            const oldNumber = match ? match[0] : "";
            const newNumber = String(index + 1);
            if (oldNumber) numberMap.set(oldNumber, newNumber);
            numberNode.textContent = `№ ${newNumber}`;
        });

        document.querySelectorAll(
            ".journal-print-lifecycle-label, .opj-entry-history-heading strong",
        ).forEach((node) => replaceReferencedNumber(node, numberMap));
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
            if (actionable) window.setTimeout(closeMenu, 0);
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

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", renumberVisibleJournal, {once: true});
    } else {
        renumberVisibleJournal();
    }
})();
