(() => {
    "use strict";

    const MOSCOW_TIME_ZONE = "Europe/Moscow";

    function pad(value) {
        return String(value).padStart(2, "0");
    }

    function partsInMoscow(date) {
        const parts = new Intl.DateTimeFormat("en-CA", {
            timeZone: MOSCOW_TIME_ZONE,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hourCycle: "h23",
        }).formatToParts(date);
        const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
        return {
            date: `${values.year}-${values.month}-${values.day}`,
            time: `${values.hour}:${values.minute}`,
        };
    }

    function formatMoscow(date) {
        return new Intl.DateTimeFormat("ru-RU", {
            timeZone: MOSCOW_TIME_ZONE,
            dateStyle: "short",
            timeStyle: "medium",
        }).format(date);
    }

    function formatDevice(date) {
        return new Intl.DateTimeFormat("ru-RU", {
            dateStyle: "short",
            timeStyle: "medium",
        }).format(date);
    }

    let authoritativeNow = () => new Date();

    function setTimeSensitiveFormsBlocked(blocked) {
        document.querySelectorAll("[data-time-sensitive-form]").forEach((form) => {
            form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach((button) => {
                if (blocked) {
                    if (!button.disabled) {
                        button.dataset.timeTrustDisabled = "true";
                        button.disabled = true;
                    }
                } else if (button.dataset.timeTrustDisabled === "true") {
                    button.disabled = false;
                    delete button.dataset.timeTrustDisabled;
                }
            });
            form.classList.toggle("is-time-blocked", blocked);
        });
    }

    function initTimeTrust() {
        const widgets = [...document.querySelectorAll("[data-defect-time-trust]")];
        if (!widgets.length) {
            return;
        }
        const source = widgets[0];
        const serverEpoch = Number(source.dataset.serverEpoch) * 1000;
        const maxDrift = Number(source.dataset.maxDriftSeconds || 180) * 1000;
        const loadedAt = performance.now();
        if (!Number.isFinite(serverEpoch)) {
            return;
        }

        authoritativeNow = () => new Date(serverEpoch + (performance.now() - loadedAt));

        const update = () => {
            const serverNow = authoritativeNow();
            const deviceNow = new Date();
            const drift = Math.abs(deviceNow.getTime() - serverNow.getTime());
            const blocked = drift > maxDrift;

            widgets.forEach((widget) => {
                const serverClock = widget.querySelector("[data-defect-server-clock]");
                const deviceClock = widget.querySelector("[data-defect-device-clock]");
                const warning = widget.querySelector("[data-defect-time-warning]");
                const ok = widget.querySelector("[data-defect-time-ok]");
                if (serverClock) serverClock.textContent = formatMoscow(serverNow);
                if (deviceClock) deviceClock.textContent = formatDevice(deviceNow);
                if (warning) warning.hidden = !blocked;
                if (ok) ok.hidden = blocked;
                widget.classList.toggle("is-warning", blocked);
            });
            setTimeSensitiveFormsBlocked(blocked);
        };

        update();
        window.setInterval(update, 1000);
    }

    function enhanceDateTimeInput(input) {
        if (input.dataset.enhanced === "true") return;
        input.dataset.enhanced = "true";

        const control = document.createElement("div");
        control.className = "defect-datetime-control";

        const dateGroup = document.createElement("label");
        dateGroup.className = "defect-datetime-part";
        dateGroup.innerHTML = "<span>Дата</span>";
        const dateInput = document.createElement("input");
        dateInput.type = "date";
        dateInput.className = "defect-date-part";
        dateInput.setAttribute("aria-label", `${input.getAttribute("aria-label") || "Дата и время"}: дата`);
        dateGroup.appendChild(dateInput);

        const timeGroup = document.createElement("label");
        timeGroup.className = "defect-datetime-part";
        timeGroup.innerHTML = "<span>Время (МСК)</span>";
        const timeInput = document.createElement("input");
        timeInput.type = "time";
        timeInput.step = "60";
        timeInput.className = "defect-time-part";
        timeInput.setAttribute("aria-label", `${input.getAttribute("aria-label") || "Дата и время"}: время`);
        timeGroup.appendChild(timeInput);

        const syncFromNative = () => {
            const [dateValue = "", timeValue = ""] = (input.value || "").split("T");
            dateInput.value = dateValue;
            timeInput.value = timeValue.slice(0, 5);
        };
        const syncToNative = () => {
            input.value = dateInput.value && timeInput.value ? `${dateInput.value}T${timeInput.value}` : "";
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
        };

        dateInput.addEventListener("change", syncToNative);
        timeInput.addEventListener("change", syncToNative);
        control.append(dateGroup, timeGroup);

        if (input.dataset.allowServerNow === "true") {
            const nowButton = document.createElement("button");
            nowButton.type = "button";
            nowButton.className = "defect-now-button";
            nowButton.textContent = "Системное время";
            nowButton.addEventListener("click", () => {
                const parts = partsInMoscow(authoritativeNow());
                dateInput.value = parts.date;
                timeInput.value = parts.time;
                syncToNative();
            });
            control.appendChild(nowButton);
        }

        syncFromNative();
        input.classList.add("defect-datetime-native--enhanced");
        input.insertAdjacentElement("afterend", control);
    }

    function initDateTimeControls() {
        document.querySelectorAll("input[data-defect-datetime]").forEach(enhanceDateTimeInput);
    }

    function compareItems(a, b, mode) {
        const numberA = Number(a.dataset.sortNumber || 0);
        const numberB = Number(b.dataset.sortNumber || 0);
        const eventA = Number(a.dataset.sortEvent || 0);
        const eventB = Number(b.dataset.sortEvent || 0);
        const equipmentA = a.dataset.sortEquipment || "";
        const equipmentB = b.dataset.sortEquipment || "";
        const statusOrder = { REGISTERED: 0, IN_PROGRESS: 1, RESOLVED: 2, CLOSED: 3 };
        switch (mode) {
            case "event-asc": return eventA - eventB;
            case "number-desc": return numberB - numberA;
            case "number-asc": return numberA - numberB;
            case "equipment-asc": return equipmentA.localeCompare(equipmentB, "ru");
            case "status-asc": return (statusOrder[a.dataset.status] ?? 99) - (statusOrder[b.dataset.status] ?? 99) || eventB - eventA;
            case "event-desc":
            default: return eventB - eventA;
        }
    }

    function sortContainer(container, mode) {
        const items = [...container.querySelectorAll(":scope > [data-defect-sortable-item]")];
        items.sort((a, b) => compareItems(a, b, mode));
        items.forEach((item) => container.appendChild(item));
    }

    function initSorting() {
        const select = document.querySelector("[data-defect-sort]");
        if (!select) return;
        const stored = window.sessionStorage.getItem("eod-defect-sort");
        if (stored && [...select.options].some((option) => option.value === stored)) {
            select.value = stored;
        }
        const apply = () => {
            const mode = select.value;
            document.querySelectorAll("[data-defect-sort-container]").forEach((container) => sortContainer(container, mode));
            window.sessionStorage.setItem("eod-defect-sort", mode);
        };
        select.addEventListener("change", apply);
        apply();
    }

    document.addEventListener("DOMContentLoaded", () => {
        initTimeTrust();
        initDateTimeControls();
        initSorting();
    });
})();
