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
    const shiftStartAt = workspace.dataset.shiftStart || "";
    const shiftEndAt = workspace.dataset.shiftEnd || "";

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
    const quickDisplayForm = workspace.querySelector(
        "[data-quick-display-form]",
    );
    const quickSettingStatus = workspace.querySelector(
        "[data-quick-setting-status]",
    );
    const simplifiedTimeToggle = workspace.querySelector(
        "[data-simplified-time-toggle]",
    );
    const simplifiedTimeLabel = workspace.querySelector(
        "[data-simplified-time-label]",
    );
    const themeChoiceButtons = Array.from(
        workspace.querySelectorAll("[data-theme-choice]"),
    );
    const pageWidthChoiceButtons = Array.from(
        workspace.querySelectorAll("[data-page-width-choice]"),
    );
    const typographySizeButtons = Array.from(
        workspace.querySelectorAll(
            "[data-typography-target][data-typography-size]",
        ),
    );
    const typographyPresetButtons = Array.from(
        workspace.querySelectorAll("[data-typography-preset]"),
    );
    const journalTitleNode = document.querySelector(
        ".shift-book-header[data-journal-title-size]",
    );
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
    let editorOverlayActive = false;
    let inlineCreation = null;
    let inlineCreationTimer = null;
    let activeDateEditor = null;
    let quickSettingsController = null;
    let pendingRemoval = null;
    let simplifiedTimeEnabled = (
        workspace.dataset.initialSimplifiedTime === "true"
    );
    let themePreference = normalizeThemeChoice(
        workspace.dataset.initialTheme
        || document.documentElement.dataset.theme
        || "system",
    );
    let pageWidthPreference = normalizePageWidthChoice(
        workspace.dataset.initialPageWidth || "wide",
    );
    let typographyPreferences = {
        entry: normalizeJournalFontSize(
            workspace.dataset.initialJournalEntrySize,
        ),
        time: normalizeJournalFontSize(
            workspace.dataset.initialJournalTimeSize,
        ),
        date: normalizeJournalFontSize(
            workspace.dataset.initialJournalDateSize,
        ),
        tableHeader: normalizeJournalFontSize(
            workspace.dataset.initialJournalTableHeaderSize,
        ),
        title: normalizeJournalFontSize(
            workspace.dataset.initialJournalTitleSize,
        ),
    };
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

    function normalizeThemeChoice(value) {
        const normalized = String(value || "").toLowerCase();
        return ["system", "light", "dark"].includes(normalized)
            ? normalized
            : "system";
    }

    function normalizePageWidthChoice(value) {
        const normalized = String(value || "").toLowerCase();
        return ["standard", "wide", "full"].includes(normalized)
            ? normalized
            : "wide";
    }

    function normalizeJournalFontSize(value) {
        const normalized = String(value || "").toLowerCase();
        return [
            "small",
            "normal",
            "large",
            "extra_large",
        ].includes(normalized)
            ? normalized
            : "normal";
    }

    function resolvedTheme(value) {
        if (value !== "system") {
            return value;
        }
        return window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    }

    function updateQuickSettingButtons() {
        themeChoiceButtons.forEach((button) => {
            const active = button.dataset.themeChoice === themePreference;
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });
        pageWidthChoiceButtons.forEach((button) => {
            const active = (
                button.dataset.pageWidthChoice === pageWidthPreference
            );
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });
        typographySizeButtons.forEach((button) => {
            const target = button.dataset.typographyTarget;
            const active = (
                typographyPreferences[target]
                === button.dataset.typographySize
            );
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });
        typographyPresetButtons.forEach((button) => {
            const size = button.dataset.typographyPreset;
            const active = Object.values(
                typographyPreferences,
            ).every((value) => value === size);
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });
        if (simplifiedTimeToggle) {
            simplifiedTimeToggle.classList.toggle(
                "is-active",
                simplifiedTimeEnabled,
            );
            simplifiedTimeToggle.setAttribute(
                "aria-pressed",
                String(simplifiedTimeEnabled),
            );
            simplifiedTimeToggle.title = simplifiedTimeEnabled
                ? "Упрощённый ввод времени включён"
                : "Вводить 1120 вместо 11:20";
        }
        if (simplifiedTimeLabel) {
            simplifiedTimeLabel.textContent = simplifiedTimeEnabled
                ? "Время · упрощённо"
                : "Время · обычно";
        }
    }

    function applyQuickDisplayPreferences() {
        document.documentElement.dataset.themePreference = themePreference;
        document.documentElement.dataset.theme = resolvedTheme(
            themePreference,
        );
        workspace.dataset.pageWidth = pageWidthPreference;
        workspace.dataset.journalEntrySize = typographyPreferences.entry;
        workspace.dataset.journalTimeSize = typographyPreferences.time;
        workspace.dataset.journalDateSize = typographyPreferences.date;
        workspace.dataset.journalTableHeaderSize = (
            typographyPreferences.tableHeader
        );
        workspace.dataset.journalTitleSize = typographyPreferences.title;
        document.documentElement.dataset.journalSize = (
            typographyPreferences.entry
        );
        document.documentElement.dataset.journalTimeSize = (
            typographyPreferences.time
        );
        document.documentElement.dataset.journalDateSize = (
            typographyPreferences.date
        );
        document.documentElement.dataset.journalTableHeaderSize = (
            typographyPreferences.tableHeader
        );
        document.documentElement.dataset.journalTitleSize = (
            typographyPreferences.title
        );
        workspace.dataset.simplifiedTimeInput = String(
            simplifiedTimeEnabled,
        );
        workspace.dispatchEvent(
            new CustomEvent("eod:simplified-time-setting", {
                detail: {enabled: simplifiedTimeEnabled},
            }),
        );
        if (journalTitleNode) {
            journalTitleNode.dataset.journalTitleSize = (
                typographyPreferences.title
            );
        }
        rows.forEach((row) => {
            autoGrow(row.querySelector("[data-auto-grow]"));
        });
        updateQuickSettingButtons();
        schedulePagination(20);
    }

    async function persistQuickDisplayPreferences(previous) {
        if (!quickDisplayForm) {
            return;
        }
        if (quickSettingsController) {
            quickSettingsController.abort();
        }
        const controller = new AbortController();
        quickSettingsController = controller;
        quickSettingStatus.textContent = "Сохранение…";
        const data = new FormData(quickDisplayForm);
        data.set("theme", themePreference.toUpperCase());
        data.set("journal_width", pageWidthPreference.toUpperCase());
        data.set(
            "journal_font_size",
            typographyPreferences.entry.toUpperCase(),
        );
        data.set(
            "journal_time_font_size",
            typographyPreferences.time.toUpperCase(),
        );
        data.set(
            "journal_date_font_size",
            typographyPreferences.date.toUpperCase(),
        );
        data.set(
            "journal_table_header_font_size",
            typographyPreferences.tableHeader.toUpperCase(),
        );
        data.set(
            "journal_title_font_size",
            typographyPreferences.title.toUpperCase(),
        );
        data.set(
            "journal_simplified_time_input",
            simplifiedTimeEnabled ? "1" : "0",
        );

        try {
            const response = await fetch(quickDisplayForm.action, {
                method: "POST",
                body: data,
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                signal: controller.signal,
            });
            const payload = await response.json();
            if (!response.ok || !payload.ok) {
                throw new Error(payload.message || "save_failed");
            }
            themePreference = normalizeThemeChoice(payload.theme);
            pageWidthPreference = normalizePageWidthChoice(
                payload.journal_width,
            );
            typographyPreferences = {
                entry: normalizeJournalFontSize(
                    payload.journal_font_size,
                ),
                time: normalizeJournalFontSize(
                    payload.journal_time_font_size,
                ),
                date: normalizeJournalFontSize(
                    payload.journal_date_font_size,
                ),
                tableHeader: normalizeJournalFontSize(
                    payload.journal_table_header_font_size,
                ),
                title: normalizeJournalFontSize(
                    payload.journal_title_font_size,
                ),
            };
            simplifiedTimeEnabled = Boolean(
                payload.journal_simplified_time_input,
            );
            applyQuickDisplayPreferences();
            quickSettingStatus.textContent = "✓ Сохранено";
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }
            themePreference = previous.theme;
            pageWidthPreference = previous.pageWidth;
            typographyPreferences = {
                ...previous.typography,
            };
            simplifiedTimeEnabled = previous.simplifiedTime;
            applyQuickDisplayPreferences();
            quickSettingStatus.textContent = "Не удалось сохранить";
        } finally {
            if (quickSettingsController === controller) {
                quickSettingsController = null;
            }
        }
    }

    function selectQuickDisplayPreference(kind, value) {
        const previous = {
            theme: themePreference,
            pageWidth: pageWidthPreference,
            typography: {
                ...typographyPreferences,
            },
            simplifiedTime: simplifiedTimeEnabled,
        };
        if (kind === "theme") {
            themePreference = normalizeThemeChoice(value);
        } else {
            pageWidthPreference = normalizePageWidthChoice(value);
        }
        applyQuickDisplayPreferences();
        void persistQuickDisplayPreferences(previous);
    }

    function selectTypographyPreference(target, value) {
        if (!(target in typographyPreferences)) {
            return;
        }
        const previous = {
            theme: themePreference,
            pageWidth: pageWidthPreference,
            typography: {
                ...typographyPreferences,
            },
            simplifiedTime: simplifiedTimeEnabled,
        };
        typographyPreferences[target] = normalizeJournalFontSize(value);
        applyQuickDisplayPreferences();
        void persistQuickDisplayPreferences(previous);
    }

    function selectTypographyPreset(value) {
        const normalized = normalizeJournalFontSize(value);
        const previous = {
            theme: themePreference,
            pageWidth: pageWidthPreference,
            typography: {
                ...typographyPreferences,
            },
            simplifiedTime: simplifiedTimeEnabled,
        };
        typographyPreferences = {
            entry: normalized,
            time: normalized,
            date: normalized,
            tableHeader: normalized,
            title: normalized,
        };
        applyQuickDisplayPreferences();
        void persistQuickDisplayPreferences(previous);
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

    function isEditorOverlayTarget(node) {
        return Boolean(
            node?.closest?.(
                "[data-editor-ribbon], "
                + "[data-editor-floating-toolbar], "
                + "[data-entry-kind-menu], "
                + "[data-reference-picker], "
                + "[data-reference-preview]",
            ),
        );
    }

    function isDraftEditing() {
        if (compositionDepth > 0 || editorOverlayActive) {
            return true;
        }
        if (!activeDraftForm) {
            return false;
        }
        const active = document.activeElement;
        return Boolean(
            active
            && (
                activeDraftForm.contains(active)
                || isEditorOverlayTarget(active)
            )
        );
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

    function firstFormError(errors) {
        const source = errors || {};
        const priority = [
            "event_at",
            "editor_payload",
            "content",
            "editor_schema_version",
        ];
        const keys = [
            ...priority,
            ...Object.keys(source).filter(
                (key) => !priority.includes(key),
            ),
        ];
        for (const key of keys) {
            const values = Array.isArray(source[key])
                ? source[key]
                : [source[key]];
            const first = values.find(Boolean);
            if (typeof first === "string") {
                return first;
            }
            if (first?.message) {
                return first.message;
            }
        }
        return "Не сохранено";
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

    function applySimplifiedTimeToInput(input, final = false) {
        if (!simplifiedTimeEnabled || !input) {
            return false;
        }
        const source = String(input.value || "");
        if (source.includes(":")) {
            return false;
        }
        const digits = source.replace(/\D/g, "");
        if (digits.length !== 4 && !(final && digits.length === 3)) {
            return false;
        }
        const normalized = normalizeTime(digits);
        if (!normalized) {
            return false;
        }
        input.value = normalized;
        return true;
    }

    function setSimplifiedTimeEnabled(value) {
        const previous = {
            theme: themePreference,
            pageWidth: pageWidthPreference,
            typography: {
                ...typographyPreferences,
            },
            simplifiedTime: simplifiedTimeEnabled,
        };
        simplifiedTimeEnabled = Boolean(value);
        applyQuickDisplayPreferences();
        void persistQuickDisplayPreferences(previous);
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

    function dateLabelToIso(value) {
        const normalized = normalizeDate(value || "");
        if (!normalized) {
            return null;
        }
        const [day, month, year] = normalized.split(".");
        return `${year}-${month}-${day}`;
    }

    function parseLocalDateTime(value) {
        const match = String(value || "").match(
            /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/,
        );
        if (!match) {
            return null;
        }
        const [, year, month, day, hours, minutes] = match;
        const parsed = new Date(
            Number(year),
            Number(month) - 1,
            Number(day),
            Number(hours),
            Number(minutes),
            0,
            0,
        );
        if (
            parsed.getFullYear() !== Number(year)
            || parsed.getMonth() + 1 !== Number(month)
            || parsed.getDate() !== Number(day)
            || parsed.getHours() !== Number(hours)
            || parsed.getMinutes() !== Number(minutes)
        ) {
            return null;
        }
        return parsed;
    }

    function formatShiftBoundary(value) {
        const parsed = parseLocalDateTime(value);
        if (!parsed) {
            return value;
        }
        return new Intl.DateTimeFormat("ru-RU", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        }).format(parsed).replace(",", "");
    }

    function shiftRangeLabel() {
        return (
            `${formatShiftBoundary(shiftStartAt)} — `
            + formatShiftBoundary(shiftEndAt)
        );
    }

    function validateShiftDateTime(dateIso, timeValue) {
        const normalizedTime = normalizeTime(timeValue || "");
        const candidate = parseLocalDateTime(
            `${dateIso}T${normalizedTime || ""}`,
        );
        const start = parseLocalDateTime(shiftStartAt);
        const end = parseLocalDateTime(shiftEndAt);
        if (!candidate || !normalizedTime) {
            return {
                ok: false,
                message: "Укажите корректные дату и время.",
            };
        }
        if (
            start
            && end
            && (candidate < start || candidate > end)
        ) {
            return {
                ok: false,
                message: (
                    "Дата и время должны входить в интервал смены: "
                    + shiftRangeLabel()
                ),
            };
        }
        return {
            ok: true,
            dateTime: `${dateIso}T${normalizedTime}`,
            normalizedTime,
        };
    }

    function compareDraftRows(left, right) {
        const timeCompare = String(left.dataset.entryAt || "").localeCompare(
            String(right.dataset.entryAt || ""),
        );
        if (timeCompare !== 0) {
            return timeCompare;
        }
        const positionCompare = (
            Number(left.dataset.entryPosition || 0)
            - Number(right.dataset.entryPosition || 0)
        );
        if (positionCompare !== 0) {
            return positionCompare;
        }
        return String(left.dataset.draftId || "").localeCompare(
            String(right.dataset.draftId || ""),
        );
    }

    function sortRowsChronologically() {
        rows.sort(compareDraftRows);
        rows.forEach((row) => rowStore.append(row));
        refreshInlineDateMarkers();
    }

    function revealChronologicalRow(row) {
        sortRowsChronologically();
        paginateByRecordCount(true);
        const pageIndex = pages.findIndex((page) => (
            page.rows.includes(row)
        ));
        if (pageIndex >= 0) {
            currentPage = viewMode === "spread"
                ? Math.floor(pageIndex / 2) * 2
                : pageIndex;
            renderCurrentPages();
        }
        row.classList.remove("is-chronology-moved");
        void row.offsetWidth;
        row.classList.add("is-chronology-moved");
        window.setTimeout(() => {
            row.classList.remove("is-chronology-moved");
        }, 1600);
        window.requestAnimationFrame(() => {
            row.scrollIntoView({
                block: "center",
                behavior: "smooth",
            });
        });
    }

    function applyPendingChronology(form) {
        if (form.dataset.chronologyPending !== "true") {
            return false;
        }
        delete form.dataset.chronologyPending;
        const row = form.closest("[data-draft-card]");
        if (row) {
            revealChronologicalRow(row);
        }
        return true;
    }

    function refreshInlineDateMarkers() {
        let previousDate = null;
        rows.forEach((row) => {
            const rowDate = row.dataset.entryDate || "";
            const rowLabel = row.dataset.entryDateLabel || "";
            let marker = row.querySelector("[data-inline-date]");
            const needsMarker = Boolean(
                rowDate && rowDate !== previousDate,
            );
            if (needsMarker) {
                if (!marker) {
                    marker = document.createElement("div");
                    marker.className = "draft-inline-date";
                    marker.dataset.inlineDate = "true";
                    row.prepend(marker);
                }
                marker.textContent = rowLabel;
            } else if (marker) {
                marker.remove();
            }
            previousDate = rowDate || previousDate;
        });
    }

    function closeDateEditor(restoreFocus = false) {
        if (!activeDateEditor) {
            return;
        }
        const { editor, button } = activeDateEditor;
        editor.remove();
        button.setAttribute("aria-expanded", "false");
        activeDateEditor = null;
        if (restoreFocus) {
            button.focus();
        }
    }

    function openDateEditor(form, dateButton) {
        if (
            activeDateEditor
            && activeDateEditor.form === form
        ) {
            activeDateEditor.dateInput.focus();
            return;
        }
        closeDateEditor();

        const contentCell = form.querySelector(
            ".draft-ledger-content",
        );
        const lower = form.querySelector(
            ".draft-ledger-lower",
        );
        const timeInput = form.querySelector(
            "[data-quick-time]",
        );
        if (!contentCell || !lower || !timeInput) {
            return;
        }

        const editor = document.createElement("section");
        editor.className = "draft-date-editor";
        editor.dataset.dateEditor = "true";
        editor.setAttribute("aria-label", "Редактор даты записи");

        const heading = document.createElement("div");
        heading.className = "draft-date-editor-heading";
        const title = document.createElement("strong");
        title.textContent = "Дата записи";
        const range = document.createElement("span");
        range.textContent = `Смена: ${shiftRangeLabel()}`;
        heading.append(title, range);

        const controls = document.createElement("div");
        controls.className = "draft-date-editor-controls";
        const dateLabel = document.createElement("label");
        dateLabel.textContent = "Дата";
        const dateInput = document.createElement("input");
        dateInput.type = "date";
        dateInput.value = (
            dateLabelToIso(dateButton.dataset.currentDate)
            || form.querySelector("[data-event-at]")
                ?.value.slice(0, 10)
            || defaultEntryDateIso
        );
        if (shiftStartAt) {
            dateInput.min = shiftStartAt.slice(0, 10);
        }
        if (shiftEndAt) {
            dateInput.max = shiftEndAt.slice(0, 10);
        }
        dateLabel.append(dateInput);

        const timePreview = document.createElement("div");
        timePreview.className = "draft-date-editor-time";
        timePreview.innerHTML = (
            "<span>Время записи</span>"
            + `<strong>${normalizeTime(timeInput.value) || "—"}</strong>`
        );

        const actions = document.createElement("div");
        actions.className = "draft-date-editor-actions";
        const cancelButton = document.createElement("button");
        cancelButton.type = "button";
        cancelButton.className = "secondary";
        cancelButton.textContent = "Отмена";
        const applyButton = document.createElement("button");
        applyButton.type = "button";
        applyButton.className = "button compact-button";
        applyButton.textContent = "Применить";
        actions.append(cancelButton, applyButton);
        controls.append(dateLabel, timePreview, actions);

        const message = document.createElement("p");
        message.className = "draft-date-editor-message";
        message.setAttribute("role", "status");
        message.setAttribute("aria-live", "polite");
        editor.append(heading, controls, message);
        contentCell.insertBefore(editor, lower);
        dateButton.setAttribute("aria-expanded", "true");
        activeDateEditor = {
            form,
            button: dateButton,
            editor,
            dateInput,
            message,
        };

        const applySelection = async () => {
            const validation = validateShiftDateTime(
                dateInput.value,
                timeInput.value,
            );
            if (!validation.ok) {
                message.textContent = validation.message;
                editor.classList.add("has-error");
                dateInput.focus();
                return;
            }

            editor.classList.remove("has-error");
            message.textContent = "Сохранение…";
            const dateText = isoDateToLabel(dateInput.value);
            const hidden = form.querySelector("[data-event-at]");
            const row = form.closest("[data-draft-card]");
            const original = {
                dateText: dateButton.dataset.currentDate || "",
                title: dateButton.title,
                hiddenValue: hidden?.value || "",
                timeValue: timeInput.value,
                rowDate: row?.dataset.entryDate || "",
                rowDateLabel: row?.dataset.entryDateLabel || "",
                rowEntryAt: row?.dataset.entryAt || "",
            };
            if (!hidden) {
                message.textContent = "Не найдено поле даты записи.";
                editor.classList.add("has-error");
                return;
            }

            dateButton.dataset.currentDate = dateText;
            dateButton.title = `Дата записи: ${dateText}`;
            hidden.value = validation.dateTime;
            timeInput.value = validation.normalizedTime;
            if (row) {
                row.dataset.entryDate = dateInput.value;
                row.dataset.entryDateLabel = dateText;
            }

            const saved = await save(form);
            if (!saved) {
                dateButton.dataset.currentDate = original.dateText;
                dateButton.title = original.title;
                hidden.value = original.hiddenValue;
                timeInput.value = original.timeValue;
                if (row) {
                    row.dataset.entryDate = original.rowDate;
                    row.dataset.entryDateLabel = original.rowDateLabel;
                    row.dataset.entryAt = original.rowEntryAt;
                }
                message.textContent = (
                    "Не удалось сохранить дату. Проверьте интервал смены."
                );
                editor.classList.add("has-error");
                return;
            }

            closeDateEditor(false);
            form.classList.remove("has-focus");
            if (activeDraftForm === form) {
                activeDraftForm = null;
            }
            applyPendingChronology(form);
            window.requestAnimationFrame(() => dateButton.focus());
        };

        cancelButton.addEventListener("click", () => {
            closeDateEditor(true);
        });
        applyButton.addEventListener("click", () => {
            void applySelection();
        });
        editor.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                event.preventDefault();
                closeDateEditor(true);
            }
            if (
                event.key === "Enter"
                && event.target === dateInput
            ) {
                event.preventDefault();
                void applySelection();
            }
        });

        window.requestAnimationFrame(() => {
            dateInput.focus();
        });
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

        const dateIso = dateLabelToIso(normalizedDate);
        const validation = validateShiftDateTime(
            dateIso,
            normalizedTime,
        );
        if (!validation.ok) {
            return false;
        }

        time.value = validation.normalizedTime;
        hidden.value = validation.dateTime;
        dateButton.dataset.currentDate = normalizedDate;

        const row = form.closest("[data-draft-card]");
        if (row) {
            row.dataset.entryDate = dateIso;
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
        const row = form.closest("[data-draft-card]");
        const previousEntryAt = row?.dataset.entryAt || "";
        if (!syncHiddenDateTime(form)) {
            setStatus(
                form,
                "Дата и время вне интервала смены",
                "is-error",
            );
            return false;
        }

        const previous = controllers.get(form);
        if (previous) {
            previous.abort();
        }

        const controller = new AbortController();
        controllers.set(form, controller);
        setStatus(form, "Сохранение…", "is-saving");
        window.EODDraftEditor?.syncForm(form);

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
                return false;
            }
            if (!response.ok || !payload.ok) {
                setStatus(
                    form,
                    firstFormError(payload.errors),
                    "is-error",
                );
                return false;
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
            window.EODDraftEditor?.acceptSaved(form, payload);
            setStatus(
                form,
                `Сохранено · ${payload.saved_at}`,
                "is-saved",
            );

            const savedEntryAt = (
                payload.event_at
                || form.querySelector("[data-event-at]")?.value
                || previousEntryAt
            );
            if (row) {
                row.dataset.entryAt = savedEntryAt;
                if (savedEntryAt !== previousEntryAt) {
                    form.dataset.chronologyPending = "true";
                    markPaginationPending();
                    if (!form.contains(document.activeElement)) {
                        applyPendingChronology(form);
                    }
                }
            }
            flushDeferredPagination();
            return true;
        } catch (error) {
            if (error.name !== "AbortError") {
                setStatus(form, "Нет связи", "is-error");
            }
            return false;
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

        setStatus(form, "Есть изменения", "is-dirty");
        const timer = window.setTimeout(() => {
            timers.delete(form);
            void save(form);
        }, autosaveDelay);
        timers.set(form, timer);
    }

    function preserveViewport(callback) {
        const x = window.scrollX;
        const y = window.scrollY;
        callback();
        window.requestAnimationFrame(() => {
            window.scrollTo(x, y);
            window.requestAnimationFrame(() => window.scrollTo(x, y));
        });
    }

    function stopRemovalTimers(state) {
        if (!state) {
            return;
        }
        window.clearTimeout(state.timeout);
        window.clearInterval(state.interval);
        state.timeout = null;
        state.interval = null;
    }

    function clearInlineRemovalState(state) {
        stopRemovalTimers(state);
        if (pendingRemoval === state) {
            pendingRemoval = null;
        }
    }

    function finalizeRemovedDraft(state, animate = true) {
        if (!state || state.restoring || state.finalized) {
            return;
        }
        state.finalized = true;
        clearInlineRemovalState(state);
        const index = rows.indexOf(state.row);
        if (index >= 0) {
            rows.splice(index, 1);
        }
        const remove = () => {
            state.row.remove();
            paginateByRecordCount(true);
            refreshInlineDateMarkers();
        };
        if (!animate) {
            preserveViewport(remove);
            return;
        }
        state.row.classList.add("is-undo-expiring");
        window.setTimeout(() => preserveViewport(remove), 180);
    }

    async function postDraftAction(url, form) {
        const response = await fetch(url, {
            method: "POST",
            body: new FormData(form),
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
            throw new Error(firstFormError(payload.errors));
        }
        return payload;
    }

    function updateInlineRemovalCountdown(state) {
        const seconds = Math.max(
            0,
            Math.ceil((state.deadline - Date.now()) / 1000),
        );
        state.countdown.textContent = `${seconds} с`;
    }

    function showInlineRemovalPlaceholder(state) {
        if (pendingRemoval && pendingRemoval !== state) {
            finalizeRemovedDraft(pendingRemoval, false);
        }
        pendingRemoval = state;
        state.form.hidden = true;
        state.placeholder.hidden = false;
        state.placeholder.style.minHeight = `${Math.max(
            48,
            Math.round(state.formHeight),
        )}px`;
        state.row.classList.remove("is-removing");
        state.row.classList.add("is-undo-pending");
        state.deadline = Date.now() + 10000;
        updateInlineRemovalCountdown(state);
        state.interval = window.setInterval(
            () => updateInlineRemovalCountdown(state),
            250,
        );
        state.timeout = window.setTimeout(
            () => finalizeRemovedDraft(state, true),
            10000,
        );
    }

    function restoreInlineRemovalPresentation(state) {
        state.placeholder.hidden = true;
        state.placeholder.style.removeProperty("min-height");
        state.form.hidden = false;
        state.row.classList.remove(
            "is-removing",
            "is-undo-pending",
            "is-undo-expiring",
        );
    }

    async function undoRemovedDraft(state, button) {
        if (pendingRemoval !== state || state.restoring || state.finalized) {
            return;
        }
        state.restoring = true;
        button.disabled = true;
        button.textContent = "Восстановление…";
        try {
            const payload = await postDraftAction(
                state.restoreUrl,
                state.form,
            );
            const versionInput = state.form.querySelector(
                "[data-draft-version]",
            );
            const versionLabel = state.form.querySelector(
                "[data-version-label]",
            );
            if (versionInput) {
                versionInput.value = String(payload.version);
            }
            if (versionLabel) {
                versionLabel.textContent = String(payload.version);
            }
            clearInlineRemovalState(state);
            restoreInlineRemovalPresentation(state);
            state.row.classList.add("is-restoring");
            window.setTimeout(() => {
                state.row.classList.remove("is-restoring");
            }, 700);
            setStatus(state.form, "Восстановлено", "is-saved");
            button.disabled = false;
            button.textContent = "Восстановить";
        } catch (error) {
            state.restoring = false;
            button.disabled = false;
            button.textContent = "Восстановить";
            state.message.textContent = (
                error.message || "Не удалось восстановить запись"
            );
        }
    }

    async function removeDraftRow(form, row, removeUrl, restoreUrl) {
        if (
            !form
            || !row
            || row.classList.contains("is-removing")
            || row.classList.contains("is-undo-pending")
        ) {
            return;
        }
        const activeTimer = timers.get(form);
        if (activeTimer) {
            window.clearTimeout(activeTimer);
            timers.delete(form);
        }
        const status = statusNode(form);
        if (
            status?.classList.contains("is-dirty")
            || status?.classList.contains("is-saving")
        ) {
            const saved = await save(form);
            if (!saved) {
                return;
            }
        }

        window.EODDraftEditor?.deactivate(form);
        form.classList.remove("has-focus");
        if (activeDraftForm === form) {
            activeDraftForm = null;
        }

        const placeholder = row.querySelector("[data-inline-undo]");
        const button = row.querySelector("[data-inline-undo-button]");
        const countdown = row.querySelector("[data-inline-undo-countdown]");
        const message = row.querySelector(".draft-inline-undo-message");
        if (!placeholder || !button || !countdown || !message) {
            setStatus(form, "Не удалось открыть восстановление", "is-error");
            return;
        }
        const state = {
            row,
            form,
            restoreUrl,
            placeholder,
            button,
            countdown,
            message,
            formHeight: form.getBoundingClientRect().height,
            deadline: 0,
            timeout: null,
            interval: null,
            restoring: false,
            finalized: false,
        };
        button.onclick = () => void undoRemovedDraft(state, button);
        message.textContent = "Запись удалена";
        button.disabled = false;
        button.textContent = "Восстановить";

        row.classList.add("is-removing");
        try {
            await postDraftAction(removeUrl, form);
            showInlineRemovalPlaceholder(state);
        } catch (error) {
            restoreInlineRemovalPresentation(state);
            setStatus(
                form,
                error.message || "Не удалось удалить запись",
                "is-error",
            );
        }
    }

    async function finishDraftEditing(form, shortcut) {
        if (!form || form.dataset.finishing === "true") {
            return;
        }
        form.dataset.finishing = "true";
        const activeTimer = timers.get(form);
        if (activeTimer) {
            window.clearTimeout(activeTimer);
            timers.delete(form);
        }
        const row = form.closest("[data-draft-card]");
        const x = window.scrollX;
        const y = window.scrollY;
        const saved = await save(form);
        if (!saved) {
            delete form.dataset.finishing;
            return;
        }
        const active = document.activeElement;
        if (form.contains(active)) {
            active.blur();
        }
        window.EODDraftEditor?.deactivate(form);
        form.classList.remove("has-focus");
        if (activeDraftForm === form) {
            activeDraftForm = null;
        }
        if (!applyPendingChronology(form)) {
            flushDeferredPagination();
        }
        row?.classList.add("is-edit-complete");
        window.setTimeout(() => {
            row?.classList.remove("is-edit-complete");
        }, 850);
        window.requestAnimationFrame(() => {
            window.scrollTo(x, y);
        });
        delete form.dataset.finishing;
        workspace.dispatchEvent(
            new CustomEvent("eod:draft-edit-finished", {
                bubbles: true,
                detail: {
                    publicId: row?.dataset.draftId || "",
                    shortcut,
                },
            }),
        );
    }

    function rowText(row) {
        const textarea = row.querySelector(
            "[data-editor-fallback]",
        );
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
            window.EODDraftEditor?.seedPlainText(form, content);
            row.dataset.entryFilled = (
                content.trim() ? "true" : "false"
            );

            hiddenDateTime.value = (
                `${dateIso}T${normalizedTime}`
            );
            dateButton.dataset.currentDate = dateLabel;
            row.dataset.entryDate = dateIso;
            row.dataset.entryDateLabel = dateLabel;
            row.dataset.entryAt = `${dateIso}T${normalizedTime}`;

            const serverDateMarker = row.querySelector(
                "[data-inline-date]",
            );
            if (serverDateMarker) {
                serverDateMarker.remove();
            }

            state.record.replaceWith(row);
            rows.push(row);
            form.dataset.chronologyPending = "true";
            bindDraftRow(row);
            bindEditorCommands(row);
            inlineCreation = null;
            refreshInlineDateMarkers();
            markPaginationPending();

            activeDraftForm = form;
            form.classList.add("has-focus");
            autoGrow(contentInput);

            if (focusContent) {
                if (!window.EODDraftEditor?.focus(form, "end")) {
                    contentInput.focus();
                    contentInput.setSelectionRange(
                        contentInput.value.length,
                        contentInput.value.length,
                    );
                }
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
        timeInput.dataset.quickTime = "true";
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
        const addButton = document.createElement("button");
        addButton.type = "button";
        addButton.className = "draft-empty-record-add";
        addButton.dataset.inlineCreateTrigger = "true";
        addButton.textContent = "+";
        addButton.setAttribute(
            "aria-label",
            "Добавить запись в эту строку",
        );
        addButton.title = "Добавить запись";
        addButton.addEventListener("click", () => {
            beginInlineCreation(
                record,
                record.dataset.entryDateLabel,
                record.dataset.entryDate,
            );
        });
        timeCell.append(addButton);

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
        window.EODDraftEditor?.bindToolbar(scope);
    }

    function bindDraftRow(row) {
        if (row.dataset.bound === "true") {
            return;
        }
        row.dataset.bound = "true";

        const form = row.querySelector("[data-draft-form]");
        const textarea = form.querySelector("[data-editor-fallback]");
        const timeInput = form.querySelector("[data-quick-time]");
        const dateButton = form.querySelector("[data-date-button]");
        const richEditor = (
            window.EODDraftEditor?.initializeRow(row) || null
        );

        if (!richEditor) {
            autoGrow(textarea);
        }

        form.addEventListener("focusin", () => {
            activeDraftForm = form;
            form.classList.add("has-focus");
        });

        form.addEventListener("focusout", () => {
            window.setTimeout(() => {
                const active = document.activeElement;
                if (
                    form.contains(active)
                    || editorOverlayActive
                    || isEditorOverlayTarget(active)
                ) {
                    return;
                }
                form.classList.remove("has-focus");
                if (activeDraftForm === form) {
                    activeDraftForm = null;
                }
                if (!applyPendingChronology(form)) {
                    flushDeferredPagination();
                }
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
                if (!window.EODDraftEditor?.focus(form)) {
                    textarea.focus();
                }
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
            openDateEditor(form, dateButton);
        });

        form.addEventListener("submit", (event) => {
            const submitter = event.submitter;
            if (submitter?.matches?.("[data-remove-draft]")) {
                event.preventDefault();
                void removeDraftRow(
                    form,
                    row,
                    submitter.formAction
                    || submitter.getAttribute("formaction")
                    || "",
                    submitter.dataset.restoreUrl,
                );
                return;
            }
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

    workspace.addEventListener("eod:finish-draft-edit", (event) => {
        const form = event.target.closest?.("[data-draft-form]");
        if (!form) {
            return;
        }
        void finishDraftEditing(
            form,
            event.detail?.shortcut || "external",
        );
    });

    workspace.addEventListener("eod:editor-overlay-state", (event) => {
        editorOverlayActive = Boolean(event.detail?.active);
        if (!editorOverlayActive) {
            flushDeferredPagination();
        }
    });

    workspace.addEventListener("eod:reveal-draft-reference", (event) => {
        const draftId = String(event.detail?.draftId || "");
        if (!draftId) {
            return;
        }
        const row = rows.find((candidate) => (
            candidate.dataset.draftId === draftId
        ));
        if (!row) {
            return;
        }
        editorOverlayActive = false;
        activeDraftForm = null;
        revealChronologicalRow(row);
    });

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

    themeChoiceButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectQuickDisplayPreference(
                "theme",
                button.dataset.themeChoice,
            );
        });
    });

    pageWidthChoiceButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectQuickDisplayPreference(
                "pageWidth",
                button.dataset.pageWidthChoice,
            );
        });
    });

    simplifiedTimeToggle?.addEventListener("click", () => {
        setSimplifiedTimeEnabled(!simplifiedTimeEnabled);
    });

    workspace.addEventListener("input", (event) => {
        const input = event.target.closest?.("[data-quick-time]");
        if (!input || !workspace.contains(input)) {
            return;
        }
        applySimplifiedTimeToInput(input, false);
    });

    workspace.addEventListener("focusout", (event) => {
        const input = event.target.closest?.("[data-quick-time]");
        if (!input || !workspace.contains(input)) {
            return;
        }
        applySimplifiedTimeToInput(input, true);
    });

    const systemThemeQuery = window.matchMedia(
        "(prefers-color-scheme: dark)",
    );
    systemThemeQuery.addEventListener?.("change", () => {
        if (themePreference === "system") {
            applyQuickDisplayPreferences();
        }
    });

    typographySizeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectTypographyPreference(
                button.dataset.typographyTarget,
                button.dataset.typographySize,
            );
        });
    });

    typographyPresetButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectTypographyPreset(
                button.dataset.typographyPreset,
            );
        });
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
    applyQuickDisplayPreferences();
    updateRecordControls();
    sortRowsChronologically();

    updateColumnWidths(
        readPreference("eod-draft-column-time", "14"),
        readPreference("eod-draft-column-remarks", "20"),
        false,
    );

    window.requestAnimationFrame(() => {
        paginateByRecordCount(true);
    });
})();
