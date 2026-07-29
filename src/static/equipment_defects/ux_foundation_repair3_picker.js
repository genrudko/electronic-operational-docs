(() => {
    "use strict";

    const DATE_SELECTOR = ".defect-manual-date";
    const TIME_SELECTOR = ".defect-manual-time";
    const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
    const MONTH_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
        month: "long",
        year: "numeric",
    });
    const DATE_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
    });

    function node(tag, className, text) {
        const result = document.createElement(tag);
        if (className) result.className = className;
        if (text !== undefined) result.textContent = text;
        return result;
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
            const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
            return {
                year: Number(values.year),
                month: Number(values.month),
                day: Number(values.day),
                hour: Number(values.hour),
                minute: Number(values.minute),
            };
        };
    }

    function dispatchInput(input) {
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function icon(kind) {
        const content = kind === "date"
            ? '<rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M16 3v4M8 3v4M3 10h18"></path><path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"></path>'
            : '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>';
        return `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${content}</svg>`;
    }

    function enhanceInput(input, kind, open) {
        if (input.dataset.customPickerEnhanced === "true") return;
        input.dataset.customPickerEnhanced = "true";

        const field = node("div", "defect-picker-field");
        input.insertAdjacentElement("beforebegin", field);
        field.appendChild(input);

        const trigger = node("button", "defect-picker-trigger");
        trigger.type = "button";
        trigger.innerHTML = icon(kind);
        trigger.title = kind === "date" ? "Выбрать дату" : "Выбрать время";
        trigger.setAttribute(
            "aria-label",
            kind === "date" ? "Открыть календарь" : "Открыть выбор времени",
        );
        trigger.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            open(kind, input, trigger);
        });
        field.appendChild(trigger);
    }

    function createPicker(now) {
        const root = node("div", "defect-picker-root");
        root.hidden = true;
        const backdrop = node("button", "defect-picker-backdrop");
        backdrop.type = "button";
        backdrop.setAttribute("aria-label", "Закрыть выбор даты и времени");
        const panel = node("section", "defect-picker-panel");
        panel.setAttribute("role", "dialog");
        panel.setAttribute("aria-modal", "true");
        panel.setAttribute("aria-labelledby", "defect-picker-title");
        root.append(backdrop, panel);
        document.body.appendChild(root);

        let input = null;
        let trigger = null;
        let selectedDate = null;
        let shownMonth = null;
        let selectedTime = null;

        function close(restoreFocus = true) {
            root.hidden = true;
            panel.replaceChildren();
            document.documentElement.classList.remove("defect-picker-open");
            if (restoreFocus && trigger) trigger.focus();
            input = null;
            trigger = null;
        }

        backdrop.addEventListener("click", () => close());
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && !root.hidden) {
                event.preventDefault();
                close();
            }
        });

        function header(title, subtitle) {
            const result = node("header", "defect-picker-header");
            const heading = node("div", "defect-picker-heading");
            const titleNode = node("h2", "", title);
            titleNode.id = "defect-picker-title";
            heading.append(titleNode, node("p", "", subtitle));
            const closeButton = node("button", "defect-picker-close", "×");
            closeButton.type = "button";
            closeButton.setAttribute("aria-label", "Закрыть");
            closeButton.addEventListener("click", () => close());
            result.append(heading, closeButton);
            return result;
        }

        function footer(apply) {
            const result = node("footer", "defect-picker-footer");
            const cancel = node("button", "defect-picker-button secondary", "Отмена");
            cancel.type = "button";
            cancel.addEventListener("click", () => close());
            const accept = node("button", "defect-picker-button primary", "Применить");
            accept.type = "button";
            accept.addEventListener("click", apply);
            result.append(cancel, accept);
            return result;
        }

        function datesEqual(left, right) {
            return left && right
                && left.year === right.year
                && left.month === right.month
                && left.day === right.day;
        }

        function renderCalendar(body, announcement) {
            body.replaceChildren();
            const navigation = node("div", "defect-calendar-navigation");
            const previous = node("button", "defect-calendar-nav", "‹");
            const next = node("button", "defect-calendar-nav", "›");
            previous.type = "button";
            next.type = "button";
            previous.setAttribute("aria-label", "Предыдущий месяц");
            next.setAttribute("aria-label", "Следующий месяц");
            previous.addEventListener("click", () => {
                const probe = new Date(shownMonth.year, shownMonth.month - 2, 1);
                shownMonth = { year: probe.getFullYear(), month: probe.getMonth() + 1 };
                renderCalendar(body, announcement);
            });
            next.addEventListener("click", () => {
                const probe = new Date(shownMonth.year, shownMonth.month, 1);
                shownMonth = { year: probe.getFullYear(), month: probe.getMonth() + 1 };
                renderCalendar(body, announcement);
            });
            navigation.append(
                previous,
                node(
                    "strong",
                    "defect-calendar-month",
                    MONTH_FORMATTER.format(new Date(shownMonth.year, shownMonth.month - 1, 1)),
                ),
                next,
            );

            const weekdays = node("div", "defect-calendar-weekdays");
            WEEKDAYS.forEach((weekday) => weekdays.appendChild(node("span", "", weekday)));
            const grid = node("div", "defect-calendar-grid");
            grid.setAttribute("role", "grid");

            const first = new Date(shownMonth.year, shownMonth.month - 1, 1);
            const offset = (first.getDay() + 6) % 7;
            const start = new Date(shownMonth.year, shownMonth.month - 1, 1 - offset);
            const today = now();

            for (let index = 0; index < 42; index += 1) {
                const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + index);
                const value = {
                    year: date.getFullYear(),
                    month: date.getMonth() + 1,
                    day: date.getDate(),
                };
                const day = node("button", "defect-calendar-day", String(value.day));
                day.type = "button";
                day.setAttribute("role", "gridcell");
                day.setAttribute("aria-label", DATE_FORMATTER.format(date));
                if (value.month !== shownMonth.month) day.classList.add("is-adjacent");
                if (datesEqual(value, today)) day.classList.add("is-today");
                if (datesEqual(value, selectedDate)) {
                    day.classList.add("is-selected");
                    day.setAttribute("aria-selected", "true");
                }
                day.addEventListener("click", () => {
                    selectedDate = value;
                    shownMonth = { year: value.year, month: value.month };
                    announcement.textContent = DATE_FORMATTER.format(date);
                    renderCalendar(body, announcement);
                });
                grid.appendChild(day);
            }

            const quick = node("div", "defect-picker-quick-actions");
            const todayButton = node("button", "defect-picker-link-button", "Сегодня");
            todayButton.type = "button";
            todayButton.addEventListener("click", () => {
                const value = now();
                selectedDate = { year: value.year, month: value.month, day: value.day };
                shownMonth = { year: value.year, month: value.month };
                announcement.textContent = DATE_FORMATTER.format(
                    new Date(value.year, value.month - 1, value.day),
                );
                renderCalendar(body, announcement);
            });
            quick.appendChild(todayButton);
            body.append(navigation, weekdays, grid, quick);
        }

        function renderDatePicker() {
            const current = parseDate(input.value) || now();
            selectedDate = { year: current.year, month: current.month, day: current.day };
            shownMonth = { year: current.year, month: current.month };
            panel.appendChild(header("Выберите дату", "Календарь · московское время"));
            const announcement = node(
                "p",
                "defect-picker-current-value",
                DATE_FORMATTER.format(
                    new Date(selectedDate.year, selectedDate.month - 1, selectedDate.day),
                ),
            );
            announcement.setAttribute("aria-live", "polite");
            panel.appendChild(announcement);
            const body = node("div", "defect-picker-body defect-calendar-body");
            renderCalendar(body, announcement);
            panel.append(body, footer(() => {
                input.value = `${two(selectedDate.day)}.${two(selectedDate.month)}.${selectedDate.year}`;
                dispatchInput(input);
                close();
            }));
        }

        function buildTimeColumn(label, count, selected, update, display) {
            const column = node("section", "defect-time-column");
            column.appendChild(node("h3", "", label));
            const list = node("div", "defect-time-wheel");
            list.setAttribute("role", "listbox");
            for (let value = 0; value < count; value += 1) {
                const option = node("button", "defect-time-option", two(value));
                option.type = "button";
                option.setAttribute("role", "option");
                if (value === selected) {
                    option.classList.add("is-selected");
                    option.setAttribute("aria-selected", "true");
                }
                option.addEventListener("click", () => {
                    update(value);
                    display.textContent = `${two(selectedTime.hour)}:${two(selectedTime.minute)}`;
                    list.querySelectorAll(".defect-time-option").forEach((candidate) => {
                        const active = Number(candidate.textContent) === value;
                        candidate.classList.toggle("is-selected", active);
                        candidate.setAttribute("aria-selected", active ? "true" : "false");
                    });
                });
                list.appendChild(option);
            }
            column.appendChild(list);
            return { column, list };
        }

        function renderTimePicker() {
            const current = parseTime(input.value) || now();
            selectedTime = { hour: current.hour, minute: current.minute };
            panel.appendChild(header("Выберите время", "Часы и минуты · МСК"));
            const display = node(
                "div",
                "defect-time-picker-display",
                `${two(selectedTime.hour)}:${two(selectedTime.minute)}`,
            );
            display.setAttribute("aria-live", "polite");
            panel.appendChild(display);

            const body = node("div", "defect-picker-body defect-time-picker-body");
            const columns = node("div", "defect-time-columns");
            const hours = buildTimeColumn(
                "Часы",
                24,
                selectedTime.hour,
                (value) => { selectedTime.hour = value; },
                display,
            );
            const minutes = buildTimeColumn(
                "Минуты",
                60,
                selectedTime.minute,
                (value) => { selectedTime.minute = value; },
                display,
            );
            columns.append(hours.column, minutes.column);
            body.appendChild(columns);
            panel.append(body, footer(() => {
                input.value = `${two(selectedTime.hour)}:${two(selectedTime.minute)}`;
                dispatchInput(input);
                close();
            }));
            requestAnimationFrame(() => {
                hours.list.querySelector(".is-selected")?.scrollIntoView({ block: "center" });
                minutes.list.querySelector(".is-selected")?.scrollIntoView({ block: "center" });
            });
        }

        function open(kind, activeInput, activeTrigger) {
            input = activeInput;
            trigger = activeTrigger;
            panel.replaceChildren();
            root.hidden = false;
            document.documentElement.classList.add("defect-picker-open");
            if (kind === "date") renderDatePicker();
            else renderTimePicker();
            requestAnimationFrame(() => panel.querySelector("button")?.focus());
        }

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
