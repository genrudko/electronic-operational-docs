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

    const formatBytes = (value) => {
        if (!Number.isFinite(value) || value < 0) {
            return "";
        }
        if (value < 1024) {
            return `${value} Б`;
        }
        const units = ["КБ", "МБ", "ГБ"];
        let amount = value;
        let unit = "Б";
        for (const candidate of units) {
            amount /= 1024;
            unit = candidate;
            if (amount < 1024) {
                break;
            }
        }
        return `${amount.toLocaleString("ru-RU", {
            maximumFractionDigits: amount >= 10 ? 1 : 2,
        })} ${unit}`;
    };

    let toastTimer = 0;

    const ensureDownloadToast = () => {
        const existing = document.querySelector("[data-power-system-download-toast]");
        if (existing instanceof HTMLElement) {
            return existing;
        }
        const toast = document.createElement("div");
        toast.className = "ps-download-toast";
        toast.hidden = true;
        toast.dataset.powerSystemDownloadToast = "";
        toast.setAttribute("role", "status");
        toast.setAttribute("aria-live", "assertive");
        toast.setAttribute("aria-atomic", "true");
        document.body.append(toast);
        return toast;
    };

    const showDownloadToast = (message, state) => {
        const toast = ensureDownloadToast();
        window.clearTimeout(toastTimer);
        toast.dataset.state = state;
        toast.textContent = message;
        toast.hidden = false;
        window.requestAnimationFrame(() => {
            toast.classList.add("is-visible");
        });
        toastTimer = window.setTimeout(() => {
            toast.classList.remove("is-visible");
            window.setTimeout(() => {
                toast.hidden = true;
            }, 180);
        }, 10000);
    };

    const updateProgress = (progress, message, state, focus = false) => {
        if (!(progress instanceof HTMLElement)) {
            return;
        }
        progress.hidden = false;
        progress.dataset.state = state;
        progress.textContent = message;
        if (focus) {
            progress.focus({preventScroll: true});
        }
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
        const originalLabel = trigger.textContent?.trim() || "Скачать канонический JSON";
        let completed = false;

        trigger.dataset.snapshotLoading = "true";
        trigger.setAttribute("aria-busy", "true");
        trigger.setAttribute("aria-disabled", "true");
        trigger.textContent = "Подготавливается канонический JSON…";
        container?.setAttribute("aria-busy", "true");
        updateProgress(progress, "Сервер формирует точный канонический файл…", "loading");

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
            const size = formatBytes(blob.size);
            const sizePart = size ? ` (${size})` : "";
            const digestPart = digest ? ` SHA-256: ${digest}` : "";
            updateProgress(
                progress,
                `Файл передан в загрузки браузера: ${filename}${sizePart}.${digestPart}`,
                "success",
                true,
            );
            showDownloadToast(
                `Канонический JSON передан в загрузки браузера: ${filename}`,
                "success",
            );
            trigger.textContent = "Скачать ещё раз";
            trigger.dataset.snapshotDownloaded = "true";
            completed = true;
        } catch (_error) {
            updateProgress(
                progress,
                "Не удалось передать JSON в загрузки браузера. Повторите попытку.",
                "error",
                true,
            );
            showDownloadToast("Не удалось скачать канонический JSON.", "error");
        } finally {
            trigger.dataset.snapshotLoading = "false";
            trigger.removeAttribute("aria-busy");
            trigger.removeAttribute("aria-disabled");
            if (!completed) {
                trigger.textContent = originalLabel;
            }
            container?.removeAttribute("aria-busy");
        }
    });
})();
