(() => {
    "use strict";

    const correctionDialog = document.querySelector("[data-correction-dialog]");
    const cancellationDialog = document.querySelector("[data-cancellation-dialog]");
    const correctionEditorForm = correctionDialog?.querySelector("[data-draft-form]");
    const correctionSubmitForm = correctionDialog?.querySelector("[data-correction-form]");
    const settingsDialog = document.getElementById("journal-display-settings");
    const catalogNode = document.getElementById("opj-semantic-reference-catalog");

    let actionPortal = null;
    let actionTrigger = null;
    let referencePreview = null;
    let referenceTrigger = null;
    let catalog = {};

    try {
        catalog = catalogNode ? JSON.parse(catalogNode.textContent || "{}") : {};
    } catch (_error) {
        catalog = {};
    }

    const catalogByReference = new Map();
    Object.values(catalog).forEach((rows) => {
        if (!Array.isArray(rows)) return;
        rows.forEach((row) => {
            if (row?.reference) catalogByReference.set(row.reference, row);
        });
    });

    function withinViewport(left, top, width, height) {
        const margin = 12;
        return {
            left: Math.max(margin, Math.min(left, window.innerWidth - width - margin)),
            top: Math.max(margin, Math.min(top, window.innerHeight - height - margin)),
        };
    }

    function placeOverlay(anchor, overlay, preferredWidth = 310) {
        const rect = anchor.getBoundingClientRect();
        overlay.style.width = `${Math.min(preferredWidth, window.innerWidth - 24)}px`;
        overlay.style.visibility = "hidden";
        overlay.hidden = false;
        const overlayRect = overlay.getBoundingClientRect();
        let top = rect.bottom + 6;
        if (top + overlayRect.height > window.innerHeight - 12) {
            top = rect.top - overlayRect.height - 6;
        }
        const position = withinViewport(
            rect.right - overlayRect.width,
            top,
            overlayRect.width,
            overlayRect.height,
        );
        overlay.style.left = `${Math.round(position.left)}px`;
        overlay.style.top = `${Math.round(position.top)}px`;
        overlay.style.visibility = "";
    }

    function closeActionMenu({restoreFocus = false} = {}) {
        if (actionPortal) actionPortal.remove();
        actionPortal = null;
        if (actionTrigger) {
            actionTrigger.setAttribute("aria-expanded", "false");
            if (restoreFocus && actionTrigger.isConnected) {
                actionTrigger.focus({preventScroll: true});
            }
        }
        actionTrigger = null;
    }

    function openActionMenu(trigger) {
        const source = trigger.closest("[data-entry-actions]")
            ?.querySelector("[data-entry-actions-menu]");
        if (!source) return;
        if (actionTrigger === trigger) {
            closeActionMenu({restoreFocus: true});
            return;
        }
        closeActionMenu();
        actionTrigger = trigger;
        actionTrigger.setAttribute("aria-expanded", "true");
        actionPortal = source.cloneNode(true);
        actionPortal.hidden = false;
        actionPortal.classList.add("is-floating", "opj-action-portal");
        actionPortal.dataset.actionPortal = "";
        document.body.append(actionPortal);
        placeOverlay(trigger, actionPortal, 310);
        actionPortal.querySelector("[role=menuitem]")?.focus({preventScroll: true});
    }

    function parseEditorPayload(scriptId) {
        const script = document.getElementById(scriptId);
        if (!script) throw new Error("Не найдена зарегистрированная редакция записи.");
        return JSON.parse(script.textContent || "{}");
    }

    function initializeCorrectionEditor() {
        if (!correctionDialog || !correctionEditorForm) return;
        try {
            const card = correctionDialog.querySelector("[data-draft-card]");
            window.EODDraftEditor?.initializeRow(card);
            window.EODDraftEditor?.bindToolbar(correctionDialog);
        } catch (_error) {
            // Ошибка редактора исправления не должна отключать меню действий.
        }
    }

    function openCorrection(button) {
        closeActionMenu();
        if (!correctionDialog || !correctionEditorForm || !correctionSubmitForm) return;
        const errorNode = correctionDialog.querySelector("[data-correction-error]");
        try {
            const payload = parseEditorPayload(button.dataset.editorPayloadId);
            correctionSubmitForm.action = button.dataset.correctUrl;
            correctionDialog.querySelector("[data-correction-entry-label]").textContent = (
                button.dataset.entryLabel || ""
            );
            correctionSubmitForm.querySelector("[name=reason]").value = "";
            const card = correctionDialog.querySelector("[data-draft-card]");
            card.dataset.draftId = `correction-${button.dataset.editorPayloadId || "entry"}`;
            window.EODDraftEditor?.acceptSaved(correctionEditorForm, {editor_payload: payload});
            if (errorNode) {
                errorNode.hidden = true;
                errorNode.textContent = "";
            }
        } catch (error) {
            if (errorNode) {
                errorNode.textContent = error.message || "Не удалось открыть редактор исправления.";
                errorNode.hidden = false;
            }
        }
        correctionDialog.showModal();
        window.requestAnimationFrame(() => {
            window.EODDraftEditor?.focus(correctionEditorForm, "end");
        });
    }

    function closeCorrection() {
        window.EODDraftEditor?.deactivate(correctionEditorForm);
        if (correctionDialog?.open) correctionDialog.close();
    }

    function openCancellation(button) {
        closeActionMenu();
        if (!cancellationDialog) return;
        const form = cancellationDialog.querySelector("[data-cancellation-form]");
        form.action = button.dataset.cancelUrl;
        form.querySelector("[name=reason]").value = "";
        cancellationDialog.querySelector("[data-cancellation-entry-label]").textContent = (
            button.dataset.entryLabel || ""
        );
        cancellationDialog.showModal();
        form.querySelector("[name=reason]")?.focus({preventScroll: true});
    }

    function closeCancellation() {
        if (cancellationDialog?.open) cancellationDialog.close();
    }

    function toggleHistory(button) {
        closeActionMenu();
        const history = document.getElementById(button.dataset.historyId);
        if (!history) return;
        history.hidden = !history.hidden;
        if (!history.hidden) history.scrollIntoView({block: "nearest", behavior: "smooth"});
    }

    function buildReferencePreview() {
        if (referencePreview) return referencePreview;
        const preview = document.createElement("aside");
        preview.className = "draft-reference-preview opj-reference-preview screen-only";
        preview.dataset.opjReferencePreview = "";
        preview.setAttribute("role", "dialog");
        preview.setAttribute("aria-label", "Связанный объект");
        preview.hidden = true;
        preview.innerHTML = `
            <header>
                <div><span class="draft-reference-preview-kind" data-preview-kind></span><strong data-preview-label></strong></div>
                <button type="button" class="draft-reference-preview-close" data-preview-close aria-label="Закрыть карточку">×</button>
            </header>
            <p class="draft-reference-preview-meta" data-preview-meta></p>
            <p class="draft-reference-preview-summary" data-preview-summary></p>
            <dl class="draft-reference-preview-facts" data-preview-facts></dl>
            <span class="draft-reference-preview-status" data-preview-status></span>
            <footer class="draft-reference-preview-actions">
                <button type="button" class="da-button is-secondary is-compact" data-preview-open>Открыть карточку</button>
            </footer>`;
        document.body.append(preview);
        preview.querySelector("[data-preview-close]").addEventListener("click", () => {
            closeReferencePreview({restoreFocus: true});
        });
        preview.querySelector("[data-preview-open]").addEventListener("click", () => {
            const url = preview.dataset.referenceUrl;
            if (url) window.location.assign(url);
        });
        referencePreview = preview;
        return preview;
    }

    function referenceKindLabel(kind) {
        return {
            equipment: "Оборудование",
            document: "Документ",
            person: "Сотрудник",
            employee: "Сотрудник",
            related_entry: "Запись журнала",
        }[kind] || "Связанный объект";
    }

    function renderFacts(node, facts) {
        node.replaceChildren();
        (Array.isArray(facts) ? facts : []).slice(0, 8).forEach((fact) => {
            const term = document.createElement("dt");
            term.textContent = String(fact?.label || "");
            const value = document.createElement("dd");
            value.textContent = String(fact?.value || "—");
            node.append(term, value);
        });
        node.hidden = node.childElementCount === 0;
    }

    function openReferencePreview(trigger) {
        closeActionMenu();
        closeReferencePreview();
        const preview = buildReferencePreview();
        const identity = trigger.dataset.referenceValue || "";
        const kind = trigger.dataset.referenceKind || identity.split(":", 1)[0] || "";
        const item = catalogByReference.get(identity) || {};
        const details = item.preview && typeof item.preview === "object" ? item.preview : {};
        const label = item.label || trigger.dataset.referenceLabel || trigger.textContent.trim();
        const meta = item.meta || "Связанный объект оперативной записи";
        preview.querySelector("[data-preview-kind]").textContent = referenceKindLabel(kind);
        preview.querySelector("[data-preview-label]").textContent = label;
        preview.querySelector("[data-preview-meta]").textContent = meta;
        const summary = String(details.summary || "");
        preview.querySelector("[data-preview-summary]").textContent = summary;
        preview.querySelector("[data-preview-summary]").hidden = !summary || summary === meta;
        const status = String(details.status || "");
        preview.querySelector("[data-preview-status]").textContent = status;
        preview.querySelector("[data-preview-status]").hidden = !status;
        renderFacts(preview.querySelector("[data-preview-facts]"), details.facts);
        preview.dataset.referenceUrl = trigger.dataset.referenceUrl || "";
        preview.querySelector("[data-preview-open]").hidden = !preview.dataset.referenceUrl;
        referenceTrigger = trigger;
        placeOverlay(trigger, preview, 390);
        preview.querySelector("[data-preview-close]").focus({preventScroll: true});
    }

    function closeReferencePreview({restoreFocus = false} = {}) {
        if (referencePreview) referencePreview.hidden = true;
        if (restoreFocus && referenceTrigger?.isConnected) {
            referenceTrigger.focus({preventScroll: true});
        }
        referenceTrigger = null;
    }

    document.addEventListener("click", (event) => {
        const actionToggle = event.target.closest?.("[data-entry-actions-toggle]");
        if (actionToggle) {
            event.preventDefault();
            event.stopPropagation();
            openActionMenu(actionToggle);
            return;
        }
        const correction = event.target.closest?.("[data-open-correction]");
        if (correction) {
            event.preventDefault();
            openCorrection(correction);
            return;
        }
        const cancellation = event.target.closest?.("[data-open-cancellation]");
        if (cancellation) {
            event.preventDefault();
            openCancellation(cancellation);
            return;
        }
        const history = event.target.closest?.("[data-toggle-entry-history]");
        if (history) {
            event.preventDefault();
            toggleHistory(history);
            return;
        }
        const reference = event.target.closest?.("[data-opj-reference-token]");
        if (reference) {
            event.preventDefault();
            event.stopPropagation();
            openReferencePreview(reference);
            return;
        }
        if (event.target.closest?.("[data-close-entry-history]")) {
            const panel = event.target.closest("[data-entry-history]");
            if (panel) panel.hidden = true;
            return;
        }
        if (event.target.closest?.("[data-close-correction]")) {
            closeCorrection();
            return;
        }
        if (event.target.closest?.("[data-close-cancellation]")) {
            closeCancellation();
            return;
        }
        if (event.target.closest?.("[data-open-journal-settings]")) {
            settingsDialog?.showModal();
            return;
        }
        if (event.target.closest?.("[data-close-journal-settings]")) {
            settingsDialog?.close();
            return;
        }
        const portalLink = event.target.closest?.("[data-action-portal] a[href]");
        if (portalLink) {
            window.EODOPJNavigation?.allowOnce();
            closeActionMenu();
            return;
        }
        if (actionPortal && !actionPortal.contains(event.target)) closeActionMenu();
        if (referencePreview && !referencePreview.hidden
            && !referencePreview.contains(event.target)
            && event.target !== referenceTrigger) {
            closeReferencePreview();
        }
    }, true);

    correctionSubmitForm?.addEventListener("submit", (event) => {
        window.EODDraftEditor?.syncForm(correctionEditorForm);
        const content = correctionSubmitForm
            .querySelector("[name=replacement_content]")?.value.trim();
        const reason = correctionSubmitForm.querySelector("[name=reason]")?.value.trim();
        const error = correctionDialog.querySelector("[data-correction-error]");
        if (!content || !reason) {
            event.preventDefault();
            if (error) {
                error.textContent = !content
                    ? "Исправленная редакция не может быть пустой."
                    : "Укажите причину исправления.";
                error.hidden = false;
            }
        }
    });

    [correctionDialog, cancellationDialog].forEach((dialog) => {
        dialog?.addEventListener("click", (event) => {
            if (event.target !== dialog) return;
            if (dialog === correctionDialog) closeCorrection();
            if (dialog === cancellationDialog) closeCancellation();
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        if (actionPortal) return closeActionMenu({restoreFocus: true});
        if (referencePreview && !referencePreview.hidden) {
            return closeReferencePreview({restoreFocus: true});
        }
        if (correctionDialog?.open) return closeCorrection();
        if (cancellationDialog?.open) return closeCancellation();
        if (settingsDialog?.open) settingsDialog.close();
    });

    const closeTransientOverlays = () => {
        closeActionMenu();
        closeReferencePreview();
    };
    window.addEventListener("resize", closeTransientOverlays);
    document.addEventListener("scroll", closeTransientOverlays, true);

    document.querySelectorAll(
        ".opj-registered-context, [data-opj-registered-context]",
    ).forEach((node) => node.remove());

    initializeCorrectionEditor();
})();
