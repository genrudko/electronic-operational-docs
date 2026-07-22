(() => {
    "use strict";

    const triggers = document.querySelectorAll("[data-power-system-preview-trigger]");
    for (const trigger of triggers) {
        trigger.addEventListener("click", (event) => {
            if (
                event instanceof MouseEvent
                && (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)
            ) {
                return;
            }
            const container = trigger.closest("[data-power-system-preview-container]") || trigger.parentElement;
            if (trigger.dataset.previewSubmitting === "true") {
                event.preventDefault();
                return;
            }

            trigger.dataset.previewSubmitting = "true";
            trigger.setAttribute("aria-busy", "true");
            trigger.setAttribute("aria-disabled", "true");
            if (container) {
                container.setAttribute("aria-busy", "true");
            }

            if (trigger instanceof HTMLButtonElement) {
                trigger.dataset.originalLabel = trigger.textContent || "";
                trigger.textContent = "Формируется предварительная проверка…";
            } else if (trigger instanceof HTMLAnchorElement) {
                trigger.dataset.originalLabel = trigger.textContent || "";
                trigger.textContent = "Формируется предварительная проверка…";
            } else if (trigger instanceof HTMLInputElement) {
                trigger.dataset.originalLabel = trigger.value;
                trigger.value = "Формируется предварительная проверка…";
            }

            const progress = container?.querySelector("[data-power-system-preview-progress]");
            if (progress) {
                progress.hidden = false;
            }

            if (trigger instanceof HTMLAnchorElement) {
                event.preventDefault();
                const destination = trigger.href;
                window.setTimeout(() => window.location.assign(destination), 50);
            }
        });
    }
})();
