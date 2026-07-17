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

    const measurePage = workspace.querySelector(
        "[data-measure-page]",
    );
    const measureBody = workspace.querySelector(
        "[data-measure-body]",
    );
    const measureDate = workspace.querySelector(
        "[data-measure-date]",
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

    const sidePanel = workspace.querySelector(
        "[data-draft-side-panel]",
    );
    const timeColumnInput = workspace.querySelector(
        "[data-column-time]",
    );
    const remarksColumnInput = workspace.querySelector(
        "[data-column-remarks]",
    );
    const columnValues = workspace.querySelector(
        "[data-column-values]",
    );

    let pages = [];
    let currentPage = 0;
    let paginationTimer = null;
    let resizeTimer = null;
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
            // Настройка продолжает работать в текущей вкладке.
        }
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
            `${Math.max(34, textarea.scrollHeight)}px`
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
        measureBody.replaceChildren();
    }

    function rowOverflowsMeasurePage() {
        return (
            measureBody.scrollHeight
            > measureBody.clientHeight + 1
        );
    }

    function paginateByHeight() {
        restoreRowsToStore();

        const visibleRows = filteredRows();
        const pageWidth = leftShell.getBoundingClientRect().width;
        const pageHeight = leftShell.getBoundingClientRect().height;
        measurePage.style.width = `${pageWidth}px`;
        measurePage.style.height = `${pageHeight}px`;

        pages = [];
        let pageRows = [];

        visibleRows.forEach((row) => {
            row.hidden = false;
            row.classList.remove("is-page-first");

            if (pageRows.length === 0) {
                row.classList.add("is-page-first");
                measureDate.textContent = (
                    row.dataset.entryDateLabel || ""
                );
            }

            measureBody.append(row);
            autoGrow(row.querySelector("[data-auto-grow]"));

            if (
                rowOverflowsMeasurePage()
                && pageRows.length > 0
            ) {
                measureBody.removeChild(row);
                pageRows.forEach((pageRow) => {
                    rowStore.append(pageRow);
                });
                pages.push(pageRows);

                pageRows = [];
                measureBody.replaceChildren();
                row.classList.add("is-page-first");
                measureDate.textContent = (
                    row.dataset.entryDateLabel || ""
                );
                measureBody.append(row);
                autoGrow(row.querySelector("[data-auto-grow]"));
            }

            pageRows.push(row);
        });

        if (pageRows.length > 0) {
            pageRows.forEach((pageRow) => {
                rowStore.append(pageRow);
            });
            pages.push(pageRows);
        }

        rows
            .filter((row) => !visibleRows.includes(row))
            .forEach((row) => {
                row.hidden = true;
                rowStore.append(row);
            });

        if (pages.length === 0) {
            pages = [[]];
        }

        const visiblePageCount = (
            viewMode === "spread" ? 2 : 1
        );
        const lastStart = Math.max(
            0,
            pages.length - visiblePageCount,
        );
        currentPage = Math.min(currentPage, lastStart);
        if (viewMode === "spread") {
            currentPage = (
                Math.floor(currentPage / 2) * 2
            );
        }

        renderCurrentPages();
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

        const pageRows = pages[pageIndex];
        if (!pageRows) {
            shell.classList.add("is-empty-page");
            dateNode.textContent = "";
            numberNode.textContent = "";
            return;
        }

        pageRows.forEach((row) => {
            row.hidden = false;
            body.append(row);
            autoGrow(row.querySelector("[data-auto-grow]"));
        });
        dateNode.textContent = (
            pageRows[0]?.dataset.entryDateLabel || ""
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

    function schedulePagination() {
        if (paginationTimer) {
            window.clearTimeout(paginationTimer);
        }
        paginationTimer = window.setTimeout(() => {
            paginationTimer = null;
            paginateByHeight();
        }, 260);
    }

    function applyColumnWidths(timeValue, remarksValue) {
        let time = Number(timeValue);
        let remarks = Number(remarksValue);
        if (!Number.isFinite(time)) {
            time = 14;
        }
        if (!Number.isFinite(remarks)) {
            remarks = 20;
        }

        time = Math.min(24, Math.max(10, time));
        remarks = Math.min(30, Math.max(15, remarks));
        const content = 100 - time - remarks;

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

        timeColumnInput.value = String(time);
        remarksColumnInput.value = String(remarks);
        columnValues.textContent = (
            `${time} / ${content} / ${remarks}`
        );

        writePreference("eod-draft-column-time", time);
        writePreference(
            "eod-draft-column-remarks",
            remarks,
        );
        schedulePagination();
    }

    rows.forEach((row) => {
        const form = row.querySelector("[data-draft-form]");
        const textarea = form.querySelector("[data-auto-grow]");
        const timeInput = form.querySelector("[data-quick-time]");
        const dateButton = form.querySelector("[data-date-button]");

        autoGrow(textarea);

        textarea.addEventListener("input", () => {
            autoGrow(textarea);
            row.dataset.entryFilled = (
                textarea.value.trim() ? "true" : "false"
            );
            scheduleSave(form);
            schedulePagination();
        });

        textarea.addEventListener("focus", () => {
            form.classList.add("has-focus");
        });
        textarea.addEventListener("blur", () => {
            window.setTimeout(() => {
                form.classList.remove("has-focus");
            }, 160);
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
            scheduleSave(form);
            schedulePagination();
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
    });

    workspace
        .querySelectorAll("[data-editor-command]")
        .forEach((button) => {
            button.addEventListener("click", () => {
                button
                    .closest("[data-draft-form]")
                    ?.querySelector("textarea")
                    ?.focus();
            });
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
                    paginateByHeight,
                );
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

    const initialTimeColumn = readPreference(
        "eod-draft-column-time",
        "14",
    );
    const initialRemarksColumn = readPreference(
        "eod-draft-column-remarks",
        "20",
    );
    applyColumnWidths(
        initialTimeColumn,
        initialRemarksColumn,
    );

    timeColumnInput.addEventListener("input", () => {
        applyColumnWidths(
            timeColumnInput.value,
            remarksColumnInput.value,
        );
    });
    remarksColumnInput.addEventListener("input", () => {
        applyColumnWidths(
            timeColumnInput.value,
            remarksColumnInput.value,
        );
    });
    workspace
        .querySelector("[data-reset-columns]")
        .addEventListener("click", () => {
            applyColumnWidths(14, 20);
        });

    const panelHidden = (
        readPreference(
            "eod-draft-side-panel-hidden",
            "false",
        ) === "true"
    );
    workspace.classList.toggle(
        "side-panel-hidden",
        panelHidden,
    );

    workspace
        .querySelector("[data-toggle-side-panel]")
        ?.addEventListener("click", () => {
            const hidden = workspace.classList.toggle(
                "side-panel-hidden",
            );
            writePreference(
                "eod-draft-side-panel-hidden",
                hidden,
            );
            window.requestAnimationFrame(
                paginateByHeight,
            );
        });

    window.addEventListener("resize", () => {
        if (resizeTimer) {
            window.clearTimeout(resizeTimer);
        }
        resizeTimer = window.setTimeout(() => {
            resizeTimer = null;
            paginateByHeight();
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

    window.requestAnimationFrame(paginateByHeight);
})();
