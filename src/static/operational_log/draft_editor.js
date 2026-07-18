(() => {
    "use strict";

    const SCHEMA_VERSION = "operational-draft-editor.v2";
    const LEGACY_SCHEMA_VERSIONS = new Set([
        "operational-draft-editor.v1",
    ]);
    const SEMANTIC_KINDS = Object.freeze({
        command: {label: "Команда", prefix: "Команда: "},
        permission: {label: "Разрешение", prefix: "Разрешение: "},
        message: {label: "Сообщение", prefix: "Сообщение: "},
        warning: {label: "Предупреждение", prefix: "Предупреждение: "},
        equipment: {label: "Оборудование", prefix: ""},
        document: {label: "Документ", prefix: ""},
        person: {label: "Сотрудник или должность", prefix: ""},
        event_time: {label: "Время события", prefix: ""},
        related_entry: {label: "Связанная запись", prefix: ""},
        carryover: {label: "На следующую смену", prefix: "На следующую смену: "},
    });
    const controllers = new WeakMap();
    const ribbon = document.querySelector("[data-editor-ribbon]");
    const ribbonStatus = document.querySelector(
        "[data-editor-ribbon-status]",
    );
    const floatingToolbar = document.querySelector(
        "[data-editor-floating-toolbar]",
    );
    const semanticPalette = document.querySelector(
        "[data-semantic-palette]",
    );
    const semanticDialog = document.querySelector(
        "[data-semantic-dialog]",
    );
    const semanticDialogForm = semanticDialog?.querySelector(
        "[data-semantic-dialog-form]",
    );
    const semanticKindInput = semanticDialog?.querySelector(
        "[data-semantic-kind]",
    );
    const semanticKindLabel = semanticDialog?.querySelector(
        "[data-semantic-kind-label]",
    );
    const semanticLabelInput = semanticDialog?.querySelector(
        "[data-semantic-label]",
    );
    const semanticReferenceInput = semanticDialog?.querySelector(
        "[data-semantic-reference]",
    );
    const semanticDialogTitle = semanticDialog?.querySelector(
        "[data-semantic-dialog-title]",
    );
    let activeController = null;
    let selectionFrame = null;
    let semanticTrigger = null;
    let semanticEditingToken = null;

    function emptyDocument() {
        return {
            schema_version: SCHEMA_VERSION,
            blocks: [{type: "paragraph", segments: []}],
        };
    }

    function plainTextDocument(value) {
        const text = String(value || "")
            .replace(/\r\n/g, "\n")
            .replace(/\r/g, "\n");
        return {
            schema_version: SCHEMA_VERSION,
            blocks: text.split("\n").map((line) => ({
                type: "paragraph",
                segments: line ? [{text: line, marks: []}] : [],
            })),
        };
    }

    function normalizeMarks(value) {
        const source = Array.isArray(value) ? value : [];
        return ["bold", "underline"].filter(
            (mark) => source.includes(mark),
        );
    }

    function normalizeSingleLine(value, maxLength) {
        return String(value || "")
            .replace(/\r\n/g, "\n")
            .replace(/\r/g, "\n")
            .split(/\s+/)
            .filter(Boolean)
            .join(" ")
            .trim()
            .slice(0, maxLength);
    }

    function normalizeSemantic(value) {
        if (!value || typeof value !== "object") {
            return null;
        }
        const kind = String(value.kind || "");
        if (!SEMANTIC_KINDS[kind]) {
            return null;
        }
        const label = normalizeSingleLine(value.label, 500);
        if (!label) {
            return null;
        }
        const reference = normalizeSingleLine(value.reference, 200);
        return {
            kind,
            label,
            ...(reference ? {reference} : {}),
        };
    }

    function semanticProjection(semantic) {
        const definition = SEMANTIC_KINDS[semantic.kind];
        return `${definition?.prefix || ""}${semantic.label}`;
    }

    function normalizeSegments(value) {
        const source = Array.isArray(value) ? value : [];
        const result = [];
        source.forEach((segment) => {
            if (!segment || typeof segment !== "object") {
                return;
            }
            const marks = normalizeMarks(segment.marks);
            const semantic = normalizeSemantic(segment.semantic);
            if (semantic) {
                result.push({
                    text: semanticProjection(semantic),
                    marks,
                    semantic,
                });
                return;
            }
            if (typeof segment.text !== "string") {
                return;
            }
            const text = segment.text
                .replace(/\r\n/g, "\n")
                .replace(/\r/g, "\n");
            if (!text) {
                return;
            }
            const previous = result.at(-1);
            if (
                previous
                && !previous.semantic
                && JSON.stringify(previous.marks) === JSON.stringify(marks)
            ) {
                previous.text += text;
            } else {
                result.push({text, marks});
            }
        });
        return result;
    }

    function normalizeDocument(value, fallbackText = "") {
        if (
            !value
            || typeof value !== "object"
            || (
                value.schema_version !== SCHEMA_VERSION
                && !LEGACY_SCHEMA_VERSIONS.has(value.schema_version)
            )
            || !Array.isArray(value.blocks)
        ) {
            return plainTextDocument(fallbackText);
        }
        const blocks = [];
        value.blocks.forEach((block) => {
            if (!block || typeof block !== "object") {
                return;
            }
            if (block.type === "paragraph") {
                blocks.push({
                    type: "paragraph",
                    segments: normalizeSegments(block.segments),
                });
                return;
            }
            if (
                ["bullet_list", "ordered_list"].includes(block.type)
                && Array.isArray(block.items)
            ) {
                blocks.push({
                    type: block.type,
                    items: block.items.map((item) => ({
                        segments: normalizeSegments(item?.segments),
                    })),
                });
            }
        });
        return {
            schema_version: SCHEMA_VERSION,
            blocks: blocks.length ? blocks : emptyDocument().blocks,
        };
    }

    function documentToText(documentPayload) {
        const lines = [];
        documentPayload.blocks.forEach((block) => {
            if (block.type === "paragraph") {
                lines.push(
                    block.segments.map((segment) => segment.text).join(""),
                );
                return;
            }
            block.items.forEach((item, index) => {
                const text = item.segments
                    .map((segment) => segment.text)
                    .join("");
                const prefix = block.type === "bullet_list"
                    ? "• "
                    : `${index + 1}. `;
                lines.push(prefix + text);
            });
        });
        return lines.join("\n");
    }

    function semanticToken(semantic) {
        const definition = SEMANTIC_KINDS[semantic.kind];
        const token = document.createElement("span");
        token.className = "draft-semantic-token";
        token.dataset.semanticKind = semantic.kind;
        token.dataset.semanticLabel = semantic.label;
        if (semantic.reference) {
            token.dataset.semanticReference = semantic.reference;
        }
        token.contentEditable = "false";
        token.setAttribute("role", "button");
        token.setAttribute("tabindex", "0");
        token.setAttribute(
            "aria-label",
            `${definition.label}: ${semantic.label}`,
        );
        token.title = semantic.reference
            ? `${definition.label}: ${semantic.label} · ${semantic.reference}`
            : `${definition.label}: ${semantic.label}`;

        const prefix = document.createElement("span");
        prefix.className = "draft-semantic-token-prefix";
        prefix.textContent = definition.prefix;
        token.append(prefix);

        const badge = document.createElement("span");
        badge.className = "draft-semantic-token-badge";
        badge.setAttribute("aria-hidden", "true");
        badge.textContent = definition.label;
        token.append(badge);

        const label = document.createElement("span");
        label.className = "draft-semantic-token-label";
        label.textContent = semantic.label;
        token.append(label);

        if (semantic.reference) {
            const reference = document.createElement("span");
            reference.className = "draft-semantic-token-reference";
            reference.textContent = semantic.reference;
            token.append(reference);
        }
        return token;
    }

    function appendSegment(parent, segment) {
        let node = segment.semantic
            ? semanticToken(segment.semantic)
            : document.createTextNode(segment.text);
        if (segment.marks.includes("underline")) {
            const underline = document.createElement("u");
            underline.append(node);
            node = underline;
        }
        if (segment.marks.includes("bold")) {
            const strong = document.createElement("strong");
            strong.append(node);
            node = strong;
        }
        parent.append(node);
    }

    function renderDocument(editor, documentPayload) {
        editor.replaceChildren();
        documentPayload.blocks.forEach((block) => {
            if (block.type === "paragraph") {
                const paragraph = document.createElement("p");
                block.segments.forEach((segment) => {
                    appendSegment(paragraph, segment);
                });
                if (!paragraph.hasChildNodes()) {
                    paragraph.append(document.createElement("br"));
                }
                editor.append(paragraph);
                return;
            }
            const list = document.createElement(
                block.type === "bullet_list" ? "ul" : "ol",
            );
            block.items.forEach((item) => {
                const listItem = document.createElement("li");
                item.segments.forEach((segment) => {
                    appendSegment(listItem, segment);
                });
                if (!listItem.hasChildNodes()) {
                    listItem.append(document.createElement("br"));
                }
                list.append(listItem);
            });
            if (!list.hasChildNodes()) {
                const listItem = document.createElement("li");
                listItem.append(document.createElement("br"));
                list.append(listItem);
            }
            editor.append(list);
        });
        updateEmptyState(editor);
    }

    function pushTextSegment(result, text, marks) {
        if (!text) {
            return;
        }
        const normalizedMarks = normalizeMarks(marks);
        const previous = result.at(-1);
        if (
            previous
            && !previous.semantic
            && JSON.stringify(previous.marks)
                === JSON.stringify(normalizedMarks)
        ) {
            previous.text += text;
        } else {
            result.push({text, marks: normalizedMarks});
        }
    }

    function pushSemanticSegment(result, semantic, marks) {
        const normalized = normalizeSemantic(semantic);
        if (!normalized) {
            return;
        }
        result.push({
            text: semanticProjection(normalized),
            marks: normalizeMarks(marks),
            semantic: normalized,
        });
    }

    function segmentsFromNode(node, inheritedMarks = []) {
        const result = [];
        if (node.nodeType === Node.TEXT_NODE) {
            pushTextSegment(result, node.nodeValue || "", inheritedMarks);
            return result;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return result;
        }
        const tag = node.tagName.toLowerCase();
        if (node.matches?.("[data-semantic-kind]")) {
            pushSemanticSegment(
                result,
                {
                    kind: node.dataset.semanticKind,
                    label: node.dataset.semanticLabel,
                    reference: node.dataset.semanticReference || "",
                },
                inheritedMarks,
            );
            return result;
        }
        if (tag === "br") {
            pushTextSegment(result, "\n", inheritedMarks);
            return result;
        }
        const marks = [...inheritedMarks];
        if (["strong", "b"].includes(tag) && !marks.includes("bold")) {
            marks.push("bold");
        }
        if (tag === "u" && !marks.includes("underline")) {
            marks.push("underline");
        }
        node.childNodes.forEach((child) => {
            segmentsFromNode(child, marks).forEach((segment) => {
                pushTextSegment(result, segment.text, segment.marks);
            });
        });
        return result;
    }

    function editableBlockSegments(node) {
        const segments = normalizeSegments(segmentsFromNode(node));
        if (
            segments.length === 1
            && segments[0].text === "\n"
            && segments[0].marks.length === 0
        ) {
            return [];
        }
        return segments;
    }

    function editorToDocument(editor) {
        const blocks = [];
        const children = Array.from(editor.childNodes);
        children.forEach((node) => {
            if (
                node.nodeType === Node.ELEMENT_NODE
                && ["ul", "ol"].includes(node.tagName.toLowerCase())
            ) {
                const items = Array.from(node.children)
                    .filter((item) => item.tagName.toLowerCase() === "li")
                    .map((item) => ({
                        segments: editableBlockSegments(item),
                    }));
                blocks.push({
                    type: node.tagName.toLowerCase() === "ul"
                        ? "bullet_list"
                        : "ordered_list",
                    items,
                });
                return;
            }
            blocks.push({
                type: "paragraph",
                segments: editableBlockSegments(node),
            });
        });
        return normalizeDocument({
            schema_version: SCHEMA_VERSION,
            blocks: blocks.length ? blocks : emptyDocument().blocks,
        });
    }

    function updateEmptyState(editor) {
        editor.dataset.empty = editor.textContent.trim() ? "false" : "true";
    }

    function payloadField(form) {
        return form.querySelector("[data-editor-payload]");
    }

    function fallbackField(form) {
        return form.querySelector("[data-editor-fallback]");
    }

    function schemaField(form) {
        return form.querySelector("[data-editor-schema-version]");
    }

    function parseStoredDocument(form) {
        const payload = payloadField(form)?.value || "";
        const fallback = fallbackField(form)?.value || "";
        if (!payload) {
            return plainTextDocument(fallback);
        }
        try {
            return normalizeDocument(JSON.parse(payload), fallback);
        } catch (error) {
            return plainTextDocument(fallback);
        }
    }

    function writeFormState(form, documentPayload) {
        const normalized = normalizeDocument(
            documentPayload,
            fallbackField(form)?.value || "",
        );
        const payload = payloadField(form);
        const fallback = fallbackField(form);
        const schema = schemaField(form);
        if (payload) {
            payload.value = JSON.stringify(normalized);
        }
        if (fallback) {
            fallback.value = documentToText(normalized);
        }
        if (schema) {
            schema.value = SCHEMA_VERSION;
        }
        return normalized;
    }

    function dispatchFallbackEvent(controller, type) {
        const fallback = fallbackField(controller.form);
        if (!fallback) {
            return;
        }
        fallback.dispatchEvent(new Event(type, {bubbles: true}));
    }

    function syncController(controller, emitInput = false) {
        const documentPayload = editorToDocument(controller.editor);
        writeFormState(controller.form, documentPayload);
        updateEmptyState(controller.editor);
        if (emitInput) {
            dispatchFallbackEvent(controller, "input");
        }
        updateToolbarState(controller);
        return documentPayload;
    }

    function queryCommandState(command) {
        try {
            return document.queryCommandState(command);
        } catch (error) {
            return false;
        }
    }

    function commandButtons() {
        return Array.from(
            document.querySelectorAll("[data-editor-command]"),
        );
    }

    function isRangeInsideEditor(range, editor) {
        if (!range || !editor?.isConnected) {
            return false;
        }
        return (
            editor.contains(range.startContainer)
            && editor.contains(range.endContainer)
        );
    }

    function selectionController() {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            return null;
        }
        const range = selection.getRangeAt(0);
        const node = range.commonAncestorContainer;
        const element = (
            node.nodeType === Node.ELEMENT_NODE
                ? node
                : node.parentElement
        );
        const editor = element?.closest?.("[data-rich-editor]");
        if (!editor) {
            return null;
        }
        const form = editor.closest("[data-draft-form]");
        const controller = form ? controllers.get(form) : null;
        if (!controller || !isRangeInsideEditor(range, controller.editor)) {
            return null;
        }
        return {controller, range};
    }

    function recordLabel(controller) {
        const time = (
            controller.row.querySelector("[data-quick-time]")?.value
            || "—"
        );
        const sequence = (
            controller.row.querySelector(".draft-sequence-muted")
                ?.textContent.trim()
            || ""
        );
        return `Запись ${time}${sequence ? ` · ${sequence}` : ""}`;
    }

    function setActiveController(controller) {
        if (activeController === controller) {
            return;
        }
        activeController?.row.classList.remove("is-editor-active");
        activeController = controller || null;
        activeController?.row.classList.add("is-editor-active");
        if (ribbonStatus) {
            ribbonStatus.textContent = activeController
                ? recordLabel(activeController)
                : "Щёлкните по тексту записи";
        }
        updateToolbarState(activeController);
    }

    function restoreSelection(controller) {
        const selection = window.getSelection();
        if (!selection) {
            return false;
        }
        if (
            controller.savedRange
            && isRangeInsideEditor(
                controller.savedRange,
                controller.editor,
            )
        ) {
            selection.removeAllRanges();
            selection.addRange(controller.savedRange.cloneRange());
            return true;
        }
        const range = document.createRange();
        range.selectNodeContents(controller.editor);
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
        controller.savedRange = range.cloneRange();
        return true;
    }

    function captureSelection(controller = null) {
        const resolved = selectionController();
        if (!resolved) {
            return null;
        }
        const target = controller || resolved.controller;
        if (resolved.controller !== target) {
            return null;
        }
        target.savedRange = resolved.range.cloneRange();
        setActiveController(target);
        return resolved;
    }

    function hideFloatingToolbar() {
        if (!floatingToolbar) {
            return;
        }
        floatingToolbar.hidden = true;
        floatingToolbar.style.removeProperty("left");
        floatingToolbar.style.removeProperty("top");
    }

    function positionFloatingToolbar(range) {
        if (!floatingToolbar || range.collapsed) {
            hideFloatingToolbar();
            return;
        }
        const rectangles = Array.from(range.getClientRects());
        const targetRect = rectangles[0] || range.getBoundingClientRect();
        if (
            !targetRect
            || (!targetRect.width && !targetRect.height)
        ) {
            hideFloatingToolbar();
            return;
        }

        floatingToolbar.hidden = false;
        window.requestAnimationFrame(() => {
            if (floatingToolbar.hidden) {
                return;
            }
            const toolbarRect = floatingToolbar.getBoundingClientRect();
            const margin = 8;
            let left = (
                targetRect.left
                + (targetRect.width / 2)
                - (toolbarRect.width / 2)
            );
            left = Math.max(
                margin,
                Math.min(
                    left,
                    window.innerWidth - toolbarRect.width - margin,
                ),
            );
            let top = targetRect.top - toolbarRect.height - 10;
            if (top < margin) {
                top = targetRect.bottom + 10;
            }
            top = Math.max(
                margin,
                Math.min(
                    top,
                    window.innerHeight - toolbarRect.height - margin,
                ),
            );
            floatingToolbar.style.left = `${Math.round(left)}px`;
            floatingToolbar.style.top = `${Math.round(top)}px`;
        });
    }

    function refreshSelectionUi() {
        selectionFrame = null;
        const resolved = captureSelection();
        if (!resolved || resolved.range.collapsed) {
            hideFloatingToolbar();
            if (activeController) {
                updateToolbarState(activeController);
            }
            return;
        }
        positionFloatingToolbar(resolved.range);
        updateToolbarState(resolved.controller);
    }

    function scheduleSelectionUi() {
        if (selectionFrame !== null) {
            window.cancelAnimationFrame(selectionFrame);
        }
        selectionFrame = window.requestAnimationFrame(
            refreshSelectionUi,
        );
    }

    function updateToolbarState(controller) {
        commandButtons().forEach((button) => {
            const command = button.dataset.editorCommand;
            button.disabled = !controller;
            let active = false;
            if (controller) {
                if (command === "bold") {
                    active = queryCommandState("bold");
                } else if (command === "underline") {
                    active = queryCommandState("underline");
                } else if (command === "bullet_list") {
                    active = queryCommandState(
                        "insertUnorderedList",
                    );
                } else if (command === "ordered_list") {
                    active = queryCommandState(
                        "insertOrderedList",
                    );
                }
            }
            button.classList.toggle("is-active", active);
            if ([
                "bold",
                "underline",
                "bullet_list",
                "ordered_list",
            ].includes(command)) {
                button.setAttribute(
                    "aria-pressed",
                    String(active),
                );
            }
        });
        document
            .querySelectorAll("[data-editor-semantic-trigger]")
            .forEach((button) => {
                button.disabled = !controller;
            });
        ribbon?.classList.toggle("has-active-editor", Boolean(controller));
    }


    function hideSemanticPalette() {
        if (!semanticPalette) {
            return;
        }
        semanticPalette.hidden = true;
        semanticPalette.style.removeProperty("left");
        semanticPalette.style.removeProperty("top");
        semanticTrigger?.setAttribute("aria-expanded", "false");
        semanticTrigger = null;
    }

    function positionSemanticPalette(trigger) {
        if (!semanticPalette || !trigger) {
            return;
        }
        semanticPalette.hidden = false;
        semanticTrigger = trigger;
        trigger.setAttribute("aria-expanded", "true");
        window.requestAnimationFrame(() => {
            const triggerRect = trigger.getBoundingClientRect();
            const paletteRect = semanticPalette.getBoundingClientRect();
            const margin = 8;
            let left = triggerRect.left;
            left = Math.max(
                margin,
                Math.min(
                    left,
                    window.innerWidth - paletteRect.width - margin,
                ),
            );
            let top = triggerRect.bottom + 8;
            if (top + paletteRect.height > window.innerHeight - margin) {
                top = triggerRect.top - paletteRect.height - 8;
            }
            semanticPalette.style.left = `${Math.round(left)}px`;
            semanticPalette.style.top = `${Math.max(margin, Math.round(top))}px`;
        });
    }

    function closeSemanticDialog() {
        if (!semanticDialog) {
            return;
        }
        semanticDialog.hidden = true;
        semanticEditingToken = null;
        semanticLabelInput?.setCustomValidity("");
        semanticDialogForm?.reset();
    }

    function selectedText(controller) {
        const selection = window.getSelection();
        if (selection && selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            if (isRangeInsideEditor(range, controller.editor)) {
                controller.savedRange = range.cloneRange();
                return normalizeSingleLine(selection.toString(), 500);
            }
        }
        if (
            controller.savedRange
            && isRangeInsideEditor(
                controller.savedRange,
                controller.editor,
            )
        ) {
            return normalizeSingleLine(
                controller.savedRange.toString(),
                500,
            );
        }
        return "";
    }

    function openSemanticDialog(kind, token = null) {
        if (!semanticDialog || !activeController || !SEMANTIC_KINDS[kind]) {
            return;
        }
        hideSemanticPalette();
        hideFloatingToolbar();
        semanticEditingToken = token;
        const semantic = token ? {
            kind: token.dataset.semanticKind,
            label: token.dataset.semanticLabel,
            reference: token.dataset.semanticReference || "",
        } : null;
        const label = semantic?.label || selectedText(activeController);
        const reference = semantic?.reference || "";
        semanticKindInput.value = kind;
        semanticKindLabel.textContent = SEMANTIC_KINDS[kind].label;
        semanticLabelInput.value = label;
        semanticReferenceInput.value = reference;
        semanticDialogTitle.textContent = token
            ? "Изменить семантический элемент"
            : "Вставить семантический элемент";
        semanticDialog.hidden = false;
        window.requestAnimationFrame(() => {
            semanticLabelInput.focus();
            semanticLabelInput.select();
        });
    }

    function nearestEditableBlock(node, editor) {
        const element = node.nodeType === Node.ELEMENT_NODE
            ? node
            : node.parentElement;
        const block = element?.closest?.("p, li");
        return block && editor.contains(block) ? block : null;
    }

    function insertSemantic(controller, semantic) {
        setActiveController(controller);
        restoreSelection(controller);
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            return false;
        }
        const range = selection.getRangeAt(0);
        if (!isRangeInsideEditor(range, controller.editor)) {
            return false;
        }
        const startBlock = nearestEditableBlock(
            range.startContainer,
            controller.editor,
        );
        const endBlock = nearestEditableBlock(
            range.endContainer,
            controller.editor,
        );
        if (!startBlock || startBlock !== endBlock) {
            return false;
        }
        range.deleteContents();
        const token = semanticToken(semantic);
        range.insertNode(token);
        const spacer = document.createTextNode(" ");
        token.after(spacer);
        const nextRange = document.createRange();
        nextRange.setStartAfter(spacer);
        nextRange.collapse(true);
        selection.removeAllRanges();
        selection.addRange(nextRange);
        controller.savedRange = nextRange.cloneRange();
        syncController(controller, true);
        scheduleSelectionUi();
        return true;
    }

    function updateSemanticToken(controller, token, semantic) {
        const replacement = semanticToken(semantic);
        token.replaceWith(replacement);
        controller.savedRange = null;
        syncController(controller, true);
        replacement.focus({preventScroll: true});
        return true;
    }

    function bindSemanticUi(scope) {
        scope.querySelectorAll("[data-editor-semantic-trigger]").forEach((button) => {
            if (button.dataset.semanticBound === "true") {
                return;
            }
            button.dataset.semanticBound = "true";
            button.addEventListener("mousedown", (event) => {
                event.preventDefault();
                if (activeController) {
                    captureSelection(activeController);
                }
            });
            button.addEventListener("click", () => {
                if (!activeController) {
                    return;
                }
                if (
                    semanticTrigger === button
                    && semanticPalette
                    && !semanticPalette.hidden
                ) {
                    hideSemanticPalette();
                    return;
                }
                positionSemanticPalette(button);
            });
        });

        semanticPalette?.querySelectorAll("[data-semantic-option]").forEach((button) => {
            if (button.dataset.semanticOptionBound === "true") {
                return;
            }
            button.dataset.semanticOptionBound = "true";
            button.addEventListener("click", () => {
                openSemanticDialog(button.dataset.semanticOption);
            });
        });
    }

    semanticDialogForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!activeController) {
            closeSemanticDialog();
            return;
        }
        const semantic = normalizeSemantic({
            kind: semanticKindInput.value,
            label: semanticLabelInput.value,
            reference: semanticReferenceInput.value,
        });
        if (!semantic) {
            semanticLabelInput.setCustomValidity(
                "Укажи текст семантического элемента.",
            );
            semanticLabelInput.reportValidity();
            return;
        }
        semanticLabelInput.setCustomValidity("");
        const applied = semanticEditingToken?.isConnected
            ? updateSemanticToken(
                activeController,
                semanticEditingToken,
                semantic,
            )
            : insertSemantic(activeController, semantic);
        if (!applied) {
            semanticLabelInput.setCustomValidity(
                "Выделение должно находиться внутри одного абзаца или пункта списка.",
            );
            semanticLabelInput.reportValidity();
            return;
        }
        closeSemanticDialog();
    });

    semanticDialog?.querySelectorAll("[data-semantic-cancel]").forEach((button) => {
        button.addEventListener("click", closeSemanticDialog);
    });

    function executeEditorCommand(controller, command) {
        const commandMap = {
            bold: "bold",
            underline: "underline",
            bullet_list: "insertUnorderedList",
            ordered_list: "insertOrderedList",
            undo: "undo",
            redo: "redo",
            clear: "removeFormat",
        };
        const nativeCommand = commandMap[command];
        if (!nativeCommand) {
            return;
        }
        setActiveController(controller);
        restoreSelection(controller);
        controller.editor.focus({preventScroll: true});
        if (["bold", "underline"].includes(command)) {
            document.execCommand("styleWithCSS", false, false);
        }
        document.execCommand(nativeCommand, false, null);
        captureSelection(controller);
        syncController(controller, true);
        scheduleSelectionUi();
    }

    function insertPlainText(editor, text) {
        editor.focus();
        document.execCommand("insertText", false, text);
    }

    function initializeRow(row) {
        const form = row.querySelector("[data-draft-form]");
        if (!form) {
            return null;
        }
        if (controllers.has(form)) {
            return controllers.get(form);
        }
        const host = form.querySelector("[data-rich-editor-host]");
        const fallback = fallbackField(form);
        if (!host || !fallback) {
            return null;
        }

        const editor = document.createElement("div");
        editor.className = "draft-rich-editor";
        editor.contentEditable = "true";
        editor.spellcheck = true;
        editor.dataset.richEditor = "true";
        editor.dataset.empty = "true";
        editor.setAttribute("role", "textbox");
        editor.setAttribute("aria-multiline", "true");
        editor.setAttribute(
            "aria-label",
            fallback.getAttribute("aria-label") || "Содержание записи",
        );
        editor.setAttribute("data-placeholder", "Содержание записи…");
        host.replaceChildren(editor);

        const controller = {
            form,
            row,
            host,
            editor,
            composing: false,
            savedRange: null,
        };
        controllers.set(form, controller);
        const payload = payloadField(form);
        if (payload) {
            payload.hidden = true;
            payload.setAttribute("aria-hidden", "true");
            payload.setAttribute("tabindex", "-1");
            payload.style.setProperty(
                "display",
                "none",
                "important",
            );
        }
        renderDocument(editor, parseStoredDocument(form));
        form.classList.add("is-rich-editor-ready");

        editor.addEventListener("focus", () => {
            setActiveController(controller);
            window.requestAnimationFrame(() => {
                captureSelection(controller);
            });
        });
        editor.addEventListener("mouseup", scheduleSelectionUi);
        editor.addEventListener("keyup", scheduleSelectionUi);
        editor.addEventListener("compositionstart", () => {
            controller.composing = true;
            dispatchFallbackEvent(controller, "compositionstart");
        });
        editor.addEventListener("compositionend", () => {
            controller.composing = false;
            syncController(controller, false);
            dispatchFallbackEvent(controller, "compositionend");
            dispatchFallbackEvent(controller, "input");
        });
        editor.addEventListener("input", () => {
            hideFloatingToolbar();
            syncController(controller, !controller.composing);
            window.requestAnimationFrame(() => {
                captureSelection(controller);
            });
        });
        editor.addEventListener("paste", (event) => {
            event.preventDefault();
            insertPlainText(
                editor,
                event.clipboardData?.getData("text/plain") || "",
            );
        });
        editor.addEventListener("drop", (event) => {
            event.preventDefault();
            insertPlainText(
                editor,
                event.dataTransfer?.getData("text/plain") || "",
            );
        });
        editor.addEventListener("dblclick", (event) => {
            const token = event.target.closest?.("[data-semantic-kind]");
            if (!token || !editor.contains(token)) {
                return;
            }
            event.preventDefault();
            setActiveController(controller);
            openSemanticDialog(token.dataset.semanticKind, token);
        });
        editor.addEventListener("keydown", (event) => {
            const token = event.target.closest?.("[data-semantic-kind]");
            if (
                token
                && ["Enter", " "].includes(event.key)
            ) {
                event.preventDefault();
                setActiveController(controller);
                openSemanticDialog(token.dataset.semanticKind, token);
                return;
            }
            const modifier = event.ctrlKey || event.metaKey;
            const key = event.key.toLowerCase();
            if (
                modifier
                && (event.code === "KeyB" || key === "b")
            ) {
                event.preventDefault();
                executeEditorCommand(controller, "bold");
                return;
            }
            if (
                modifier
                && (event.code === "KeyU" || key === "u")
            ) {
                event.preventDefault();
                executeEditorCommand(controller, "underline");
                return;
            }
            if (
                modifier
                && (event.code === "KeyI" || key === "i")
            ) {
                event.preventDefault();
                return;
            }
            if (
                modifier
                && event.shiftKey
                && event.code === "Digit7"
            ) {
                event.preventDefault();
                executeEditorCommand(controller, "ordered_list");
                return;
            }
            if (
                modifier
                && event.shiftKey
                && event.code === "Digit8"
            ) {
                event.preventDefault();
                executeEditorCommand(controller, "bullet_list");
                return;
            }
            if (
                modifier
                && event.shiftKey
                && event.code === "KeyM"
            ) {
                event.preventDefault();
                captureSelection(controller);
                const trigger = document.querySelector(
                    "[data-editor-semantic-trigger]",
                );
                positionSemanticPalette(trigger);
                return;
            }
            if (
                modifier
                && (event.code === "Backslash" || key === "\\")
            ) {
                event.preventDefault();
                executeEditorCommand(controller, "clear");
            }
        });
        return controller;
    }

    function bindToolbar(scope) {
        scope.querySelectorAll("[data-editor-command]").forEach((button) => {
            if (button.dataset.editorBound === "true") {
                return;
            }
            button.dataset.editorBound = "true";
            button.addEventListener("mousedown", (event) => {
                event.preventDefault();
                if (activeController) {
                    restoreSelection(activeController);
                }
            });
            button.addEventListener("click", () => {
                if (!activeController || button.disabled) {
                    return;
                }
                executeEditorCommand(
                    activeController,
                    button.dataset.editorCommand,
                );
            });
        });
    }

    document.addEventListener("selectionchange", scheduleSelectionUi);
    document.addEventListener("mouseup", scheduleSelectionUi);
    document.addEventListener("keyup", scheduleSelectionUi);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            hideFloatingToolbar();
            hideSemanticPalette();
            closeSemanticDialog();
        }
    });
    document.addEventListener("mousedown", (event) => {
        if (
            floatingToolbar?.contains(event.target)
            || semanticPalette?.contains(event.target)
            || semanticDialog?.contains(event.target)
            || ribbon?.contains(event.target)
            || event.target.closest?.("[data-rich-editor]")
        ) {
            return;
        }
        hideFloatingToolbar();
        hideSemanticPalette();
    });
    window.addEventListener(
        "scroll",
        hideFloatingToolbar,
        true,
    );
    window.addEventListener("resize", hideFloatingToolbar);

    bindToolbar(document);
    bindSemanticUi(document);
    updateToolbarState(null);

    window.EODDraftEditor = Object.freeze({
        schemaVersion: SCHEMA_VERSION,
        initializeRow,
        bindToolbar,
        syncForm(form) {
            const controller = controllers.get(form);
            if (!controller) {
                return false;
            }
            syncController(controller, false);
            return true;
        },
        seedPlainText(form, content) {
            writeFormState(form, plainTextDocument(content));
            return true;
        },
        focus(form, position = "end") {
            const controller = controllers.get(form);
            if (!controller) {
                return false;
            }
            setActiveController(controller);
            controller.editor.focus();
            if (position === "end") {
                const selection = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(controller.editor);
                range.collapse(false);
                selection.removeAllRanges();
                selection.addRange(range);
                controller.savedRange = range.cloneRange();
            } else {
                captureSelection(controller);
            }
            return true;
        },
        acceptSaved(form, payload) {
            if (!payload?.editor_payload) {
                return;
            }
            writeFormState(form, payload.editor_payload);
        },
    });
})();
