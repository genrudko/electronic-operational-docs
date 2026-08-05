(() => {
    "use strict";

    const workspace = document.querySelector("[data-draft-workspace]");
    const registerDialog = document.querySelector("[data-register-dialog]");
    const correctionDialog = document.querySelector("[data-correction-dialog]");
    const cancellationDialog = document.querySelector("[data-cancellation-dialog]");
    const correctionEditorForm = correctionDialog?.querySelector("[data-draft-form]");
    const correctionSubmitForm = correctionDialog?.querySelector("[data-correction-form]");
    const selectionToggle = document.querySelector("[data-selection-mode-toggle]");

    let pendingRegistrationRows = [];
    let floatingMenu = null;

    function firstError(payload) {
        if (typeof payload?.message === "string" && payload.message) {
            return payload.message;
        }
        const errors = payload?.errors;
        if (!errors) return "Не удалось сохранить строку.";
        if (Array.isArray(errors)) return String(errors[0] || "Ошибка сохранения.");
        for (const value of Object.values(errors)) {
            if (Array.isArray(value) && value.length) {
                const first = value[0];
                return typeof first === "object"
                    ? String(first.message || first)
                    : String(first);
            }
        }
        return "Не удалось сохранить строку.";
    }

    function setStatus(form, text, state) {
        const node = form.querySelector("[data-save-status]");
        if (!node) return;
        node.textContent = text;
        node.classList.remove("is-saved", "is-saving", "is-error", "is-dirty");
        if (state) node.classList.add(state);
    }

    async function responsePayload(response) {
        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) return response.json();
        return {ok: response.ok, message: response.statusText};
    }

    async function persistDraft(form) {
        window.EODDraftEditor?.syncForm(form);
        setStatus(form, "Сохранение перед регистрацией…", "is-saving");
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            credentials: "same-origin",
            headers: {"X-Requested-With": "XMLHttpRequest"},
        });
        const payload = await responsePayload(response);
        if (!response.ok || !payload.ok) throw new Error(firstError(payload));
        const version = form.querySelector("[data-draft-version]");
        if (version) version.value = String(payload.version);
        window.EODDraftEditor?.acceptSaved(form, payload);
        setStatus(form, `Сохранено · ${payload.saved_at}`, "is-saved");
    }

    function registerableRows() {
        return Array.from(document.querySelectorAll("[data-registerable-draft]"));
    }

    function rowCheckbox(row) {
        return row?.querySelector("[data-draft-selection]") || null;
    }

    function selectedRows() {
        return registerableRows().filter((row) => rowCheckbox(row)?.checked);
    }

    function setSelectionMode(active) {
        if (!workspace) return;
        workspace.classList.toggle("is-selection-mode", active);
        selectionToggle?.setAttribute("aria-pressed", String(active));
        if (selectionToggle) {
            const label = active ? "Завершить выбор" : "Выбрать записи";
            selectionToggle.querySelector("span").textContent = label;
        }
        if (!active) {
            registerableRows().forEach((row) => {
                const checkbox = rowCheckbox(row);
                if (checkbox) checkbox.checked = false;
            });
        }
        updateSelectionUi();
    }

    function updateSelectionUi() {
        const rows = registerableRows();
        const selected = selectedRows();
        const bar = document.querySelector("[data-batch-registration-bar]");
        const count = document.querySelector("[data-selected-count]");
        const selectAll = document.querySelector("[data-select-all-drafts]");
        rows.forEach((row) => {
            row.classList.toggle(
                "is-selected-for-registration",
                Boolean(rowCheckbox(row)?.checked),
            );
        });
        if (bar) {
            bar.hidden = !workspace?.classList.contains("is-selection-mode")
                || selected.length === 0;
        }
        if (count) count.textContent = `Выбрано: ${selected.length}`;
        if (selectAll) {
            selectAll.checked = rows.length > 0 && selected.length === rows.length;
            selectAll.indeterminate = selected.length > 0 && selected.length < rows.length;
        }
    }

    function setRowsSelected(rows, selected) {
        rows.forEach((row) => {
            const checkbox = rowCheckbox(row);
            if (checkbox) checkbox.checked = selected;
        });
        updateSelectionUi();
    }

    function rowSummary(row) {
        const time = row.querySelector("[data-quick-time]")?.value
            || row.dataset.entryAt?.slice(11, 16)
            || "—";
        const fallback = row.querySelector("[data-editor-fallback]");
        const content = String(fallback?.value || row.textContent || "")
            .replace(/\s+/g, " ")
            .trim();
        return {time, content: content || "Пустая строка"};
    }

    function openRegisterDialog(rows) {
        if (!registerDialog || !rows.length) return;
        pendingRegistrationRows = rows;
        const count = registerDialog.querySelector("[data-register-dialog-count]");
        const list = registerDialog.querySelector("[data-register-dialog-list]");
        const label = registerDialog.querySelector("[data-register-confirm-label]");
        const error = registerDialog.querySelector("[data-register-dialog-error]");
        if (count) count.textContent = `Выбрано строк: ${rows.length}`;
        if (label) {
            label.textContent = rows.length === 1
                ? "Перенести запись"
                : `Перенести ${rows.length} записей`;
        }
        if (error) {
            error.hidden = true;
            error.textContent = "";
        }
        if (list) {
            list.replaceChildren(...rows.map((row) => {
                const summary = rowSummary(row);
                const item = document.createElement("div");
                item.className = "opj-register-selection-item";
                const time = document.createElement("strong");
                time.textContent = summary.time;
                const content = document.createElement("span");
                content.textContent = summary.content;
                item.append(time, content);
                return item;
            }));
        }
        registerDialog.showModal();
        registerDialog.querySelector("[data-register-confirm]")?.focus();
    }

    function closeRegisterDialog() {
        if (registerDialog?.open) registerDialog.close();
        pendingRegistrationRows = [];
    }

    async function submitRegistration() {
        if (!registerDialog || !pendingRegistrationRows.length) return;
        const confirmButton = registerDialog.querySelector("[data-register-confirm]");
        const errorNode = registerDialog.querySelector("[data-register-dialog-error]");
        const originalLabel = confirmButton?.textContent || "Перенести в чистовик";
        if (confirmButton) {
            confirmButton.disabled = true;
            confirmButton.textContent = "Сохранение и регистрация…";
        }
        if (errorNode) {
            errorNode.hidden = true;
            errorNode.textContent = "";
        }

        try {
            const orderedRows = [...pendingRegistrationRows].sort((left, right) => (
                String(left.dataset.entryAt || "").localeCompare(
                    String(right.dataset.entryAt || ""),
                ) || Number(left.dataset.entryPosition || 0)
                    - Number(right.dataset.entryPosition || 0)
            ));
            for (const row of orderedRows) {
                const form = row.querySelector("form[data-draft-form]");
                if (!form) throw new Error("Не найдена форма выбранной строки.");
                await persistDraft(form);
            }

            const firstForm = orderedRows[0].querySelector("form[data-draft-form]");
            const body = new FormData();
            const csrf = firstForm?.querySelector("[name=csrfmiddlewaretoken]")?.value;
            if (csrf) body.append("csrfmiddlewaretoken", csrf);
            orderedRows.forEach((row) => body.append("draft_ids", row.dataset.draftId));
            const response = await fetch(registerDialog.dataset.batchUrl, {
                method: "POST",
                body,
                credentials: "same-origin",
                headers: {"X-Requested-With": "XMLHttpRequest"},
            });
            const payload = await responsePayload(response);
            const registeredCount = Number(payload.registered_count || 0);
            if (!response.ok || registeredCount === 0) {
                const resultError = payload.results?.find((item) => !item.ok)?.message;
                throw new Error(resultError || firstError(payload));
            }
            if (payload.failed_count) {
                const messages = payload.results
                    .filter((item) => !item.ok)
                    .map((item) => item.message)
                    .filter(Boolean);
                if (errorNode) {
                    errorNode.textContent = (
                        `Перенесено: ${registeredCount}. `
                        + `Не перенесено: ${payload.failed_count}. `
                        + messages.join(" ")
                    );
                    errorNode.hidden = false;
                }
                window.setTimeout(() => {
                    closeRegisterDialog();
                    setSelectionMode(false);
                    window.EODOPJNavigation?.allowOnce();
                    window.location.reload();
                }, 1500);
                return;
            }
            const lastSuccess = [...payload.results].reverse().find((item) => item.ok);
            const target = new URL(window.location.href);
            target.hash = lastSuccess?.public_id ? `draft-${lastSuccess.public_id}` : "";
            closeRegisterDialog();
            setSelectionMode(false);
            window.EODOPJNavigation?.allowOnce();
            window.location.assign(target.toString());
        } catch (error) {
            if (errorNode) {
                errorNode.textContent = error.message || "Не удалось перенести выбранные строки.";
                errorNode.hidden = false;
            }
            pendingRegistrationRows.forEach((row) => {
                const form = row.querySelector("form[data-draft-form]");
                if (form) setStatus(form, error.message || "Ошибка регистрации.", "is-error");
            });
        } finally {
            if (confirmButton) {
                confirmButton.disabled = false;
                confirmButton.textContent = originalLabel;
            }
        }
    }

    function restoreFloatingMenu() {
        if (!floatingMenu) return;
        const {menu, root, button} = floatingMenu;
        menu.hidden = true;
        menu.classList.remove("is-floating");
        menu.style.removeProperty("left");
        menu.style.removeProperty("top");
        root.append(menu);
        button.setAttribute("aria-expanded", "false");
        floatingMenu = null;
    }

    function closeActionMenus() {
        restoreFloatingMenu();
        document.querySelectorAll("[data-entry-actions]").forEach((root) => {
            const button = root.querySelector("[data-entry-actions-toggle]");
            const menu = root.querySelector("[data-entry-actions-menu]");
            if (button) button.setAttribute("aria-expanded", "false");
            if (menu) menu.hidden = true;
        });
    }

    function placeFloatingMenu(button, menu) {
        const margin = 12;
        const gap = 6;
        const buttonRect = button.getBoundingClientRect();
        menu.style.visibility = "hidden";
        menu.hidden = false;
        const menuRect = menu.getBoundingClientRect();
        let left = buttonRect.right - menuRect.width;
        left = Math.max(margin, Math.min(left, window.innerWidth - menuRect.width - margin));
        let top = buttonRect.bottom + gap;
        if (top + menuRect.height > window.innerHeight - margin) {
            top = Math.max(margin, buttonRect.top - menuRect.height - gap);
        }
        menu.style.left = `${Math.round(left)}px`;
        menu.style.top = `${Math.round(top)}px`;
        menu.style.visibility = "";
    }

    function toggleActionMenu(button) {
        const root = button.closest("[data-entry-actions]");
        const menu = root?.querySelector("[data-entry-actions-menu]");
        if (!root || !menu) return;
        if (floatingMenu?.button === button) {
            closeActionMenus();
            return;
        }
        closeActionMenus();
        document.body.append(menu);
        menu.classList.add("is-floating");
        button.setAttribute("aria-expanded", "true");
        floatingMenu = {root, menu, button};
        placeFloatingMenu(button, menu);
        menu.querySelector("[role=menuitem]")?.focus({preventScroll: true});
    }

    function parseEditorPayload(scriptId) {
        const script = document.getElementById(scriptId);
        if (!script) throw new Error("Не найдена зарегистрированная редакция записи.");
        return JSON.parse(script.textContent || "{}");
    }

    function initializeCorrectionEditor() {
        if (!correctionDialog || !correctionEditorForm) return;
        const card = correctionDialog.querySelector("[data-draft-card]");
        window.EODDraftEditor?.initializeRow(card);
        window.EODDraftEditor?.bindToolbar(correctionDialog);
    }

    function openCorrection(button) {
        if (!correctionDialog || !correctionEditorForm || !correctionSubmitForm) return;
        closeActionMenus();
        const errorNode = correctionDialog.querySelector("[data-correction-error]");
        if (errorNode) {
            errorNode.hidden = true;
            errorNode.textContent = "";
        }
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
            correctionDialog.showModal();
            window.requestAnimationFrame(() => {
                window.EODDraftEditor?.focus(correctionEditorForm, "end");
            });
        } catch (error) {
            if (errorNode) {
                errorNode.textContent = error.message || "Не удалось открыть редактор исправления.";
                errorNode.hidden = false;
            }
            correctionDialog.showModal();
        }
    }

    function closeCorrection() {
        if (!correctionDialog) return;
        window.EODDraftEditor?.deactivate(correctionEditorForm);
        if (correctionDialog.open) correctionDialog.close();
    }

    function openCancellation(button) {
        if (!cancellationDialog) return;
        closeActionMenus();
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
        const history = document.getElementById(button.dataset.historyId);
        closeActionMenus();
        if (!history) return;
        history.hidden = !history.hidden;
        if (!history.hidden) history.scrollIntoView({block: "nearest", behavior: "smooth"});
    }

    document.addEventListener("change", (event) => {
        if (event.target.matches("[data-draft-selection]")) updateSelectionUi();
        if (event.target.matches("[data-select-all-drafts]")) {
            setRowsSelected(registerableRows(), event.target.checked);
        }
    });

    document.addEventListener("click", (event) => {
        const registerButton = event.target.closest?.("[data-register-draft]");
        if (registerButton) {
            event.preventDefault();
            const row = registerButton.closest("[data-registerable-draft]");
            if (row) openRegisterDialog([row]);
            return;
        }
        if (event.target.closest?.("[data-selection-mode-toggle]")) {
            event.preventDefault();
            setSelectionMode(!workspace?.classList.contains("is-selection-mode"));
            return;
        }
        if (event.target.closest?.("[data-register-selected]")) {
            event.preventDefault();
            openRegisterDialog(selectedRows());
            return;
        }
        if (event.target.closest?.("[data-clear-draft-selection]")) {
            event.preventDefault();
            setRowsSelected(registerableRows(), false);
            return;
        }
        if (event.target.closest?.("[data-register-confirm]")) {
            event.preventDefault();
            void submitRegistration();
            return;
        }
        if (event.target.closest?.("[data-dialog-close]")) {
            event.preventDefault();
            closeRegisterDialog();
            return;
        }

        const actionToggle = event.target.closest?.("[data-entry-actions-toggle]");
        if (actionToggle) {
            event.preventDefault();
            toggleActionMenu(actionToggle);
            return;
        }
        const correctionButton = event.target.closest?.("[data-open-correction]");
        if (correctionButton) {
            event.preventDefault();
            openCorrection(correctionButton);
            return;
        }
        const cancellationButton = event.target.closest?.("[data-open-cancellation]");
        if (cancellationButton) {
            event.preventDefault();
            openCancellation(cancellationButton);
            return;
        }
        const historyButton = event.target.closest?.("[data-toggle-entry-history]");
        if (historyButton) {
            event.preventDefault();
            toggleHistory(historyButton);
            return;
        }
        const historyClose = event.target.closest?.("[data-close-entry-history]");
        if (historyClose) {
            event.preventDefault();
            const history = historyClose.closest("[data-entry-history]");
            if (history) history.hidden = true;
            return;
        }
        if (event.target.closest?.("[data-close-correction]")) {
            event.preventDefault();
            closeCorrection();
            return;
        }
        if (event.target.closest?.("[data-close-cancellation]")) {
            event.preventDefault();
            closeCancellation();
            return;
        }
        if (event.target.closest?.("[data-open-journal-settings]")) {
            event.preventDefault();
            document.getElementById("journal-display-settings")?.showModal();
            return;
        }
        if (event.target.closest?.("[data-close-journal-settings]")) {
            event.preventDefault();
            document.getElementById("journal-display-settings")?.close();
            return;
        }
        if (floatingMenu && !event.target.closest?.("[data-entry-actions-menu]")) {
            closeActionMenus();
        }
    });

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
        } else if (error) {
            error.hidden = true;
            error.textContent = "";
        }
    });

    [registerDialog, correctionDialog, cancellationDialog].forEach((dialog) => {
        dialog?.addEventListener("click", (event) => {
            if (event.target !== dialog) return;
            if (dialog === registerDialog) closeRegisterDialog();
            if (dialog === correctionDialog) closeCorrection();
            if (dialog === cancellationDialog) closeCancellation();
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        if (floatingMenu) {
            closeActionMenus();
            return;
        }
        if (registerDialog?.open) closeRegisterDialog();
        else if (correctionDialog?.open) closeCorrection();
        else if (cancellationDialog?.open) closeCancellation();
        else if (workspace?.classList.contains("is-selection-mode")) setSelectionMode(false);
    });

    window.addEventListener("resize", closeActionMenus);
    document.addEventListener("scroll", (event) => {
        if (!floatingMenu || floatingMenu.menu.contains(event.target)) return;
        closeActionMenus();
    }, true);

    initializeCorrectionEditor();
    setSelectionMode(false);
})();
