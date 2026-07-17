(() => {
    "use strict";

    const workspace = document.querySelector("[data-draft-workspace]");
    if (!workspace) {
        return;
    }

    const delay = Number.parseInt(
        workspace.dataset.autosaveDelay || "700",
        10,
    );
    const timers = new WeakMap();
    const controllers = new WeakMap();

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

    function updateVersion(form, version) {
        const versionInput = form.querySelector("[data-draft-version]");
        const versionLabel = form
            .closest("[data-draft-card]")
            ?.querySelector("[data-version-label]");
        if (versionInput) {
            versionInput.value = String(version);
        }
        if (versionLabel) {
            versionLabel.textContent = String(version);
        }
    }

    async function save(form) {
        const previousController = controllers.get(form);
        if (previousController) {
            previousController.abort();
        }
        const controller = new AbortController();
        controllers.set(form, controller);
        setStatus(form, "Сохраняется…", "is-saving");

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
                setStatus(
                    form,
                    "Конфликт: запись уже изменена. Обнови страницу.",
                    "is-conflict",
                );
                form.dataset.conflict = "true";
                return;
            }
            if (!response.ok || !payload.ok) {
                setStatus(
                    form,
                    "Не сохранено. Проверь введённые данные.",
                    "is-error",
                );
                return;
            }

            updateVersion(form, payload.version);
            delete form.dataset.conflict;
            setStatus(
                form,
                `Сохранено ${payload.saved_at}`,
                "is-saved",
            );
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }
            setStatus(
                form,
                "Нет связи с сервером. Изменения пока не сохранены.",
                "is-error",
            );
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
        setStatus(form, "Есть несохранённые изменения", "is-dirty");
        const timer = window.setTimeout(() => {
            timers.delete(form);
            void save(form);
        }, delay);
        timers.set(form, timer);
    }

    document.querySelectorAll("[data-draft-form]").forEach((form) => {
        form.addEventListener("input", () => scheduleSave(form));
        form.addEventListener("change", () => scheduleSave(form));
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            const timer = timers.get(form);
            if (timer) {
                window.clearTimeout(timer);
                timers.delete(form);
            }
            void save(form);
        });
    });

    window.addEventListener("beforeunload", (event) => {
        const hasPending = document.querySelector(
            ".draft-save-status.is-dirty, "
            + ".draft-save-status.is-saving, "
            + ".draft-save-status.is-error",
        );
        if (!hasPending) {
            return;
        }
        event.preventDefault();
        event.returnValue = "";
    });
})();
