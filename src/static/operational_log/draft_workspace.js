(() => {
    "use strict";
    const workspace = document.querySelector("[data-draft-workspace]");
    if (!workspace) return;

    const delay = Number.parseInt(workspace.dataset.autosaveDelay || "700", 10);
    const pageSize = Number.parseInt(workspace.dataset.pageSize || "8", 10);
    const timers = new WeakMap();
    const controllers = new WeakMap();
    const rows = Array.from(document.querySelectorAll("[data-draft-card]"));
    const pageLabel = document.querySelector("[data-page-label]");
    const prev = document.querySelector("[data-page-prev]");
    const next = document.querySelector("[data-page-next]");
    const search = document.querySelector("[data-draft-search]");
    const filter = document.querySelector("[data-draft-filter]");
    let page = 0;
    let mode = localStorage.getItem("eod-draft-view-mode") || "single";

    function setStatus(form, text, state) {
        const node = form.querySelector("[data-save-status]");
        if (!node) return;
        node.textContent = text;
        node.className = `draft-save-status ${state}`;
    }

    function normalizeTime(value) {
        const digits = value.replace(/\D/g, "").slice(0, 4);
        if (!digits) return "";
        const value4 = digits.padStart(4, "0");
        const h = Number(value4.slice(0, 2));
        const m = Number(value4.slice(2, 4));
        if (h > 23 || m > 59) return null;
        return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
    }

    function normalizeDate(value) {
        const digits = value.replace(/\D/g, "").slice(0, 8);
        if (![4, 6, 8].includes(digits.length)) return null;
        const now = new Date();
        const d = digits.slice(0, 2);
        const m = digits.slice(2, 4);
        const y = digits.length === 4 ? String(now.getFullYear()) : digits.length === 6 ? `20${digits.slice(4)}` : digits.slice(4);
        const parsed = new Date(`${y}-${m}-${d}T00:00:00`);
        if (Number.isNaN(parsed.getTime()) || parsed.getDate() !== Number(d) || parsed.getMonth() + 1 !== Number(m)) return null;
        return `${d}.${m}.${y}`;
    }

    function syncDateTime(form) {
        const hidden = form.querySelector("[data-event-at]");
        const time = form.querySelector("[data-quick-time]");
        const date = form.querySelector("[data-date-button]");
        const nt = normalizeTime(time.value);
        const nd = normalizeDate(date.dataset.currentDate || "");
        if (!nt || !nd) return false;
        time.value = nt;
        const [d, m, y] = nd.split(".");
        hidden.value = `${y}-${m}-${d}T${nt}`;
        date.dataset.currentDate = nd;
        date.textContent = `${d}.${m}`;
        return true;
    }

    function autoGrow(area) {
        area.style.height = "auto";
        area.style.height = `${Math.max(38, area.scrollHeight)}px`;
    }

    async function save(form) {
        if (!syncDateTime(form)) {
            setStatus(form, "Некорректное время", "is-error");
            return;
        }
        controllers.get(form)?.abort();
        const controller = new AbortController();
        controllers.set(form, controller);
        setStatus(form, "…", "is-saving");
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                credentials: "same-origin",
                headers: {"X-Requested-With": "XMLHttpRequest"},
                signal: controller.signal,
            });
            const data = await response.json();
            if (response.status === 409 && data.conflict) {
                form.dataset.conflict = "true";
                setStatus(form, "Конфликт", "is-conflict");
                return;
            }
            if (!response.ok || !data.ok) {
                setStatus(form, "Не сохранено", "is-error");
                return;
            }
            form.querySelector("[data-draft-version]").value = String(data.version);
            form.querySelector("[data-version-label]").textContent = String(data.version);
            delete form.dataset.conflict;
            setStatus(form, `✓ ${data.saved_at}`, "is-saved");
        } catch (error) {
            if (error.name !== "AbortError") setStatus(form, "Нет связи", "is-error");
        }
    }

    function schedule(form) {
        if (form.dataset.conflict === "true") return;
        if (timers.get(form)) clearTimeout(timers.get(form));
        setStatus(form, "●", "is-dirty");
        timers.set(form, setTimeout(() => save(form), delay));
    }

    function matchingRows() {
        const q = (search?.value || "").trim().toLowerCase();
        const f = filter?.value || "all";
        return rows.filter((row) => {
            const filled = row.dataset.entryFilled === "true";
            return (!q || row.textContent.toLowerCase().includes(q))
                && (f === "all" || (f === "filled" && filled) || (f === "empty" && !filled));
        });
    }

    function renderPages() {
        const visible = matchingRows();
        const perScreen = mode === "spread" ? 2 : 1;
        const totalPages = Math.max(1, Math.ceil(visible.length / pageSize));
        const maxPage = Math.max(0, Math.ceil(totalPages / perScreen) - 1);
        page = Math.min(page, maxPage);
        rows.forEach((row) => row.hidden = true);
        const start = page * perScreen * pageSize;
        visible.slice(start, start + perScreen * pageSize).forEach((row) => row.hidden = false);
        workspace.dataset.viewMode = mode;
        pageLabel.textContent = mode === "spread"
            ? `Разворот ${page + 1} из ${maxPage + 1}`
            : `Страница ${page + 1} из ${maxPage + 1}`;
        prev.disabled = page === 0;
        next.disabled = page === maxPage;
    }

    document.querySelectorAll("[data-draft-form]").forEach((form) => {
        const area = form.querySelector("[data-auto-grow]");
        const time = form.querySelector("[data-quick-time]");
        const date = form.querySelector("[data-date-button]");
        autoGrow(area);
        area.addEventListener("input", () => {
            autoGrow(area);
            form.closest("[data-draft-card]").dataset.entryFilled = area.value.trim() ? "true" : "false";
            schedule(form);
        });
        area.addEventListener("focus", () => form.classList.add("has-focus"));
        area.addEventListener("blur", () => setTimeout(() => form.classList.remove("has-focus"), 160));
        time.addEventListener("focus", () => time.select());
        time.addEventListener("blur", () => {
            const normalized = normalizeTime(time.value);
            if (normalized) {
                time.value = normalized;
                schedule(form);
            } else {
                setStatus(form, "Некорректное время", "is-error");
            }
        });
        date.addEventListener("click", () => {
            const entered = prompt("Дата: 1707, 170726 или 17072026", date.dataset.currentDate || "");
            if (entered === null) return;
            const normalized = normalizeDate(entered);
            if (!normalized) {
                setStatus(form, "Некорректная дата", "is-error");
                return;
            }
            date.dataset.currentDate = normalized;
            date.textContent = normalized.slice(0, 5);
            schedule(form);
        });
        form.addEventListener("submit", (event) => {
            if (event.submitter?.formAction && event.submitter.formAction !== form.action) return;
            event.preventDefault();
            save(form);
        });
    });

    document.querySelectorAll("[data-editor-command]").forEach((button) => {
        button.addEventListener("click", () => button.closest("form").querySelector("textarea").focus());
    });
    document.querySelectorAll("[data-view-mode]").forEach((button) => {
        const activate = () => {
            mode = button.dataset.viewMode;
            localStorage.setItem("eod-draft-view-mode", mode);
            document.querySelectorAll("[data-view-mode]").forEach((item) => item.classList.toggle("is-active", item.dataset.viewMode === mode));
            page = 0;
            renderPages();
        };
        if (button.dataset.viewMode === mode) button.classList.add("is-active");
        button.addEventListener("click", activate);
    });
    prev.addEventListener("click", () => { page = Math.max(0, page - 1); renderPages(); });
    next.addEventListener("click", () => { page += 1; renderPages(); });
    search.addEventListener("input", () => { page = 0; renderPages(); });
    filter.addEventListener("change", () => { page = 0; renderPages(); });

    const panel = document.querySelector("[data-shift-panel]");
    document.querySelector("[data-toggle-shift-panel]")?.addEventListener("click", () => { panel.hidden = false; });
    document.querySelector("[data-close-shift-panel]")?.addEventListener("click", () => { panel.hidden = true; });

    renderPages();
    addEventListener("beforeunload", (event) => {
        if (!document.querySelector(".draft-save-status.is-dirty, .draft-save-status.is-saving, .draft-save-status.is-error")) return;
        event.preventDefault();
        event.returnValue = "";
    });
})();
