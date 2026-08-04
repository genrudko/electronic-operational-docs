(() => {
    "use strict";

    if (window.__EOD_OPJ_ACCEPTANCE_ACTION_REPAIR_00609__) return;
    window.__EOD_OPJ_ACCEPTANCE_ACTION_REPAIR_00609__ = true;

    let floatingMenu = null;

    function clamp(value, minimum, maximum) {
        return Math.max(minimum, Math.min(value, maximum));
    }

    function removeLegacyPortals() {
        document.querySelectorAll(
            "[data-action-portal], [data-action-repair-portal]",
        ).forEach((node) => {
            if (floatingMenu?.menu !== node) node.remove();
        });
    }

    function closeActionMenu({restoreFocus = false} = {}) {
        if (!floatingMenu) {
            removeLegacyPortals();
            return;
        }
        const {menu, root, trigger} = floatingMenu;
        menu.hidden = true;
        menu.classList.remove("is-floating", "opj-action-portal");
        menu.style.removeProperty("left");
        menu.style.removeProperty("top");
        menu.style.removeProperty("width");
        menu.style.removeProperty("visibility");
        root.append(menu);
        trigger.setAttribute("aria-expanded", "false");
        floatingMenu = null;
        removeLegacyPortals();
        if (restoreFocus && trigger.isConnected) {
            trigger.focus({preventScroll: true});
        }
    }

    function positionActionMenu(trigger, menu) {
        const margin = 12;
        const gap = 6;
        const triggerRect = trigger.getBoundingClientRect();
        const width = Math.min(310, window.innerWidth - margin * 2);
        menu.style.width = `${width}px`;
        menu.style.visibility = "hidden";
        menu.hidden = false;
        const menuRect = menu.getBoundingClientRect();
        let top = triggerRect.bottom + gap;
        if (top + menuRect.height > window.innerHeight - margin) {
            top = triggerRect.top - menuRect.height - gap;
        }
        const left = clamp(
            triggerRect.right - menuRect.width,
            margin,
            window.innerWidth - menuRect.width - margin,
        );
        top = clamp(top, margin, window.innerHeight - menuRect.height - margin);
        menu.style.left = `${Math.round(left)}px`;
        menu.style.top = `${Math.round(top)}px`;
        menu.style.visibility = "";
    }

    function openActionMenu(trigger) {
        const root = trigger.closest("[data-entry-actions]");
        const menu = root?.querySelector("[data-entry-actions-menu]");
        if (!root || !menu) return;
        if (floatingMenu?.trigger === trigger) {
            closeActionMenu({restoreFocus: true});
            return;
        }

        closeActionMenu();
        removeLegacyPortals();
        trigger.setAttribute("aria-expanded", "true");
        menu.classList.add("is-floating", "opj-action-portal");
        menu.dataset.actionRepairPortal = "";
        document.body.append(menu);
        floatingMenu = {menu, root, trigger};
        positionActionMenu(trigger, menu);
    }

    function editorPayload(scriptId) {
        const node = document.getElementById(scriptId || "");
        if (!node) return {};
        try {
            return JSON.parse(node.textContent || "{}");
        } catch (_error) {
            return {};
        }
    }

    function payloadText(payload) {
        const blocks = Array.isArray(payload?.blocks) ? payload.blocks : [];
        return blocks.map((block) => {
            const segments = Array.isArray(block?.segments) ? block.segments : [];
            return segments.map((segment) => String(segment?.text || "")).join("");
        }).join("\n").trim();
    }

    function initializeCorrectionEditor() {
        const dialog = document.querySelector("[data-correction-dialog]");
        const card = dialog?.querySelector("[data-draft-card]");
        if (!dialog || !card) return;
        try {
            window.EODDraftEditor?.initializeRow(card);
            window.EODDraftEditor?.bindToolbar(dialog);
        } catch (_error) {
            // Native fields remain available when the rich editor cannot initialise.
        }
    }

    function openCorrection(button) {
        closeActionMenu();
        const dialog = document.querySelector("[data-correction-dialog]");
        const form = dialog?.querySelector("[data-correction-form]");
        const editorForm = dialog?.querySelector("[data-draft-form]");
        if (!dialog || !form || !editorForm) return;

        const payload = editorPayload(button.dataset.editorPayloadId);
        form.action = button.dataset.correctUrl || "";
        const label = dialog.querySelector("[data-correction-entry-label]");
        if (label) label.textContent = button.dataset.entryLabel || "";
        const reason = form.querySelector("[name=reason]");
        if (reason) reason.value = "";
        const payloadField = form.querySelector("[name=replacement_editor_payload]");
        const contentField = form.querySelector("[name=replacement_content]");
        if (payloadField) payloadField.value = JSON.stringify(payload);
        if (contentField) contentField.value = payloadText(payload);

        initializeCorrectionEditor();
        try {
            window.EODDraftEditor?.acceptSaved(editorForm, {editor_payload: payload});
        } catch (_error) {
            // Fallback textarea already contains the registered text.
        }
        dialog.showModal();
        window.requestAnimationFrame(() => {
            try {
                window.EODDraftEditor?.focus(editorForm, "end");
            } catch (_error) {
                contentField?.focus({preventScroll: true});
            }
        });
    }

    function closeCorrection() {
        const dialog = document.querySelector("[data-correction-dialog]");
        const editorForm = dialog?.querySelector("[data-draft-form]");
        try {
            window.EODDraftEditor?.deactivate(editorForm);
        } catch (_error) {
            // Closing must never depend on editor state.
        }
        if (dialog?.open) dialog.close();
    }

    function openCancellation(button) {
        closeActionMenu();
        const dialog = document.querySelector("[data-cancellation-dialog]");
        const form = dialog?.querySelector("[data-cancellation-form]");
        if (!dialog || !form) return;
        form.action = button.dataset.cancelUrl || "";
        const label = dialog.querySelector("[data-cancellation-entry-label]");
        if (label) label.textContent = button.dataset.entryLabel || "";
        const reason = form.querySelector("[name=reason]");
        if (reason) reason.value = "";
        dialog.showModal();
        reason?.focus({preventScroll: true});
    }

    function closeCancellation() {
        const dialog = document.querySelector("[data-cancellation-dialog]");
        if (dialog?.open) dialog.close();
    }

    function toggleHistory(button) {
        closeActionMenu();
        const history = document.getElementById(button.dataset.historyId || "");
        if (!history) return;
        history.hidden = !history.hidden;
        if (!history.hidden) history.scrollIntoView({block: "nearest"});
    }

    function handleActionClick(event) {
        const toggle = event.target.closest?.("[data-entry-actions-toggle]");
        if (toggle) {
            event.preventDefault();
            event.stopImmediatePropagation();
            openActionMenu(toggle);
            return;
        }

        const correction = event.target.closest?.("[data-open-correction]");
        if (correction) {
            event.preventDefault();
            event.stopImmediatePropagation();
            openCorrection(correction);
            return;
        }

        const cancellation = event.target.closest?.("[data-open-cancellation]");
        if (cancellation) {
            event.preventDefault();
            event.stopImmediatePropagation();
            openCancellation(cancellation);
            return;
        }

        const history = event.target.closest?.("[data-toggle-entry-history]");
        if (history) {
            event.preventDefault();
            event.stopImmediatePropagation();
            toggleHistory(history);
            return;
        }

        if (event.target.closest?.("[data-close-entry-history]")) {
            event.preventDefault();
            event.stopImmediatePropagation();
            const panel = event.target.closest("[data-entry-history]");
            if (panel) panel.hidden = true;
            return;
        }

        if (event.target.closest?.("[data-close-correction]")) {
            event.preventDefault();
            event.stopImmediatePropagation();
            closeCorrection();
            return;
        }

        if (event.target.closest?.("[data-close-cancellation]")) {
            event.preventDefault();
            event.stopImmediatePropagation();
            closeCancellation();
            return;
        }

        if (event.target.closest?.("[data-action-repair-portal] a[href]")) {
            closeActionMenu();
            return;
        }

        if (floatingMenu && !floatingMenu.menu.contains(event.target)) {
            closeActionMenu();
        }
    }

    document.addEventListener("click", handleActionClick, true);
    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        if (floatingMenu) {
            event.preventDefault();
            closeActionMenu({restoreFocus: true});
        }
    });
    window.addEventListener("resize", () => closeActionMenu());
    window.addEventListener("scroll", () => closeActionMenu(), {passive: true});

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeCorrectionEditor, {once: true});
    } else {
        initializeCorrectionEditor();
    }
})();
