(() => {
    "use strict";

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
                return typeof first === "object" ? String(first.message || first) : String(first);
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

    async function persistDraft(form) {
        window.EODDraftEditor?.syncForm(form);
        setStatus(form, "Сохранение перед регистрацией…", "is-saving");
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            credentials: "same-origin",
            headers: {"X-Requested-With": "XMLHttpRequest"},
        });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
            throw new Error(firstError(payload));
        }
        const version = form.querySelector("[data-draft-version]");
        if (version) version.value = String(payload.version);
        window.EODDraftEditor?.acceptSaved(form, payload);
        setStatus(form, `Сохранено · ${payload.saved_at}`, "is-saved");
    }

    async function registerDraft(button) {
        const form = button.closest("form[data-draft-form]");
        if (!form || button.dataset.busy === "true") return;
        if (!window.confirm(
            "Перенести строку в чистовик? После регистрации исходный текст останется виден, но исправлять его можно будет только новой записью в чистовике."
        )) return;

        button.dataset.busy = "true";
        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = "Регистрация…";
        try {
            await persistDraft(form);
            const response = await fetch(button.formAction, {
                method: "POST",
                body: new FormData(form),
                credentials: "same-origin",
                redirect: "follow",
            });
            if (!response.ok) throw new Error("Не удалось перенести строку в чистовик.");
            window.location.assign(response.url);
        } catch (error) {
            setStatus(form, error.message || "Не удалось зарегистрировать строку.", "is-error");
            button.disabled = false;
            button.textContent = originalText;
            delete button.dataset.busy;
        }
    }

    document.addEventListener("click", (event) => {
        const button = event.target.closest?.("[data-register-draft]");
        if (!button) return;
        event.preventDefault();
        void registerDraft(button);
    });
})();
