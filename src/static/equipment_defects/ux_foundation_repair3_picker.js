(() => {
    "use strict";

    const DATE_SELECTOR = ".defect-manual-date";
    const TIME_SELECTOR = ".defect-manual-time";
    const MONTH_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
        month: "long",
        year: "numeric",
    });
    const FULL_DATE_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
    });
    const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function two(value) {
        return String(value).padStart(2, "0");
    }

    function parseDate(value) {
        const match = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(String(value || ""));
        if (!match) return null;
        const day = Number(match[1]);
        const month = Number(match[2]);
        const year = Number(match[3]);
        const probe = new Date(year, month - 1, day);
        if (
            probe.getFullYear() !== year
            || probe.getMonth() !== month - 1
            || probe.getDate() !== day
        ) return null;
        return { year, month, day };
    }

    function parseTime(value) {
        const match = /^(\d{2}):(\d{2})$/.exec(String(value || ""));
        if (!match) return null;
        const hour = Number(match[1]);
        const minute = Number(match[2]);
        if (hour > 23 || minute > 59) return null;
        return { hour, minute };
    }

    function moscowNowFactory() {
        const trust = document.querySelector("[data-defect-time-trust]");
        const epoch = Number(trust?.dataset.serverEpoch) * 1000;
        const loadedAt = performance.now();
        const current = () => Number.isFinite(epoch)
            ? new Date(epoch + (performance.now() - loadedAt))
            : new Date();

        return () => {
            const parts = new Intl.DateTimeFormat("ru-RU", {
                timeZone: "Europe/Moscow",
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                hourCycle: "h23",
            }).formatToParts(current());
            const map = Object.fromEntries(parts.map((part) => [part.type, part.value]));
            return {
                year: Number(map.year),
                month: Number(map.month),
                day: Number(map.day),
                hour: Number(map.hour),
                minute: Number(map.minute),
            };
        };
    }

    function svgIcon(kind) {
        const paths = kind === "date"
            ? '<rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M16 3v4M8 3v4M3 10h18"></path><path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"></path>'
            : '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>';
        return `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${paths}</svg>`;
    }

    function dispatchInput(input) {
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function enhanceInput(input, kind, openPicker) {
        if (input.dataset.customPickerEnhanced === "true") return;
        input.dataset.customPickerEnhanced = "true";

        const field = element("div", "defect-picker-field");
        input.insertAdjacentElement("beforebegin", field);
        field.appendChild(input);

        const trigger = element("button", "defect-picker-trigger");
        trigger.type = "button";
        trigger.innerHTML = svgIcon(kind);
        trigger.setAttribute(
            "aria-label",
            kind === "date" ? "Открыть календарь" : "Открыть выбор времени",
        );
        trigger.title = kind === "date" ? "Выбрать дату" : "Выбрать время";
        trigger.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            openPicker(kind, input, trigger);
        });
        field.appendChild(trigger);
    }

    function createPicker(now) {
        const root = element("div", "defect-picker-root");
        root.hidden = true;
        const backdrop = element("button", "defect-picker-backdrop");
        backdrop.type = "button";
        backdrop.setAttribute("aria-label", "Закрыть выбор даты и времени");
        const panel = element("section", "defect-picker-panel");
        panel.setAttribute("role", "dialog");
        panel.setAttribute("aria-modal", "true");
        panel.setAttribute("aria-labelledby", "defect-picker-title");
        root.append(backdrop, panel);
        document.body.appendChild(root);

        let activeInput = null;
        let activeTrigger = null;
        let activeKind = null;
        let dateState = null;
        let monthState = null;
        let timeState = null;

        const close = (restoreFocus = true) => {
            root.hidden = true;
            panel.replaceChildren();
            document.documentElement.classList.remove("defect-picker-open");
            if (restoreFocus && activeTrigger) activeTrigger.focus();
            activeInput = null;
            activeTrigger = null;
            activeKind = null;
        };

        backdrop.addEventListener("click", () => close());
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && !root.hidden) {
                event.preventDefault();
                close();
            }
        });

        function makeHeader(titleText, subtitleText) {
            const header = element("header", "defect-picker-header");
            const heading = element("div", "defect-picker-heading");
            const title = element("h2", "", titleText);
            title.id = "defect-picker-title";
            heading.append(title, element("p", "", subtitleText));
            const closeButton = element("button", "defect-picker-close", "×");
            closeButton.type = "button";
            closeButton.setAttribute("aria-label", "Закрыть");
            closeButton.addEventListener("click", () => close());
            header.append(heading, closeButton);
            return header;
        }

        function makeFooter(apply) {
            const footer = element("footer", "defect-picker-footer");
            const cancel = element("button", "defect-picker-button secondary", "Отмена");
            cancel.type = "button";
            cancel.addEventListener("click", () => close());
            const accept = element("button", "defect-picker-button primary", "Применить");
            accept.type = "button";
            accept.addEventListener("click", apply);
            footer.append(cancel, accept);
            return footer;
        }

        function sameDate(left, right) {
            return left && right
                && left.year === right.year
                && left.month === right.month
                && left.day === right.day;
        }

        function renderCalendar(body, announcement) {
            body.replaceChildren();
            const navigation = element("div", "defect-calendar-navigation");
            const previous = element("button", "defect-calendar-nav", "‹");
            previous.type = "button";
            previous.setAttribute("aria-label", "Предыдущий месяц");
            const monthLabel = element(
                "strong",
                "defect-calendar-month",
                MONTH_FORMATTER.format(new Date(monthState.year, monthState.month - 1, 1)),
            );
            const next = element("button", "defect-calendar-nav", "›");
            next.type = "button";
            next.setAttribute("aria-label", "Следующий месяц");
            previous.addEventListener("click", () => {
                const probe = new Date(monthState.year, monthState.month - 2, 1);
                monthState = { year: probe.getFullYear(), month: probe.getMonth() + 1 };
                renderCalendar(body, announcement);
            });
            next.addEventListener("click", () => {
                const probe = new Date(monthState.year, monthState.month, 1);
                monthState = { year: probe.getFullYear(), month: probe.getMonth() + 1 };
                renderCalendar(body, announcement);
            });
            navigation.append(previous, monthLabel, next);

            const weekdays = element("div", "defect-calendar-weekdays");
            WEEKDAYS.forEach((weekday) => weekdays.appendChild(element("span", "", weekday)));

            const grid = element("div", "defect-calendar-grid");
            grid.setAttribute("role", "grid");
            const first = new Date(monthState.year, monthState.month - 1, 1);
            const mondayIndex = (first.getDay() + 6) % 7;
            const start = new Date(monthState.year, monthState.month - 1, 1 - mondayIndex);
            const today = now();

            for (let index = 0; index < 42; index += 1) {
                const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + index);
                const value = {
                    year: date.getFullYear(),
                    month: date.getMonth() + 1,
                    day: date.getDate(),
                };
                const button = element("button", "defect-calendar-day", String(value.day));
                button.type = "button";
                button.setAttribute("role", "gridcell");
                button.setAttribute("aria-label", FULL_DATE_FORMATTER.format(date));
                if (value.month !== monthState.month) button.classList.add("is-adjacent");
                if (sameDate(value, today)) button.classList.add("is-today");
                if (sameDate(value, dateState)) {
                    button.classList.add("is-selected");
                    button.setAttribute("aria-selected", "true");
                }
                button.addEventListener("click", () => {
                    dateState = value;
                    monthState = { year: value.year, month: value.month };
                    announcement.textContent = FULL_DATE_FORMATTER.format(date);
                    renderCalendar(body, announcement);
                });
                grid.appendChild(button);
            }

            const quick = element("div", "defect-picker-quick-actions");
            const todayButton = element("button", "defect-picker-link-button", "Сегодня");
            todayButton.type = "button";
            todayButton.addEventListener("click", () => {
                dateState = { year: today.year, month: today.month, day: today.day };
                monthState = { year: today.year, month: today.month };
                announcement.textContent = FULL_DATE_FORMATTER.format(
                    new Date(today.year, today.month - 1, today.day),
                );
                renderCalendar(body, announcement);
            });
            quick.appendChild(todayButton);
            body.append(navigation, weekdays, grid, quick);
        }

        function renderDatePicker() {
            const current = parseDate(activeInput.value) || now();
            dateState = { year: current.year, month: current.month, day: current.day };
            monthState = { year: current.year, month: current.month };

            panel.appendChild(makeHeader("Выберите дату", "Календарь · московское время"));
            const announcement = element(
                "p",
                "defect-picker-current-value",
                FULL_DATE_FORMATTER.format(
                    new Date(dateState.year, dateState.month - 1, dateState.day),
                ),
            );
            announcement.setAttribute("aria-live", "polite");
            panel.appendChild(announcement);
            const body = element("div", "defect-picker-body defect-calendar-body");
            renderCalendar(body, announcement);
            panel.appendChild(body);
            panel.appendChild(makeFooter(() => {
                activeInput.value = `${two(dateState.day)}.${two(dateState.month)}.${dateState.year}`;
                dispatchInput(activeInput);
                close();
            }));
        }

        function renderTimePicker() {
            const current = parseTime(activeInput.value) || now();
            timeState = { hour: current.hour, minute: current.minute };

            panel.appendChild(makeHeader("Выберите время", "Часы и минуты · МСК"));
            const display = element(
                "div",
                "defect-time-picker-display",
                `${two(timeState.hour)}:${two(timeState.minute)}`,
            );
            display.setAttribute("aria-live", "polite");
            panel.appendChild(display);

            const body = element("div", "defect-picker-body defect-time-picker-body");
            const columns = element("div", "defect-time-columns");

            const buildColumn = (label, count, selected, setter) => {
                const column = element("section", "defect-time-column");
                column.appendChild(element("h3", "", label));
                const list = element("div", "defect-time-wheel");
                list.setAttribute("role", "listbox");
                for (let value = 0; value < count; value += 1) {
                    const button = element("button", "defect-time-option", two(value));
                    button.type = "button";
                    button.setAttribute("role", "option");
                    if (value === selected) {
                        button.classList.add("is-selected");
                        button.setAttribute("aria-selected", "true");
                    }
                    button.addEventListener("click", () => {
                        setter(value);
                        display.textContent = `${two(timeState.hour)}:${two(timeState.minute)}`;
                        list.querySelectorAll(".defect-time-option").forEach((option) => {
                            const active = Number(option.textContent) === value;
                            option.classList.toggle("is-selected", active);
                            option.setAttribute("aria-selected", active ? "true" : "false");
                        });
                    });
                    list.appendChild(button);
                }
                column.appendChild(list);
                return { column, list };
            };

            const hours = buildColumn("Часы", 24, timeState.hour, (value) => {
                timeState.hour = value;
            });
            const minutes = buildColumn("Минуты", 60, timeState.minute, (value) => {
                timeState.minute = value;
            });
            columns.append(hours.column, minutes.column);

            const quick = element("div", "defect-picker-quick-actions");
            const nowButton = element("button", "defect-picker-link-button", "Сейчас по МСК");
            nowButton.type = "button";
            nowButton.addEventListener("click", () => {
                const currentNow = now();
                timeState = { hour: currentNow.hour, minute: currentNow.minute };
                renderTimePickerFresh();
            });
            quick.appendChild(nowButton);
            body.append(columns, quick);
            panel.appendChild(body);
            panel.appendChild(makeFooter(() => {
                activeInput.value = `${two(timeState.hour)}:${two(timeState.minute)}`;
                dispatchInput(activeInput);
                close();
            }));

            requestAnimationFrame(() => {
                hours.list.querySelector(".is-selected")?.scrollIntoView({ block: "center" });
                minutes.list.querySelector(".is-selected")?.scrollIntoView({ block: "center" });
            });
        }

        function renderTimePickerFresh() {
            panel.replaceChildren();
            renderTimePicker();
        }

        const open = (kind, input, trigger) => {
            activeKind = kind;
            activeInput = input;
            activeTrigger = trigger;
            panel.replaceChildren();
            root.hidden = false;
            document.documentElement.classList.add("defect-picker-open");
            if (activeKind === "date") renderDatePicker();
            else renderTimePicker();
            requestAnimationFrame(() => panel.querySelector("button")?.focus());
        };

        return { open };
    }

    document.addEventListener("DOMContentLoaded", () => {
        const dateInputs = [...document.querySelectorAll(DATE_SELECTOR)];
        const timeInputs = [...document.querySelectorAll(TIME_SELECTOR)];
        if (!dateInputs.length && !timeInputs.length) return;
        const picker = createPicker(moscowNowFactory());
        dateInputs.forEach((input) => enhanceInput(input, "date", picker.open));
        timeInputs.forEach((input) => enhanceInput(input, "time", picker.open));
    });
})();
