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

(() => {
    "use strict";

    const filenameFromDisposition = (value, fallback) => {
        const utf8Match = value.match(/filename\*=UTF-8''([^;]+)/i);
        if (utf8Match) {
            try {
                return decodeURIComponent(utf8Match[1]);
            } catch (_error) {
                return fallback;
            }
        }
        const basicMatch = value.match(/filename="?([^";]+)"?/i);
        return basicMatch ? basicMatch[1] : fallback;
    };

    const trigger = document.querySelector("[data-power-system-snapshot-trigger]");
    if (!(trigger instanceof HTMLAnchorElement)) {
        return;
    }

    trigger.addEventListener("click", async (event) => {
        if (
            event instanceof MouseEvent
            && (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)
        ) {
            return;
        }
        event.preventDefault();
        if (trigger.dataset.snapshotLoading === "true") {
            return;
        }

        const container = trigger.closest("[data-power-system-snapshot-container]");
        const progress = container?.querySelector("[data-power-system-snapshot-progress]");
        const originalLabel = trigger.textContent || "Скачать канонический JSON";
        trigger.dataset.snapshotLoading = "true";
        trigger.setAttribute("aria-busy", "true");
        trigger.setAttribute("aria-disabled", "true");
        trigger.textContent = "Подготавливается канонический JSON…";
        if (container) {
            container.setAttribute("aria-busy", "true");
        }
        if (progress instanceof HTMLElement) {
            progress.hidden = false;
            progress.textContent = "Сервер формирует точный канонический файл…";
        }

        try {
            const response = await fetch(trigger.href, {
                cache: "no-store",
                credentials: "same-origin",
                headers: {"X-Requested-With": "XMLHttpRequest"},
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const blob = await response.blob();
            const fallback = "power-system-canonical.json";
            const filename = filenameFromDisposition(
                response.headers.get("Content-Disposition") || "",
                fallback,
            );
            const objectUrl = URL.createObjectURL(blob);
            const download = document.createElement("a");
            download.href = objectUrl;
            download.download = filename;
            download.hidden = true;
            document.body.append(download);
            download.click();
            download.remove();
            window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);

            const digest = response.headers.get("X-Content-SHA256") || "";
            if (progress instanceof HTMLElement) {
                progress.textContent = digest
                    ? `Файл подготовлен. SHA-256: ${digest}`
                    : "Файл подготовлен и передан браузеру.";
            }
        } catch (_error) {
            if (progress instanceof HTMLElement) {
                progress.textContent = "Не удалось подготовить JSON. Повторите попытку.";
            }
        } finally {
            trigger.dataset.snapshotLoading = "false";
            trigger.removeAttribute("aria-busy");
            trigger.removeAttribute("aria-disabled");
            trigger.textContent = originalLabel;
            container?.removeAttribute("aria-busy");
        }
    });
})();
