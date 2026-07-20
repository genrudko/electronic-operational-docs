(() => {
    "use strict";

    const RUNTIME_REVISION = "0113-r4";
    const workspace = document.querySelector("[data-draft-workspace]");
    if (!workspace) {
        return;
    }

    const referencePicker = document.querySelector("[data-reference-picker]");
    const entryKindMenu = document.querySelector("[data-entry-kind-menu]");
    const catalogNode = document.getElementById(
        "draft-semantic-reference-catalog",
    );

    const KIND_LABELS = Object.freeze({
        equipment: "Оборудование",
        document: "Документ",
        person: "Сотрудник",
        related_entry: "Запись журнала",
        event_time: "Время события",
    });

    let catalog = {};
    try {
        catalog = catalogNode
            ? JSON.parse(catalogNode.textContent || "{}")
            : {};
    } catch (_error) {
        catalog = {};
    }

    const catalogByReference = new Map();
    Object.values(catalog).forEach((rows) => {
        if (!Array.isArray(rows)) {
            return;
        }
        rows.forEach((row) => {
            if (row && typeof row.reference === "string") {
                catalogByReference.set(row.reference, row);
            }
        });
    });

    let activeToken = null;
    let lastEditorContext = null;
    let viewportSnapshot = null;
    let overlayActive = false;
    let restoreGeneration = 0;
    let suppressNextRestore = false;

    function createButton(label, className = "") {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        if (className) {
            button.className = className;
        }
        return button;
    }

    const preview = document.createElement("aside");
    preview.className = "draft-reference-preview screen-only";
    preview.dataset.referencePreview = "";
    preview.setAttribute("role", "dialog");
    preview.setAttribute("aria-label", "Связанный объект");
    preview.hidden = true;

    const previewHeader = document.createElement("header");
    const previewHeading = document.createElement("div");
    const previewKind = document.createElement("span");
    previewKind.className = "draft-reference-preview-kind";
    const previewLabel = document.createElement("strong");
    previewHeading.append(previewKind, previewLabel);
    const closeButton = createButton("×", "draft-reference-preview-close");
    closeButton.setAttribute("aria-label", "Закрыть карточку");
    previewHeader.append(previewHeading, closeButton);

    const previewMeta = document.createElement("p");
    previewMeta.className = "draft-reference-preview-meta";
    const previewIdentity = document.createElement("code");
    previewIdentity.className = "draft-reference-preview-identity";
    const previewActions = document.createElement("footer");
    previewActions.className = "draft-reference-preview-actions";

    const openButton = createButton("Открыть карточку", "button compact-button");
    const editButton = createButton(
        "Изменить связь",
        "button secondary compact-button",
    );
    previewActions.append(openButton, editButton);
    preview.append(
        previewHeader,
        previewMeta,
        previewIdentity,
        previewActions,
    );
    preview.dataset.runtimeRevision = RUNTIME_REVISION;
    document.body.append(preview);
    workspace.dataset.referenceNavigationRevision = RUNTIME_REVISION;

    function tokenReference(token) {
        return (
            token.dataset.referenceValue
            || token.dataset.referenceReference
            || token.dataset.reference
            || token.getAttribute("data-reference-value")
            || token.getAttribute("data-reference-reference")
            || token.getAttribute("data-reference")
            || ""
        ).trim();
    }

    function tokenKind(token, identity) {
        return (
            token.dataset.referenceKind
            || token.getAttribute("data-reference-kind")
            || identity.split(":", 1)[0]
            || ""
        ).trim();
    }

    function tokenLabel(token) {
        return (
            token.dataset.referenceLabel
            || token.getAttribute("data-reference-label")
            || token.textContent.replace("↗", "").trim()
        );
    }

    function currentEditorContext(source = document.activeElement) {
        const form = source?.closest?.("[data-draft-form]") || null;
        if (!form) {
            return lastEditorContext;
        }
        const editor = form.querySelector("[data-rich-editor]");
        return { form, editor };
    }

    function rememberEditorContext(source = document.activeElement) {
        const context = currentEditorContext(source);
        if (context?.form) {
            lastEditorContext = context;
        }
        return lastEditorContext;
    }

    function notifyOverlayState(active) {
        if (overlayActive === active) {
            return;
        }
        overlayActive = active;
        workspace.dispatchEvent(
            new CustomEvent("eod:editor-overlay-state", {
                detail: { active },
            }),
        );
    }

    function captureViewport(source = document.activeElement) {
        rememberEditorContext(source);
        if (!viewportSnapshot) {
            viewportSnapshot = {
                x: window.scrollX,
                y: window.scrollY,
            };
        }
        restoreGeneration += 1;
        notifyOverlayState(true);
    }

    function nativeOverlayVisible() {
        return Boolean(
            (referencePicker && !referencePicker.hidden)
            || (entryKindMenu && !entryKindMenu.hidden)
            || !preview.hidden,
        );
    }

    function restoreEditorAndViewport() {
        const generation = ++restoreGeneration;
        if (suppressNextRestore) {
            suppressNextRestore = false;
            viewportSnapshot = null;
            notifyOverlayState(false);
            return;
        }
        const snapshot = viewportSnapshot;
        const context = lastEditorContext;
        window.requestAnimationFrame(() => {
            if (generation !== restoreGeneration || nativeOverlayVisible()) {
                return;
            }
            if (context?.editor?.isConnected) {
                try {
                    context.editor.focus({ preventScroll: true });
                } catch (_error) {
                    context.editor.focus();
                }
            }
            if (snapshot) {
                window.scrollTo(snapshot.x, snapshot.y);
            }
            window.requestAnimationFrame(() => {
                if (generation !== restoreGeneration || nativeOverlayVisible()) {
                    return;
                }
                if (snapshot) {
                    window.scrollTo(snapshot.x, snapshot.y);
                }
                viewportSnapshot = null;
                notifyOverlayState(false);
            });
        });
    }

    function synchronizeOverlayState() {
        if (nativeOverlayVisible()) {
            captureViewport(activeToken || document.activeElement);
            return;
        }
        restoreEditorAndViewport();
    }

    function placePreview(token) {
        const rect = token.getBoundingClientRect();
        const margin = 10;
        const width = Math.min(390, window.innerWidth - (margin * 2));
        preview.style.width = `${Math.max(280, width)}px`;
        preview.style.left = `${Math.min(
            Math.max(margin, rect.left),
            window.innerWidth - width - margin,
        )}px`;
        preview.hidden = false;
        const previewRect = preview.getBoundingClientRect();
        let top = rect.bottom + 8;
        if (top + previewRect.height > window.innerHeight - margin) {
            top = Math.max(margin, rect.top - previewRect.height - 8);
        }
        preview.style.top = `${top}px`;
    }

    function referenceTarget(kind, identity) {
        const separator = identity.indexOf(":");
        const rawId = separator >= 0 ? identity.slice(separator + 1) : "";
        if (!rawId) {
            return null;
        }
        if (kind === "equipment") {
            return { mode: "url", value: `/equipment/items/${rawId}/` };
        }
        if (kind === "document") {
            return { mode: "url", value: `/documents/${rawId}/` };
        }
        if (kind === "person") {
            return { mode: "url", value: "/organization/" };
        }
        if (kind === "related_entry") {
            return { mode: "draft", value: rawId };
        }
        return null;
    }

    function hidePreview({ restore = true } = {}) {
        if (preview.hidden) {
            return;
        }
        preview.hidden = true;
        activeToken = null;
        if (restore) {
            synchronizeOverlayState();
        }
    }

    function openReferencePreview(token) {
        const identity = tokenReference(token);
        const kind = tokenKind(token, identity);
        const item = catalogByReference.get(identity) || {};
        const label = item.label || tokenLabel(token);
        const meta = item.meta || "Связанный объект оперативной записи";
        const target = referenceTarget(kind, identity);

        activeToken = token;
        captureViewport(token);
        previewKind.textContent = KIND_LABELS[kind] || "Связанный объект";
        previewLabel.textContent = label;
        previewMeta.textContent = meta;
        previewIdentity.textContent = identity;
        previewIdentity.hidden = !identity;

        if (target?.mode === "draft") {
            openButton.textContent = "Показать запись";
        } else if (kind === "person") {
            openButton.textContent = "Открыть справочник";
        } else {
            openButton.textContent = "Открыть карточку";
        }
        openButton.hidden = !target;
        openButton.dataset.referenceTargetMode = target?.mode || "";
        openButton.dataset.referenceTargetValue = target?.value || "";

        placePreview(token);
        notifyOverlayState(true);
        closeButton.focus({ preventScroll: true });
    }

    function stabilizeViewportDuringOverlay(event) {
        if (!overlayActive || !viewportSnapshot) {
            return;
        }
        const target = event.target;
        if (
            target instanceof Element
            && target.closest(
                "[data-reference-picker], "
                + "[data-entry-kind-menu], "
                + "[data-reference-preview]",
            )
        ) {
            return;
        }
        const snapshot = viewportSnapshot;
        if (
            Math.abs(window.scrollX - snapshot.x) > 1
            || Math.abs(window.scrollY - snapshot.y) > 1
        ) {
            window.requestAnimationFrame(() => {
                if (overlayActive && viewportSnapshot === snapshot) {
                    window.scrollTo(snapshot.x, snapshot.y);
                }
            });
        }
    }

    closeButton.addEventListener("click", () => hidePreview());

    openButton.addEventListener("click", () => {
        const mode = openButton.dataset.referenceTargetMode;
        const value = openButton.dataset.referenceTargetValue;
        if (!mode || !value) {
            return;
        }
        if (mode === "draft") {
            suppressNextRestore = true;
            hidePreview({ restore: false });
            workspace.dispatchEvent(
                new CustomEvent("eod:reveal-draft-reference", {
                    detail: { draftId: value },
                }),
            );
            viewportSnapshot = null;
            notifyOverlayState(false);
            return;
        }
        window.location.assign(value);
    });

    editButton.addEventListener("click", () => {
        if (!activeToken) {
            return;
        }
        const token = activeToken;
        hidePreview({ restore: false });
        captureViewport(token);
        token.dispatchEvent(
            new MouseEvent("dblclick", {
                bubbles: true,
                cancelable: true,
                view: window,
            }),
        );
        window.requestAnimationFrame(synchronizeOverlayState);
    });

    document.addEventListener("focusin", (event) => {
        if (event.target.closest?.("[data-draft-form] [data-rich-editor]")) {
            rememberEditorContext(event.target);
        }
    }, true);

    document.addEventListener("pointerdown", (event) => {
        const interactiveOverlay = event.target.closest?.(
            "[data-entry-kind-trigger], "
            + "[data-reference-trigger], "
            + "[data-entry-kind-menu], "
            + "[data-reference-picker], "
            + "[data-reference-preview]",
        );
        if (interactiveOverlay) {
            captureViewport(document.activeElement);
        }
    }, true);

    document.addEventListener("click", (event) => {
        const token = event.target.closest?.(".draft-reference-token");
        if (!token) {
            if (
                !preview.hidden
                && !preview.contains(event.target)
                && !event.target.closest?.("[data-reference-picker]")
            ) {
                hidePreview();
            }
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        openReferencePreview(token);
    }, true);

    document.addEventListener("dblclick", (event) => {
        const token = event.target.closest?.(".draft-reference-token");
        if (!token) {
            return;
        }
        hidePreview({ restore: false });
        captureViewport(token);
        window.requestAnimationFrame(synchronizeOverlayState);
    }, true);

    document.addEventListener("keydown", (event) => {
        const token = event.target.closest?.(".draft-reference-token");
        if (token && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            event.stopImmediatePropagation();
            openReferencePreview(token);
            return;
        }
        if (event.key === "Escape" && !preview.hidden) {
            event.preventDefault();
            hidePreview();
        }
    }, true);

    window.addEventListener("scroll", stabilizeViewportDuringOverlay, true);
    window.addEventListener("resize", () => {
        if (activeToken && !preview.hidden) {
            placePreview(activeToken);
        }
    });

    const overlayObserver = new MutationObserver(synchronizeOverlayState);
    [referencePicker, entryKindMenu, preview].forEach((node) => {
        if (node) {
            overlayObserver.observe(node, {
                attributes: true,
                attributeFilter: ["hidden"],
            });
        }
    });
})();
