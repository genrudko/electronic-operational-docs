(() => {
    "use strict";

    const ICON_SPRITE = "/static/system/icons.svg";

    function journalBasePath() {
        const match = window.location.pathname.match(/^(\/operations\/journal\/\d+\/)/);
        return match ? match[1] : "";
    }

    function icon(symbol) {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("class", "ui-icon");
        svg.setAttribute("aria-hidden", "true");
        const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
        use.setAttribute("href", `${ICON_SPRITE}#${symbol}`);
        svg.append(use);
        return svg;
    }

    function addRegisteredEntryLinks() {
        const base = journalBasePath();
        if (!base) return;
        document.querySelectorAll(".approved-journal-row").forEach((row) => {
            if (row.querySelector("[data-opj-lifecycle-link]")) return;
            const numberText = row.querySelector(".approved-journal-date-time small")?.textContent || "";
            const match = numberText.match(/(\d+)/);
            const message = row.querySelector(".approved-journal-message");
            if (!match || !message) return;

            const link = document.createElement("a");
            link.className = "opj-lifecycle-inline-link screen-only";
            link.href = `${base}entries/${match[1]}/lifecycle/`;
            link.dataset.opjLifecycleLink = "";
            link.append(icon("icon-history"));
            const label = document.createElement("span");
            label.textContent = "История и действия";
            link.append(label);
            message.append(link);
        });
    }

    function addDraftRegistrationActions() {
        const base = journalBasePath();
        if (!base || !window.location.pathname.endsWith("/shift/")) return;
        document.querySelectorAll("[data-draft-card]").forEach((card) => {
            if (card.querySelector("[data-register-draft]")) return;
            const draftId = card.dataset.draftId;
            const toolbar = card.querySelector(".draft-row-action-toolbar");
            if (!draftId || !toolbar) return;

            const separator = document.createElement("span");
            separator.className = "draft-row-action-separator";
            separator.setAttribute("aria-hidden", "true");

            const button = document.createElement("button");
            button.type = "submit";
            button.className = "draft-row-action opj-register-draft-action";
            button.formAction = `${base}shift/drafts/${draftId}/register/`;
            button.title = "Зарегистрировать неизменяемую запись";
            button.setAttribute("aria-label", "Зарегистрировать неизменяемую запись");
            button.dataset.registerDraft = "";
            button.append(icon("icon-check"));
            button.addEventListener("click", (event) => {
                const confirmed = window.confirm(
                    "Зарегистрировать черновик как неизменяемую запись?"
                );
                if (!confirmed) event.preventDefault();
            });

            toolbar.prepend(separator);
            toolbar.prepend(button);
        });
    }

    function confirmIrreversibleActions() {
        document.querySelectorAll("[data-opj-confirm]").forEach((form) => {
            form.addEventListener("submit", (event) => {
                const question = form.dataset.opjConfirm || "Зарегистрировать неизменяемое событие?";
                if (!window.confirm(question)) event.preventDefault();
            });
        });
    }

    function activateActionTabs() {
        const buttons = Array.from(document.querySelectorAll("[data-opj-action-tab]"));
        const panels = Array.from(document.querySelectorAll("[data-opj-action-panel]"));
        if (!buttons.length || !panels.length) return;

        const select = (name) => {
            buttons.forEach((button) => {
                const active = button.dataset.opjActionTab === name;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-selected", active ? "true" : "false");
            });
            panels.forEach((panel) => {
                panel.hidden = panel.dataset.opjActionPanel !== name;
            });
        };
        buttons.forEach((button) => {
            button.addEventListener("click", () => select(button.dataset.opjActionTab));
        });
        select(buttons[0].dataset.opjActionTab);
    }

    document.addEventListener("DOMContentLoaded", () => {
        addRegisteredEntryLinks();
        addDraftRegistrationActions();
        confirmIrreversibleActions();
        activateActionTabs();
    });
})();
