(() => {
    "use strict";

    if (window.__EOD_OPJ_ACCEPTANCE_ACTION_REPAIR_00608__) return;
    window.__EOD_OPJ_ACCEPTANCE_ACTION_REPAIR_00608__ = true;

    let actionPortal = null;
    let actionTrigger = null;

    function clamp(value, minimum, maximum) {
        return Math.max(minimum, Math.min(value, maximum));
    }

    function closeActionMenu({restoreFocus = false} = {}) {
        actionPortal?.remove();
        actionPortal = null;
        if (actionTrigger) {
            actionTrigger.setAttribute("aria-expanded", "false");
            if (restoreFocus && actionTrigger.isConnected) {
                actionTrigger.focus({preventScroll: true});
            }
        }
        actionTrigger = null;
    }

    function positionActionMenu(trigger, menu) {
        const margin = 12;
        const triggerRect = trigger.getBoundingClientRect();
        menu.style.visibility = "hidden";
        menu.style.width = `${Math.min(310, window.innerWidth - margin * 2)}px`;
        document.body.append(menu);
        const menuRect = menu.getBoundingClientRect();
        let top = triggerRect.bottom + 6;
        if (top + menuRect.height > window.innerHeight - margin) {
            top = triggerRect.top - menuRect.height - 6;
        }
        menu.style.left = `${Math.round(clamp(
            triggerRect.right - menuRect.width,
            margin,
            window.innerWidth - menuRect.width - margin,
        ))}px`;
        menu.style.top = `${Math.round(clamp(
            top,
            margin,
            window.innerHeight - menuRect.height - margin,
        ))}px`;
        menu.style.visibility = "";
    }

    function openActionMenu(trigger) {
        if (actionTrigger === trigger) {
            closeActionMenu({restoreFocus: true});
            return;
        }
        closeActionMenu();
        const source = trigger.closest("[data-entry-actions]")
            ?.querySelector("[data-entry-actions-menu]");
        if (!source) return;

        actionTrigger = trigger;
        actionTrigger.setAttribute("aria-expanded", "true");
        actionPortal = source.cloneNode(true);
        actionPortal.hidden = false;
        actionPortal.classList.add("is-floating", "opj-action-portal");
        actionPortal.dataset.actionRepairPortal = "";
        positionActionMenu(trigger, actionPortal);
        actionPortal.querySelector("[role=menuitem]")?.focus({preventScroll: true});
    }

    function editorPayload(scriptId) {
        const node = document.getElementById(scriptId);
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
            // Native textareas remain usable even if the rich editor is unavailable.
        }
    }

    function openCorrection(button) {
        const dialog = document.querySelector("[data-correction-dialog]");
        const form = dialog?.querySelector("[data-correction-form]");
        const editorForm = dialog?.querySelector("[data-draft-form]");
        if (!dialog || !form || !editorForm) return;

        const payload = editorPayload(button.dataset.editorPayloadId);
        form.action = button.dataset.correctUrl || "";
        dialog.querySelector("[data-correction-entry-label]").textContent = (
            button.dataset.entryLabel || ""
        );
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
            // Fallback textarea was already populated above.
        }
        dialog.showModal();
        window.requestAnimationFrame(() => {
            window.EODDraftEditor?.focus(editorForm, "end");
        });
    }

    function closeCorrection() {
        const dialog = document.querySelector("[data-correction-dialog]");
        const editorForm = dialog?.querySelector("[data-draft-form]");
        try {
            window.EODDraftEditor?.deactivate(editorForm);
        } catch (_error) {
            // Closing the dialog must remain available without the rich editor.
        }
        if (dialog?.open) dialog.close();
    }

    function openCancellation(button) {
        const dialog = document.querySelector("[data-cancellation-dialog]");
        const form = dialog?.querySelector("[data-cancellation-form]");
        if (!dialog || !form) return;
        form.action = button.dataset.cancelUrl || "";
        dialog.querySelector("[data-cancellation-entry-label]").textContent = (
            button.dataset.entryLabel || ""
        );
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
        const history = document.getElementById(button.dataset.historyId || "");
        if (!history) return;
        history.hidden = !history.hidden;
        if (!history.hidden) history.scrollIntoView({block: "nearest"});
    }

    document.addEventListener("click", (event) => {
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
            closeActionMenu();
            openCorrection(correction);
            return;
        }

        const cancellation = event.target.closest?.("[data-open-cancellation]");
        if (cancellation) {
            event.preventDefault();
            event.stopImmediatePropagation();
            closeActionMenu();
            openCancellation(cancellation);
            return;
        }

        const history = event.target.closest?.("[data-toggle-entry-history]");
        if (history) {
            event.preventDefault();
            event.stopImmediatePropagation();
            closeActionMenu();
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

        if (event.target.closest?.("[data-open-journal-settings]")) {
            event.preventDefault();
            event.stopImmediatePropagation();
            document.getElementById("journal-display-settings")?.showModal();
            return;
        }

        if (event.target.closest?.("[data-close-journal-settings]")) {
            event.preventDefault();
            event.stopImmediatePropagation();
            document.getElementById("journal-display-settings")?.close();
            return;
        }

        if (event.target.closest?.("[data-action-repair-portal] a[href]")) {
            closeActionMenu();
            return;
        }

        if (actionPortal && !actionPortal.contains(event.target)) closeActionMenu();
    }, true);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && actionPortal) {
            event.preventDefault();
            closeActionMenu({restoreFocus: true});
        }
    });

    window.addEventListener("resize", () => closeActionMenu());
    document.addEventListener("scroll", () => closeActionMenu(), true);

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeCorrectionEditor, {once: true});
    } else {
        initializeCorrectionEditor();
    }
})();
