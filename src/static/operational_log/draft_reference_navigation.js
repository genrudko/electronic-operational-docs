(() => {
    "use strict";

    const RUNTIME_REVISION = "01134";
    const workspace = document.querySelector("[data-draft-workspace]");
    if (!workspace) {
        return;
    }

    const referencePicker = document.querySelector("[data-reference-picker]");
    const entryKindMenu = document.querySelector("[data-entry-kind-menu]");
    const normativeMenu = document.querySelector("[data-normative-menu]");
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

    function rebuildCatalogIndex(nextCatalog = catalog) {
        catalog = nextCatalog && typeof nextCatalog === "object"
            ? nextCatalog
            : {};
        catalogByReference.clear();
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
    }

    rebuildCatalogIndex();

    let activeToken = null;
    let lastEditorContext = null;
    let viewportSnapshot = null;
    let overlayActive = false;
    let restoreGeneration = 0;
    let tokenPointerGesture = null;
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
    const previewSummary = document.createElement("p");
    previewSummary.className = "draft-reference-preview-summary";
    const previewFacts = document.createElement("dl");
    previewFacts.className = "draft-reference-preview-facts";
    const previewStatus = document.createElement("span");
    previewStatus.className = "draft-reference-preview-status";
    const previewTechnical = document.createElement("details");
    previewTechnical.className = "draft-reference-preview-technical";
    const previewTechnicalSummary = document.createElement("summary");
    previewTechnicalSummary.textContent = "Технические сведения";
    const previewIdentity = document.createElement("code");
    previewIdentity.className = "draft-reference-preview-identity";
    previewTechnical.append(previewTechnicalSummary, previewIdentity);
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
        previewSummary,
        previewFacts,
        previewStatus,
        previewTechnical,
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
            || (normativeMenu && !normativeMenu.hidden)
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

    function normalizedPreview(item) {
        const source = item?.preview && typeof item.preview === "object"
            ? item.preview
            : {};
        return {
            summary: String(source.summary || item?.meta || "").trim(),
            status: String(source.status || "").trim(),
            facts: Array.isArray(source.facts)
                ? source.facts.filter((fact) => (
                    fact
                    && typeof fact === "object"
                    && String(fact.label || "").trim()
                )).slice(0, 8)
                : [],
        };
    }

    function renderPreviewFacts(facts) {
        previewFacts.replaceChildren();
        facts.forEach((fact) => {
            const term = document.createElement("dt");
            term.textContent = String(fact.label || "");
            const value = document.createElement("dd");
            value.textContent = String(fact.value || "—");
            previewFacts.append(term, value);
        });
        previewFacts.hidden = previewFacts.childElementCount === 0;
    }

    function openReferencePreview(token) {
        const identity = tokenReference(token);
        const kind = tokenKind(token, identity);
        const item = catalogByReference.get(identity) || {};
        const label = item.label || tokenLabel(token);
        const meta = item.meta || "Связанный объект оперативной записи";
        const details = normalizedPreview(item);
        const target = referenceTarget(kind, identity);

        activeToken = token;
        captureViewport(token);
        previewKind.textContent = KIND_LABELS[kind] || "Связанный объект";
        previewLabel.textContent = label;
        previewMeta.textContent = meta;
        previewMeta.hidden = !meta;
        previewSummary.textContent = details.summary;
        previewSummary.hidden = !details.summary || details.summary === meta;
        renderPreviewFacts(details.facts);
        previewStatus.textContent = details.status;
        previewStatus.hidden = !details.status;
        previewIdentity.textContent = identity;
        previewTechnical.hidden = !identity;
        previewTechnical.open = false;

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
                + "[data-normative-menu], "
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

    workspace.addEventListener("eod:editor-deactivate", () => {
        suppressNextRestore = true;
        restoreGeneration += 1;
        activeToken = null;
        lastEditorContext = null;
        viewportSnapshot = null;
        notifyOverlayState(false);
    });

    document.addEventListener("focusin", (event) => {
        if (event.target.closest?.("[data-draft-form] [data-rich-editor]")) {
            rememberEditorContext(event.target);
        }
    }, true);

    document.addEventListener("pointerdown", (event) => {
        const token = event.target.closest?.(".draft-reference-token");
        tokenPointerGesture = token
            ? {
                token,
                pointerId: event.pointerId,
                x: event.clientX,
                y: event.clientY,
            }
            : null;
        const interactiveOverlay = event.target.closest?.(
            "[data-entry-kind-trigger], "
            + "[data-reference-trigger], "
            + "[data-entry-kind-menu], "
            + "[data-normative-menu], "
            + "[data-reference-picker], "
            + "[data-reference-preview]",
        );
        if (interactiveOverlay) {
            captureViewport(document.activeElement);
        }
    }, true);

    document.addEventListener("pointermove", (event) => {
        if (
            !tokenPointerGesture
            || tokenPointerGesture.pointerId !== event.pointerId
        ) {
            return;
        }
        const distance = Math.hypot(
            event.clientX - tokenPointerGesture.x,
            event.clientY - tokenPointerGesture.y,
        );
        if (distance > 4) {
            tokenPointerGesture.dragged = true;
        }
    }, true);

    document.addEventListener("click", (event) => {
        const token = event.target.closest?.(".draft-reference-token");
        if (!token) {
            tokenPointerGesture = null;
            if (
                !preview.hidden
                && !preview.contains(event.target)
                && !event.target.closest?.("[data-reference-picker]")
            ) {
                hidePreview();
            }
            return;
        }
        const selection = window.getSelection();
        const selectingText = Boolean(
            event.shiftKey
            || tokenPointerGesture?.dragged
            || (selection && !selection.isCollapsed),
        );
        tokenPointerGesture = null;
        if (selectingText) {
            hidePreview({restore: false});
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

    workspace.addEventListener("eod:reference-catalog-updated", (event) => {
        rebuildCatalogIndex(event.detail?.catalog);
        if (activeToken && !preview.hidden) {
            openReferencePreview(activeToken);
        }
    });

    const overlayObserver = new MutationObserver(synchronizeOverlayState);
    [referencePicker, entryKindMenu, normativeMenu, preview].forEach((node) => {
        if (node) {
            overlayObserver.observe(node, {
                attributes: true,
                attributeFilter: ["hidden"],
            });
        }
    });
})();
