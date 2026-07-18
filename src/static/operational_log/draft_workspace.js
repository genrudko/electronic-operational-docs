(() => {
    "use strict";

    const workspace = document.querySelector("[data-draft-workspace]");
    if (!workspace) {
        return;
    }

    const autosaveDelay = Number.parseInt(
        workspace.dataset.autosaveDelay || "700",
        10,
    );
    const timers = new WeakMap();
    const controllers = new WeakMap();
    const rowStore = workspace.querySelector("[data-row-store]");
    const rows = Array.from(
        workspace.querySelectorAll("[data-draft-card]"),
    );
    const addDraftForm = workspace.querySelector(
        "[data-add-draft-form]",
    );
    const defaultEntryDate = (
        workspace.dataset.defaultEntryDate || ""
    );
    const defaultEntryDateIso = (
        workspace.dataset.defaultEntryDateIso || ""
    );

    const leftShell = workspace.querySelector(
        '[data-page-shell="left"]',
    );
    const rightShell = workspace.querySelector(
        '[data-page-shell="right"]',
    );
    const leftBody = workspace.querySelector(
        '[data-page-body="left"]',
    );
    const rightBody = workspace.querySelector(
        '[data-page-body="right"]',
    );
    const leftDate = workspace.querySelector(
        '[data-page-date="left"]',
    );
    const rightDate = workspace.querySelector(
        '[data-page-date="right"]',
    );
    const leftNumber = workspace.querySelector(
        '[data-page-number="left"]',
    );
    const rightNumber = workspace.querySelector(
        '[data-page-number="right"]',
    );

    const previousButton = workspace.querySelector(
        "[data-page-prev]",
    );
    const nextButton = workspace.querySelector(
        "[data-page-next]",
    );
    const pageInput = workspace.querySelector(
        "[data-page-input]",
    );
    const pageTotal = workspace.querySelector(
        "[data-page-total]",
    );
    const pageButtons = workspace.querySelector(
        "[data-page-buttons]",
    );
    const pageRange = workspace.querySelector(
        "[data-page-range]",
    );

    const searchInput = workspace.querySelector(
        "[data-draft-search]",
    );
    const filterSelect = workspace.querySelector(
        "[data-draft-filter]",
    );

    const drawer = workspace.querySelector("[data-view-drawer]");
    const recordPresetButtons = Array.from(
        workspace.querySelectorAll("[data-records-preset]"),
    );
    const customRecordsInput = workspace.querySelector(
        "[data-records-custom]",
    );
    const applyCustomRecordsButton = workspace.querySelector(
        "[data-apply-custom-records]",
    );
    const recordSummary = workspace.querySelector(
        "[data-records-summary]",
    );

    let pages = [];
    let currentPage = 0;
    let paginationTimer = null;
    let resizeTimer = null;
    let activeColumnDrag = null;
    let activeDraftForm = null;
    let compositionDepth = 0;
    let paginationPending = false;
    let inlineCreation = null;
    let inlineCreationTimer = null;
    let currentColumnWidths = {
        time: 14,
        content: 66,
        remarks: 20,
    };
    let recordSetting = normalizeRecordSetting(
        readPreference(
            "eod-draft-records-per-page",
            "15",
        ),
    );
    let viewMode = readPreference(
        "eod-draft-view-mode",
        "single",
    );

    function readPreference(key, fallback) {
        try {
            return window.localStorage.getItem(key) || fallback;
        } catch (error) {
            return fallback;
        }
    }

    function writePreference(key, value) {
        try {
            window.localStorage.setItem(key, String(value));
        } catch (error) {
            // Настройка действует в текущей вкладке.
        }
    }

    function clamp(value, minimum, maximum) {
        return Math.min(maximum, Math.max(minimum, value));
    }

    function normalizeRecordSetting(value) {
        if (String(value).toLowerCase() === "auto") {
            return "auto";
        }
        const numeric = Number.parseInt(String(value), 10);
        if (!Number.isFinite(numeric)) {
            return "15";
        }
        return String(clamp(numeric, 5, 50));
    }

    function automaticRecordCapacity() {
        const chromeReserve = viewMode === "spread" ? 310 : 280;
        const usableHeight = Math.max(
            520,
            window.innerHeight - chromeReserve,
        );
        return clamp(
            Math.floor(usableHeight / 58),
            8,
            20,
        );
    }

    function selectedRecordCapacity() {
        if (recordSetting === "auto") {
            return automaticRecordCapacity();
        }
        return clamp(
            Number.parseInt(recordSetting, 10),
            5,
            50,
        );
    }

    function isDraftEditing() {
        if (compositionDepth > 0) {
            return true;
        }
        if (!activeDraftForm) {
            return false;
        }
        const active = document.activeElement;
        return Boolean(active && activeDraftForm.contains(active));
    }

    function updateRecordControls() {
        const capacity = selectedRecordCapacity();

        recordPresetButtons.forEach((button) => {
            const active = (
                button.dataset.recordsPreset === recordSetting
            );
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });

        if (recordSetting !== "auto") {
            customRecordsInput.value = recordSetting;
        }

        recordSummary.textContent = (
            recordSetting === "auto"
                ? `Авто · ${capacity} записей`
                : `${capacity} записей`
        );
    }

    function setRecordSetting(value) {
        recordSetting = normalizeRecordSetting(value);
        writePreference(
            "eod-draft-records-per-page",
            recordSetting,
        );
        currentPage = 0;
        updateRecordControls();
        schedulePagination(20);
    }

    function markPaginationPending() {
        paginationPending = true;
    }

    function flushDeferredPagination() {
        if (!paginationPending || isDraftEditing()) {
            return;
        }
        schedulePagination(80);
    }

    function statusNode(form) {
        return form.querySelector("[data-save-status]");
    }

    function setStatus(form, text, state) {
        const node = statusNode(form);
        if (!node) {
            return;
        }
        node.textContent = text;
        node.classList.remove(
            "is-dirty",
            "is-saving",
            "is-saved",
            "is-error",
            "is-conflict",
        );
        node.classList.add(state);
    }

    function normalizeTime(value) {
        const digits = value.replace(/\D/g, "").slice(0, 4);
        if (!digits) {
            return "";
        }
        const padded = digits.padStart(4, "0");
        const hours = Number.parseInt(padded.slice(0, 2), 10);
        const minutes = Number.parseInt(padded.slice(2, 4), 10);
        if (hours > 23 || minutes > 59) {
            return null;
        }
        return (
            `${String(hours).padStart(2, "0")}:`
            + `${String(minutes).padStart(2, "0")}`
        );
    }

    function normalizeDate(value) {
        const digits = value.replace(/\D/g, "").slice(0, 8);
        if (![4, 6, 8].includes(digits.length)) {
            return null;
        }

        const today = new Date();
        const day = digits.slice(0, 2);
        const month = digits.slice(2, 4);
        let year = String(today.getFullYear());

        if (digits.length === 6) {
            year = `20${digits.slice(4, 6)}`;
        }
        if (digits.length === 8) {
            year = digits.slice(4, 8);
        }

        const parsed = new Date(
            `${year}-${month}-${day}T00:00:00`,
        );
        if (
            Number.isNaN(parsed.getTime())
            || parsed.getFullYear() !== Number(year)
            || parsed.getMonth() + 1 !== Number(month)
            || parsed.getDate() !== Number(day)
        ) {
            return null;
        }
        return `${day}.${month}.${year}`;
    }

    function syncHiddenDateTime(form) {
        const hidden = form.querySelector("[data-event-at]");
        const time = form.querySelector("[data-quick-time]");
        const dateButton = form.querySelector("[data-date-button]");
        if (!hidden || !time || !dateButton) {
            return false;
        }

        const normalizedTime = normalizeTime(time.value);
        const normalizedDate = normalizeDate(
            dateButton.dataset.currentDate || "",
        );
        if (!normalizedTime || !normalizedDate) {
            return false;
        }

        const [day, month, year] = normalizedDate.split(".");
        time.value = normalizedTime;
        hidden.value = (
            `${year}-${month}-${day}T${normalizedTime}`
        );
        dateButton.dataset.currentDate = normalizedDate;

        const row = form.closest("[data-draft-card]");
        if (row) {
            row.dataset.entryDate = `${year}-${month}-${day}`;
            row.dataset.entryDateLabel = normalizedDate;
        }
        return true;
    }

    function autoGrow(textarea) {
        if (!textarea) {
            return;
        }
        textarea.style.height = "auto";
        textarea.style.height = (
            `${Math.max(36, textarea.scrollHeight)}px`
        );
    }

    async function save(form) {
        if (!syncHiddenDateTime(form)) {
            setStatus(form, "Некорректные дата или время", "is-error");
            return;
        }

        const previous = controllers.get(form);
        if (previous) {
            previous.abort();
        }

        const controller = new AbortController();
        controllers.set(form, controller);
        setStatus(form, "…", "is-saving");

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                signal: controller.signal,
            });
            const payload = await response.json();

            if (response.status === 409 && payload.conflict) {
                form.dataset.conflict = "true";
                setStatus(form, "Конфликт версии", "is-conflict");
                return;
            }
            if (!response.ok || !payload.ok) {
                setStatus(form, "Не сохранено", "is-error");
                return;
            }

            const versionInput = form.querySelector(
                "[data-draft-version]",
            );
            const versionLabel = form.querySelector(
                "[data-version-label]",
            );
            if (versionInput) {
                versionInput.value = String(payload.version);
            }
            if (versionLabel) {
                versionLabel.textContent = String(payload.version);
            }

            delete form.dataset.conflict;
            setStatus(
                form,
                `✓ ${payload.saved_at}`,
                "is-saved",
            );
            flushDeferredPagination();
        } catch (error) {
            if (error.name !== "AbortError") {
                setStatus(form, "Нет связи", "is-error");
            }
        } finally {
            if (controllers.get(form) === controller) {
                controllers.delete(form);
            }
        }
    }

    function scheduleSave(form) {
        if (form.dataset.conflict === "true") {
            return;
        }

        const activeTimer = timers.get(form);
        if (activeTimer) {
            window.clearTimeout(activeTimer);
        }

        setStatus(form, "●", "is-dirty");
        const timer = window.setTimeout(() => {
            timers.delete(form);
            void save(form);
        }, autosaveDelay);
        timers.set(form, timer);
    }

    function rowText(row) {
        const textarea = row.querySelector("textarea");
        return (
            `${row.textContent} ${textarea?.value || ""}`
        ).toLowerCase();
    }

    function filteredRows() {
        const query = (
            searchInput?.value || ""
        ).trim().toLowerCase();
        const filter = filterSelect?.value || "all";

        return rows.filter((row) => {
            const filled = (
                row.dataset.entryFilled === "true"
            );
            const matchesQuery = (
                !query || rowText(row).includes(query)
            );
            const matchesFilter = (
                filter === "all"
                || (filter === "filled" && filled)
                || (filter === "empty" && !filled)
            );
            return matchesQuery && matchesFilter;
        });
    }

    function restoreRowsToStore() {
        rows.forEach((row) => {
            row.classList.remove("is-page-first");
            rowStore.append(row);
        });
        leftBody.replaceChildren();
        rightBody.replaceChildren();
    }

    function paginateByRecordCount(force = false) {
        if (!force && isDraftEditing()) {
            markPaginationPending();
            return;
        }

        paginationPending = false;
        restoreRowsToStore();

        const visibleRows = filteredRows();
        const capacity = selectedRecordCapacity();
        updateRecordControls();
        pages = [];

        for (
            let start = 0;
            start < visibleRows.length;
            start += capacity
        ) {
            const pageRows = visibleRows.slice(
                start,
                start + capacity,
            );

            pageRows.forEach((row, index) => {
                row.hidden = false;
                row.classList.toggle(
                    "is-page-first",
                    index === 0,
                );
            });

            pages.push({
                rows: pageRows,
                capacity,
            });
        }

        rows
            .filter((row) => !visibleRows.includes(row))
            .forEach((row) => {
                row.hidden = true;
                row.classList.remove("is-page-first");
                rowStore.append(row);
            });

        if (pages.length === 0) {
            pages = [{
                rows: [],
                capacity,
            }];
        }

        const pagesPerScreen = (
            viewMode === "spread" ? 2 : 1
        );
        const lastStart = Math.max(
            0,
            pages.length - pagesPerScreen,
        );
        currentPage = Math.min(currentPage, lastStart);

        if (viewMode === "spread") {
            currentPage = (
                Math.floor(currentPage / 2) * 2
            );
        }

        renderCurrentPages();
    }

    function isoDateToLabel(value) {
        const match = String(value || "").match(
            /^(\d{4})-(\d{2})-(\d{2})$/,
        );
        if (!match) {
            return "";
        }
        return `${match[3]}.${match[2]}.${match[1]}`;
    }

    function activeRowIdentifiers() {
        return new Set(
            rows.map((row) => row.dataset.draftId),
        );
    }

    function parseCreatedDraftRow(html, knownIds) {
        const documentFragment = new DOMParser().parseFromString(
            html,
            "text/html",
        );
        const candidates = Array.from(
            documentFragment.querySelectorAll(
                "[data-draft-card]",
            ),
        ).filter(
            (row) => !knownIds.has(row.dataset.draftId),
        );
        return candidates.at(-1) || null;
    }

    function cancelInlineCreation() {
        if (!inlineCreation || inlineCreation.materializing) {
            return;
        }
        const { record, dateLabel, dateIso } = inlineCreation;
        inlineCreation = null;
        if (inlineCreationTimer) {
            window.clearTimeout(inlineCreationTimer);
            inlineCreationTimer = null;
        }
        const replacement = createBlankRecord(
            dateLabel,
            dateIso,
        );
        record.replaceWith(replacement);
    }

    function inlineCreationHasMeaningfulInput(state) {
        return Boolean(
            normalizeTime(state.timeInput.value)
            || state.contentInput.value.trim(),
        );
    }

    function queueInlineMaterialization() {
        if (!inlineCreation || inlineCreation.materializing) {
            return;
        }
        if (inlineCreationTimer) {
            window.clearTimeout(inlineCreationTimer);
        }
        inlineCreationTimer = window.setTimeout(() => {
            inlineCreationTimer = null;
            if (
                inlineCreation
                && inlineCreationHasMeaningfulInput(
                    inlineCreation,
                )
            ) {
                void materializeInlineDraft(true);
            }
        }, 320);
    }

    async function materializeInlineDraft(focusContent) {
        const state = inlineCreation;
        if (!state || state.materializing) {
            return;
        }

        const normalizedTime = normalizeTime(
            state.timeInput.value,
        );
        const content = state.contentInput.value;

        if (!normalizedTime) {
            state.status.textContent = "Укажите корректное время";
            state.timeInput.focus();
            state.timeInput.select();
            return;
        }

        state.materializing = true;
        state.record.classList.add("is-materializing");
        state.status.textContent = "Создание…";

        const dateIso = (
            state.dateIso || defaultEntryDateIso
        );
        const dateLabel = (
            state.dateLabel
            || isoDateToLabel(dateIso)
            || defaultEntryDate
        );
        if (!/^\d{4}-\d{2}-\d{2}$/.test(dateIso)) {
            state.materializing = false;
            state.record.classList.remove("is-materializing");
            state.status.textContent = (
                "Не удалось определить дату записи"
            );
            return;
        }

        const knownIds = activeRowIdentifiers();
        const formData = new FormData(addDraftForm);
        formData.set(
            "event_at",
            `${dateIso}T${normalizedTime}`,
        );

        try {
            const response = await fetch(addDraftForm.action, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const html = await response.text();

            if (!response.ok) {
                throw new Error("create_failed");
            }

            const parsedRow = parseCreatedDraftRow(
                html,
                knownIds,
            );
            if (!parsedRow) {
                throw new Error("created_row_not_found");
            }

            const row = document.importNode(parsedRow, true);
            const form = row.querySelector("[data-draft-form]");
            const timeInput = form.querySelector(
                "[data-quick-time]",
            );
            const contentInput = form.querySelector(
                "[data-auto-grow]",
            );
            const hiddenDateTime = form.querySelector(
                "[data-event-at]",
            );
            const dateButton = form.querySelector(
                "[data-date-button]",
            );
            timeInput.value = normalizedTime;
            contentInput.value = content;
            row.dataset.entryFilled = (
                content.trim() ? "true" : "false"
            );

            hiddenDateTime.value = (
                `${dateIso}T${normalizedTime}`
            );
            dateButton.dataset.currentDate = dateLabel;
            row.dataset.entryDate = dateIso;
            row.dataset.entryDateLabel = dateLabel;

            const serverDateMarker = row.querySelector(
                "[data-inline-date]",
            );
            if (serverDateMarker) {
                serverDateMarker.remove();
            }

            state.record.replaceWith(row);
            rows.push(row);
            bindDraftRow(row);
            bindEditorCommands(row);
            inlineCreation = null;
            markPaginationPending();

            activeDraftForm = form;
            form.classList.add("has-focus");
            autoGrow(contentInput);

            if (focusContent) {
                contentInput.focus();
                contentInput.setSelectionRange(
                    contentInput.value.length,
                    contentInput.value.length,
                );
            }

            await save(form);
        } catch (error) {
            state.materializing = false;
            state.record.classList.remove("is-materializing");
            state.status.textContent = (
                "Не удалось создать запись. Повторите."
            );
        }
    }

    function beginInlineCreation(
        record,
        dateLabel,
        dateIso,
    ) {
        if (inlineCreation) {
            if (inlineCreation.record === record) {
                inlineCreation.timeInput.focus();
                return;
            }
            if (
                inlineCreationHasMeaningfulInput(inlineCreation)
            ) {
                inlineCreation.timeInput.focus();
                return;
            }
            cancelInlineCreation();
        }

        const timeCell = document.createElement("div");
        timeCell.className = "draft-inline-create-time";
        const timeInput = document.createElement("input");
        timeInput.type = "text";
        timeInput.inputMode = "numeric";
        timeInput.autocomplete = "off";
        timeInput.placeholder = "ЧЧ:ММ";
        timeInput.value = "";
        timeInput.setAttribute(
            "aria-label",
            "Время новой записи",
        );
        timeCell.append(timeInput);

        const contentCell = document.createElement("div");
        contentCell.className = "draft-inline-create-content";
        const contentInput = document.createElement("textarea");
        contentInput.rows = 1;
        contentInput.maxLength = 20000;
        contentInput.placeholder = "Содержание записи…";
        contentInput.setAttribute(
            "aria-label",
            "Содержание новой записи",
        );
        const status = document.createElement("span");
        status.className = "draft-inline-create-status";
        status.textContent = "Esc — отмена";
        contentCell.append(contentInput, status);

        const visasCell = document.createElement("div");
        visasCell.className = "draft-inline-create-visas";

        record.replaceChildren(
            timeCell,
            contentCell,
            visasCell,
        );
        record.classList.add("is-inline-creating");
        record.removeAttribute("aria-hidden");

        inlineCreation = {
            record,
            dateLabel: dateLabel || defaultEntryDate,
            dateIso: dateIso || defaultEntryDateIso,
            timeInput,
            contentInput,
            status,
            materializing: false,
        };

        const cancelOnEscape = (event) => {
            if (event.key === "Escape") {
                event.preventDefault();
                cancelInlineCreation();
            }
        };

        timeInput.addEventListener("keydown", (event) => {
            cancelOnEscape(event);
            if (
                event.key === "Enter"
                || event.key === "Tab"
            ) {
                const normalized = normalizeTime(
                    timeInput.value,
                );
                if (!normalized) {
                    event.preventDefault();
                    status.textContent = (
                        "Некорректное время"
                    );
                    return;
                }
                timeInput.value = normalized;
                event.preventDefault();
                contentInput.focus();
            }
        });

        contentInput.addEventListener(
            "keydown",
            cancelOnEscape,
        );
        contentInput.addEventListener("input", () => {
            contentInput.style.height = "auto";
            contentInput.style.height = (
                `${Math.max(
                    36,
                    contentInput.scrollHeight,
                )}px`
            );
            if (contentInput.value.trim()) {
                queueInlineMaterialization();
            }
        });

        record.addEventListener("focusout", () => {
            window.setTimeout(() => {
                if (
                    !inlineCreation
                    || inlineCreation.record !== record
                    || record.contains(document.activeElement)
                ) {
                    return;
                }
                if (
                    inlineCreationHasMeaningfulInput(
                        inlineCreation,
                    )
                ) {
                    void materializeInlineDraft(false);
                } else {
                    cancelInlineCreation();
                }
            }, 180);
        });

        window.requestAnimationFrame(() => {
            timeInput.focus();
            timeInput.select();
        });
    }

    function createBlankRecord(dateLabel, dateIso) {
        const record = document.createElement("div");
        record.className = "draft-empty-record";
        record.dataset.blankRecord = "true";
        record.dataset.entryDateLabel = (
            dateLabel || defaultEntryDate
        );
        record.dataset.entryDate = (
            dateIso || defaultEntryDateIso
        );

        const timeCell = document.createElement("span");
        timeCell.className = "draft-empty-record-time";
        timeCell.dataset.inlineCreateTrigger = "true";
        timeCell.tabIndex = 0;
        timeCell.setAttribute("role", "button");
        timeCell.setAttribute(
            "aria-label",
            "Добавить запись в эту строку",
        );
        timeCell.title = (
            "Двойной щелчок — добавить запись"
        );

        timeCell.addEventListener("dblclick", () => {
            beginInlineCreation(
                record,
                record.dataset.entryDateLabel,
                record.dataset.entryDate,
            );
        });
        timeCell.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                beginInlineCreation(
                    record,
                    record.dataset.entryDateLabel,
                    record.dataset.entryDate,
                );
            }
        });

        record.append(
            timeCell,
            document.createElement("span"),
            document.createElement("span"),
        );
        return record;
    }

    function appendBlankRecords(
        body,
        count,
        dateLabel,
        dateIso,
    ) {
        for (let index = 0; index < count; index += 1) {
            body.append(
                createBlankRecord(dateLabel, dateIso),
            );
        }
    }

    function renderPage(
        shell,
        body,
        dateNode,
        numberNode,
        pageIndex,
    ) {
        body.replaceChildren();
        shell.classList.remove("is-empty-page");
        shell.style.removeProperty("--draft-page-body-height");

        const pageData = pages[pageIndex];
        const capacity = (
            pageData?.capacity || selectedRecordCapacity()
        );

        if (!pageData) {
            shell.classList.add("is-empty-page");
            dateNode.textContent = "";
            numberNode.textContent = "";
            appendBlankRecords(
                body,
                capacity,
                defaultEntryDate,
                defaultEntryDateIso,
            );
            return;
        }

        pageData.rows.forEach((row) => {
            row.hidden = false;
            body.append(row);
            autoGrow(row.querySelector("[data-auto-grow]"));
        });

        dateNode.textContent = (
            pageData.rows[0]?.dataset.entryDateLabel || ""
        );

        const lastRow = pageData.rows.at(-1);
        const blankDateLabel = (
            lastRow?.dataset.entryDateLabel
            || defaultEntryDate
        );
        const blankDateIso = (
            lastRow?.dataset.entryDate
            || defaultEntryDateIso
        );
        appendBlankRecords(
            body,
            Math.max(
                0,
                capacity - pageData.rows.length,
            ),
            blankDateLabel,
            blankDateIso,
        );

        numberNode.textContent = `— ${pageIndex + 1} —`;
    }

    function appendPageButton(label, pageNumber, active) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = String(label);
        button.className = "draft-page-number-button";
        button.classList.toggle("is-active", active);
        button.addEventListener("click", () => {
            goToPage(pageNumber);
        });
        pageButtons.append(button);
    }

    function appendEllipsis() {
        const span = document.createElement("span");
        span.className = "draft-page-ellipsis";
        span.textContent = "…";
        pageButtons.append(span);
    }

    function buildPageNumbers() {
        pageButtons.replaceChildren();

        const total = pages.length;
        const activePages = new Set(
            viewMode === "spread"
                ? [currentPage + 1, currentPage + 2]
                : [currentPage + 1],
        );

        const wanted = new Set([1, total]);
        for (
            let number = Math.max(1, currentPage - 1);
            number <= Math.min(total, currentPage + 4);
            number += 1
        ) {
            wanted.add(number);
        }

        const ordered = Array.from(wanted).sort(
            (left, right) => left - right,
        );
        let previous = 0;

        ordered.forEach((number) => {
            if (number - previous > 1) {
                appendEllipsis();
            }
            appendPageButton(
                number,
                number,
                activePages.has(number),
            );
            previous = number;
        });
    }

    function renderCurrentPages() {
        rows.forEach((row) => rowStore.append(row));

        workspace.dataset.viewMode = viewMode;
        rightShell.hidden = viewMode !== "spread";

        renderPage(
            leftShell,
            leftBody,
            leftDate,
            leftNumber,
            currentPage,
        );

        if (viewMode === "spread") {
            renderPage(
                rightShell,
                rightBody,
                rightDate,
                rightNumber,
                currentPage + 1,
            );
        } else {
            rightBody.replaceChildren();
        }

        const total = pages.length;
        const endPage = Math.min(
            total,
            currentPage + (viewMode === "spread" ? 2 : 1),
        );

        pageInput.max = String(total);
        pageInput.value = String(currentPage + 1);
        pageTotal.textContent = String(total);
        pageRange.textContent = (
            viewMode === "spread" && endPage > currentPage + 1
                ? `Страницы ${currentPage + 1}–${endPage} из ${total}`
                : `Страница ${currentPage + 1} из ${total}`
        );

        previousButton.disabled = currentPage === 0;
        nextButton.disabled = endPage >= total;
        buildPageNumbers();
    }

    function goToPage(pageNumber) {
        const total = pages.length;
        const normalized = Math.min(
            total,
            Math.max(1, Number(pageNumber) || 1),
        );

        currentPage = normalized - 1;
        if (viewMode === "spread") {
            currentPage = (
                Math.floor(currentPage / 2) * 2
            );
        }
        renderCurrentPages();
    }

    function schedulePagination(delay = 220) {
        markPaginationPending();

        if (isDraftEditing()) {
            return;
        }

        if (paginationTimer) {
            window.clearTimeout(paginationTimer);
        }

        paginationTimer = window.setTimeout(() => {
            paginationTimer = null;
            paginateByRecordCount(true);
        }, delay);
    }

    function updateColumnWidths(
        timeValue,
        remarksValue,
        persist = true,
    ) {
        let time = clamp(Number(timeValue) || 14, 10, 25);
        let remarks = clamp(
            Number(remarksValue) || 20,
            15,
            30,
        );

        if (100 - time - remarks < 45) {
            if (activeColumnDrag?.kind === "time") {
                time = 100 - remarks - 45;
            } else {
                remarks = 100 - time - 45;
            }
        }

        const content = 100 - time - remarks;
        currentColumnWidths = {
            time,
            content,
            remarks,
        };

        workspace.style.setProperty(
            "--draft-time-column",
            `${time}%`,
        );
        workspace.style.setProperty(
            "--draft-content-column",
            `${content}%`,
        );
        workspace.style.setProperty(
            "--draft-remarks-column",
            `${remarks}%`,
        );

        if (persist) {
            writePreference("eod-draft-column-time", time);
            writePreference(
                "eod-draft-column-remarks",
                remarks,
            );
        }

        schedulePagination();
    }

    function startColumnResize(event, handle) {
        const header = handle.closest(".draft-table-header");
        const kind = handle.dataset.columnResizer;
        if (!header || !kind) {
            return;
        }

        event.preventDefault();
        handle.setPointerCapture(event.pointerId);
        activeColumnDrag = {
            kind,
            handle,
            pointerId: event.pointerId,
            header,
        };
        document.body.classList.add("is-resizing-draft-columns");
    }

    function moveColumnResize(event) {
        if (
            !activeColumnDrag
            || event.pointerId !== activeColumnDrag.pointerId
        ) {
            return;
        }

        const rect = (
            activeColumnDrag.header.getBoundingClientRect()
        );
        const position = clamp(
            ((event.clientX - rect.left) / rect.width) * 100,
            0,
            100,
        );

        const currentTime = currentColumnWidths.time;
        const currentRemarks = currentColumnWidths.remarks;

        if (activeColumnDrag.kind === "time") {
            updateColumnWidths(
                clamp(position, 10, 25),
                currentRemarks,
            );
        } else {
            updateColumnWidths(
                currentTime,
                clamp(100 - position, 15, 30),
            );
        }
    }

    function stopColumnResize(event) {
        if (
            !activeColumnDrag
            || event.pointerId !== activeColumnDrag.pointerId
        ) {
            return;
        }

        activeColumnDrag.handle.releasePointerCapture(
            event.pointerId,
        );
        activeColumnDrag = null;
        document.body.classList.remove(
            "is-resizing-draft-columns",
        );
        schedulePagination();
    }

    function updateOverlayOffsets() {
        const candidates = Array.from(
            document.querySelectorAll(
                "body > header,"
                + " body > nav,"
                + " [data-app-shell-header],"
                + " .site-header,"
                + " .app-header",
            ),
        );

        const topHeader = candidates.find((element) => {
            const rect = element.getBoundingClientRect();
            const style = window.getComputedStyle(element);
            return (
                rect.height > 0
                && rect.top <= 2
                && rect.width >= window.innerWidth * 0.6
                && ["fixed", "sticky"].includes(style.position)
            );
        });

        const offset = topHeader
            ? Math.max(
                0,
                Math.ceil(topHeader.getBoundingClientRect().bottom),
            )
            : 50;

        workspace.style.setProperty(
            "--draft-overlay-top",
            `${offset}px`,
        );
    }

    function openDrawer() {
        updateOverlayOffsets();
        drawer.hidden = false;
        document.body.classList.add(
            "draft-view-drawer-visible",
        );
    }

    function closeDrawer() {
        drawer.hidden = true;
        document.body.classList.remove(
            "draft-view-drawer-visible",
        );
    }

    function bindEditorCommands(scope) {
        scope
            .querySelectorAll("[data-editor-command]")
            .forEach((button) => {
                if (button.dataset.bound === "true") {
                    return;
                }
                button.dataset.bound = "true";
                button.addEventListener("click", () => {
                    button
                        .closest("[data-draft-form]")
                        ?.querySelector("textarea")
                        ?.focus();
                });
            });
    }

    function bindDraftRow(row) {
        if (row.dataset.bound === "true") {
            return;
        }
        row.dataset.bound = "true";

        const form = row.querySelector("[data-draft-form]");
        const textarea = form.querySelector("[data-auto-grow]");
        const timeInput = form.querySelector("[data-quick-time]");
        const dateButton = form.querySelector("[data-date-button]");

        autoGrow(textarea);

        form.addEventListener("focusin", () => {
            activeDraftForm = form;
            form.classList.add("has-focus");
        });

        form.addEventListener("focusout", () => {
            window.setTimeout(() => {
                if (form.contains(document.activeElement)) {
                    return;
                }
                form.classList.remove("has-focus");
                if (activeDraftForm === form) {
                    activeDraftForm = null;
                }
                flushDeferredPagination();
            }, 180);
        });

        textarea.addEventListener("compositionstart", () => {
            compositionDepth += 1;
            activeDraftForm = form;
        });

        textarea.addEventListener("compositionend", () => {
            compositionDepth = Math.max(
                0,
                compositionDepth - 1,
            );
            autoGrow(textarea);
            markPaginationPending();
            scheduleSave(form);
        });

        textarea.addEventListener("input", () => {
            autoGrow(textarea);
            row.dataset.entryFilled = (
                textarea.value.trim() ? "true" : "false"
            );
            markPaginationPending();
            scheduleSave(form);
        });

        timeInput.addEventListener("focus", () => {
            timeInput.select();
        });
        timeInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                timeInput.blur();
                textarea.focus();
            }
        });
        timeInput.addEventListener("blur", () => {
            const normalized = normalizeTime(timeInput.value);
            if (!normalized) {
                setStatus(
                    form,
                    "Некорректное время",
                    "is-error",
                );
                return;
            }
            timeInput.value = normalized;
            scheduleSave(form);
        });

        dateButton.addEventListener("click", () => {
            const entered = window.prompt(
                "Дата: 1707, 170726 или 17072026",
                dateButton.dataset.currentDate || "",
            );
            if (entered === null) {
                return;
            }

            const normalized = normalizeDate(entered);
            if (!normalized) {
                setStatus(
                    form,
                    "Некорректная дата",
                    "is-error",
                );
                return;
            }

            dateButton.dataset.currentDate = normalized;
            syncHiddenDateTime(form);
            markPaginationPending();
            scheduleSave(form);
        });

        form.addEventListener("submit", (event) => {
            const submitter = event.submitter;
            if (
                submitter?.formAction
                && submitter.formAction !== form.action
            ) {
                return;
            }
            event.preventDefault();
            void save(form);
        });
    }

    rows.forEach((row) => {
        bindDraftRow(row);
        bindEditorCommands(row);
    });

    workspace
        .querySelectorAll("[data-view-mode]")
        .forEach((button) => {
            const active = (
                button.dataset.viewMode === viewMode
            );
            button.classList.toggle("is-active", active);
            button.setAttribute(
                "aria-pressed",
                String(active),
            );

            button.addEventListener("click", () => {
                viewMode = button.dataset.viewMode;
                writePreference(
                    "eod-draft-view-mode",
                    viewMode,
                );

                workspace
                    .querySelectorAll("[data-view-mode]")
                    .forEach((item) => {
                        const itemActive = (
                            item.dataset.viewMode === viewMode
                        );
                        item.classList.toggle(
                            "is-active",
                            itemActive,
                        );
                        item.setAttribute(
                            "aria-pressed",
                            String(itemActive),
                        );
                    });

                currentPage = 0;
                window.requestAnimationFrame(
                    paginateByRecordCount,
                );
            });
        });

    workspace
        .querySelectorAll("[data-column-resizer]")
        .forEach((handle) => {
            handle.addEventListener("pointerdown", (event) => {
                startColumnResize(event, handle);
            });
            handle.addEventListener(
                "pointermove",
                moveColumnResize,
            );
            handle.addEventListener(
                "pointerup",
                stopColumnResize,
            );
            handle.addEventListener(
                "pointercancel",
                stopColumnResize,
            );
            handle.addEventListener("dblclick", (event) => {
                event.preventDefault();
                updateColumnWidths(14, 20);
            });
        });

    previousButton.addEventListener("click", () => {
        currentPage = Math.max(
            0,
            currentPage - (viewMode === "spread" ? 2 : 1),
        );
        renderCurrentPages();
    });

    nextButton.addEventListener("click", () => {
        currentPage = Math.min(
            pages.length - 1,
            currentPage + (viewMode === "spread" ? 2 : 1),
        );
        if (viewMode === "spread") {
            currentPage = (
                Math.floor(currentPage / 2) * 2
            );
        }
        renderCurrentPages();
    });

    pageInput.addEventListener("change", () => {
        goToPage(pageInput.value);
    });
    pageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            goToPage(pageInput.value);
        }
    });

    searchInput.addEventListener("input", () => {
        currentPage = 0;
        schedulePagination();
    });
    filterSelect.addEventListener("change", () => {
        currentPage = 0;
        schedulePagination();
    });

    recordPresetButtons.forEach((button) => {
        button.addEventListener("click", () => {
            setRecordSetting(button.dataset.recordsPreset);
        });
    });

    applyCustomRecordsButton.addEventListener("click", () => {
        setRecordSetting(customRecordsInput.value);
    });

    customRecordsInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            setRecordSetting(customRecordsInput.value);
        }
    });

    workspace
        .querySelector("[data-open-view-drawer]")
        .addEventListener("click", openDrawer);
    workspace
        .querySelector("[data-close-view-drawer]")
        .addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !drawer.hidden) {
            closeDrawer();
        }
    });

    window.addEventListener("resize", () => {
        if (resizeTimer) {
            window.clearTimeout(resizeTimer);
        }
        resizeTimer = window.setTimeout(() => {
            resizeTimer = null;
            updateOverlayOffsets();
            updateRecordControls();
            schedulePagination(20);
        }, 180);
    });

    window.addEventListener("beforeunload", (event) => {
        const pending = workspace.querySelector(
            ".draft-save-status.is-dirty,"
            + " .draft-save-status.is-saving,"
            + " .draft-save-status.is-error",
        );
        if (!pending) {
            return;
        }
        event.preventDefault();
        event.returnValue = "";
    });

    updateOverlayOffsets();
    updateRecordControls();

    updateColumnWidths(
        readPreference("eod-draft-column-time", "14"),
        readPreference("eod-draft-column-remarks", "20"),
        false,
    );

    window.requestAnimationFrame(() => {
        paginateByRecordCount(true);
    });
})();
