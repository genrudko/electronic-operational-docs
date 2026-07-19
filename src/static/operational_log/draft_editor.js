(() => {
    "use strict";

    const SCHEMA_VERSION = "operational-draft-editor.v3";
    const LEGACY_SCHEMA_VERSIONS = new Set([
        "operational-draft-editor.v1",
        "operational-draft-editor.v2",
    ]);
    const ENTRY_KINDS = Object.freeze({
        normal: {label: "Обычная запись", short: "Обычная", prefix: ""},
        command: {label: "Команда", short: "Команда", prefix: "Команда: "},
        permission: {label: "Разрешение", short: "Разрешение", prefix: "Разрешение: "},
        message: {label: "Сообщение", short: "Сообщение", prefix: "Сообщение: "},
        warning: {label: "Предупреждение", short: "Предупреждение", prefix: "Предупреждение: "},
        carryover: {label: "На следующую смену", short: "На смену", prefix: "На следующую смену: "},
    });
    const REFERENCE_KINDS = Object.freeze({
        equipment: {label: "Оборудование", icon: "Э"},
        document: {label: "Документ", icon: "Д"},
        person: {label: "Сотрудник / должность", icon: "Л"},
        related_entry: {label: "Связанная запись", icon: "№"},
        event_time: {label: "Время события", icon: "В"},
    });
    const controllers = new WeakMap();
    const ribbon = document.querySelector("[data-editor-ribbon]");
    const ribbonStatus = document.querySelector("[data-editor-ribbon-status]");
    const floatingToolbar = document.querySelector("[data-editor-floating-toolbar]");
    const entryKindMenu = document.querySelector("[data-entry-kind-menu]");
    const referencePicker = document.querySelector("[data-reference-picker]");
    const referenceSearch = referencePicker?.querySelector("[data-reference-search]");
    const referenceSearchLabel = referenceSearch?.closest(".draft-reference-search-label");
    const referenceResults = referencePicker?.querySelector("[data-reference-results]");
    const referenceSelection = referencePicker?.querySelector("[data-reference-selection]");
    const referenceHint = referencePicker?.querySelector("[data-reference-hint]");
    const referenceRemove = referencePicker?.querySelector("[data-reference-remove]");
    const catalogNode = document.getElementById("draft-semantic-reference-catalog");
    let referenceCatalog = {};
    try {
        referenceCatalog = catalogNode
            ? JSON.parse(catalogNode.textContent || "{}")
            : {};
    } catch (error) {
        referenceCatalog = {};
    }
    let activeController = null;
    let selectionFrame = null;
    let entryKindTrigger = null;
    let referenceTrigger = null;
    let referenceState = null;
    let referenceKind = "equipment";

    function emptyDocument() {
        return {
            schema_version: SCHEMA_VERSION,
            entry_kind: "normal",
            blocks: [{type: "paragraph", segments: []}],
        };
    }

    function plainTextDocument(value) {
        const text = String(value || "")
            .replace(/\r\n/g, "\n")
            .replace(/\r/g, "\n");
        return {
            schema_version: SCHEMA_VERSION,
            entry_kind: "normal",
            blocks: text.split("\n").map((line) => ({
                type: "paragraph",
                segments: line ? [{text: line, marks: []}] : [],
            })),
        };
    }

    function normalizeMarks(value) {
        const source = Array.isArray(value) ? value : [];
        return ["bold", "underline"].filter((mark) => source.includes(mark));
    }

    function normalizeSingleLine(value, maxLength = 500) {
        return String(value || "")
            .replace(/\r\n/g, "\n")
            .replace(/\r/g, "\n")
            .split(/\s+/)
            .filter(Boolean)
            .join(" ")
            .trim()
            .slice(0, maxLength);
    }

    function normalizeEntryKind(value) {
        return ENTRY_KINDS[value] ? value : "normal";
    }

    function normalizeReference(value) {
        if (!value || typeof value !== "object") {
            return null;
        }
        const kind = String(value.kind || "");
        if (!REFERENCE_KINDS[kind]) {
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

    function normalizeLegacySemantic(value) {
        if (!value || typeof value !== "object") {
            return null;
        }
        const kind = String(value.kind || "");
        if (!ENTRY_KINDS[kind] && !REFERENCE_KINDS[kind]) {
            return null;
        }
        const label = normalizeSingleLine(value.label, 500);
        if (!label) {
            return null;
        }
        const reference = normalizeSingleLine(value.reference, 200);
        return {kind, label, ...(reference ? {reference} : {})};
    }

    function pushTextSegment(result, text, marks) {
        if (!text) {
            return;
        }
        const normalizedMarks = normalizeMarks(marks);
        const previous = result.at(-1);
        if (
            previous
            && !previous.reference
            && JSON.stringify(previous.marks) === JSON.stringify(normalizedMarks)
        ) {
            previous.text += text;
        } else {
            result.push({text, marks: normalizedMarks});
        }
    }

    function pushReferenceSegment(result, reference, marks) {
        const normalized = normalizeReference(reference);
        if (!normalized) {
            return;
        }
        result.push({
            text: normalized.label,
            marks: normalizeMarks(marks),
            reference: normalized,
        });
    }

    function normalizeSegments(value) {
        const source = Array.isArray(value) ? value : [];
        const result = [];
        source.forEach((segment) => {
            if (!segment || typeof segment !== "object") {
                return;
            }
            const marks = normalizeMarks(segment.marks);
            const reference = normalizeReference(segment.reference);
            if (reference) {
                pushReferenceSegment(result, reference, marks);
                return;
            }
            if (typeof segment.text !== "string") {
                return;
            }
            pushTextSegment(
                result,
                segment.text.replace(/\r\n/g, "\n").replace(/\r/g, "\n"),
                marks,
            );
        });
        return result;
    }

    function upgradeLegacySegments(value, state) {
        const result = [];
        const source = Array.isArray(value) ? value : [];
        source.forEach((segment) => {
            if (!segment || typeof segment !== "object") {
                return;
            }
            const marks = normalizeMarks(segment.marks);
            const semantic = normalizeLegacySemantic(segment.semantic);
            if (semantic) {
                if (ENTRY_KINDS[semantic.kind] && semantic.kind !== "normal") {
                    if (state.entryKind === "normal") {
                        state.entryKind = semantic.kind;
                        pushTextSegment(result, semantic.label, marks);
                    } else {
                        pushTextSegment(
                            result,
                            `${ENTRY_KINDS[semantic.kind].prefix}${semantic.label}`,
                            marks,
                        );
                    }
                    return;
                }
                pushReferenceSegment(
                    result,
                    {
                        kind: semantic.kind,
                        label: semantic.label,
                        reference: semantic.reference || "",
                    },
                    marks,
                );
                return;
            }
            if (typeof segment.text === "string") {
                pushTextSegment(result, segment.text, marks);
            }
        });
        return result;
    }

    function normalizeDocument(value, fallbackText = "") {
        if (!value || typeof value !== "object" || !Array.isArray(value.blocks)) {
            return plainTextDocument(fallbackText);
        }
        const sourceVersion = value.schema_version;
        if (sourceVersion !== SCHEMA_VERSION && !LEGACY_SCHEMA_VERSIONS.has(sourceVersion)) {
            return plainTextDocument(fallbackText);
        }
        const state = {
            entryKind: sourceVersion === SCHEMA_VERSION
                ? normalizeEntryKind(value.entry_kind)
                : "normal",
        };
        const blocks = [];
        value.blocks.forEach((block) => {
            if (!block || typeof block !== "object") {
                return;
            }
            const segmentNormalizer = sourceVersion === "operational-draft-editor.v2"
                ? (segments) => upgradeLegacySegments(segments, state)
                : normalizeSegments;
            if (block.type === "paragraph") {
                blocks.push({
                    type: "paragraph",
                    segments: segmentNormalizer(block.segments),
                });
                return;
            }
            if (["bullet_list", "ordered_list"].includes(block.type) && Array.isArray(block.items)) {
                blocks.push({
                    type: block.type,
                    items: block.items.map((item) => ({
                        segments: segmentNormalizer(item?.segments),
                    })),
                });
            }
        });
        return {
            schema_version: SCHEMA_VERSION,
            entry_kind: state.entryKind,
            blocks: blocks.length ? blocks : emptyDocument().blocks,
        };
    }

    function documentBodyLines(documentPayload) {
        const lines = [];
        documentPayload.blocks.forEach((block) => {
            if (block.type === "paragraph") {
                lines.push(block.segments.map((segment) => segment.text).join(""));
                return;
            }
            block.items.forEach((item, index) => {
                const text = item.segments.map((segment) => segment.text).join("");
                const prefix = block.type === "bullet_list" ? "• " : `${index + 1}. `;
                lines.push(prefix + text);
            });
        });
        return lines;
    }

    function documentToText(documentPayload) {
        const lines = documentBodyLines(documentPayload);
        if (!lines.join("\n").trim()) {
            return lines.join("\n");
        }
        const prefix = ENTRY_KINDS[documentPayload.entry_kind]?.prefix || "";
        if (prefix) {
            const index = lines.findIndex((line) => line.trim());
            if (index >= 0) {
                lines[index] = prefix + lines[index];
            }
        }
        return lines.join("\n");
    }

    function referenceToken(reference) {
        const definition = REFERENCE_KINDS[reference.kind];
        const token = document.createElement("span");
        token.className = "draft-reference-token";
        token.dataset.referenceKind = reference.kind;
        token.dataset.referenceLabel = reference.label;
        if (reference.reference) {
            token.dataset.referenceValue = reference.reference;
        }
        token.contentEditable = "false";
        token.setAttribute("role", "button");
        token.setAttribute("tabindex", "0");
        token.setAttribute("aria-label", `${definition.label}: ${reference.label}`);
        token.title = reference.reference
            ? `${definition.label}: ${reference.label}`
            : definition.label;

        const label = document.createElement("span");
        label.className = "draft-reference-token-label";
        label.textContent = reference.label;
        token.append(label);

        const icon = document.createElement("span");
        icon.className = "draft-reference-token-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = "↗";
        token.append(icon);
        return token;
    }

    function appendSegment(parent, segment) {
        let node = segment.reference
            ? referenceToken(segment.reference)
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

    function renderEntryKindBadge(controller) {
        const kind = normalizeEntryKind(controller.entryKind);
        controller.entryKind = kind;
        controller.kindBadge.dataset.entryKind = kind;
        controller.kindBadge.textContent = ENTRY_KINDS[kind].label;
        controller.kindBadge.hidden = kind === "normal";
    }

    function renderDocument(controller, documentPayload) {
        const normalized = normalizeDocument(documentPayload);
        controller.documentPayload = normalized;
        controller.entryKind = normalized.entry_kind;
        renderEntryKindBadge(controller);
        const editor = controller.editor;
        editor.replaceChildren();
        normalized.blocks.forEach((block) => {
            if (block.type === "paragraph") {
                const paragraph = document.createElement("p");
                block.segments.forEach((segment) => appendSegment(paragraph, segment));
                if (!paragraph.hasChildNodes()) {
                    paragraph.append(document.createElement("br"));
                }
                editor.append(paragraph);
                return;
            }
            const list = document.createElement(block.type === "bullet_list" ? "ul" : "ol");
            block.items.forEach((item) => {
                const listItem = document.createElement("li");
                item.segments.forEach((segment) => appendSegment(listItem, segment));
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

    function appendSerializedSegment(result, segment) {
        if (segment.reference) {
            pushReferenceSegment(result, segment.reference, segment.marks);
        } else {
            pushTextSegment(result, segment.text, segment.marks);
        }
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
        if (node.matches?.("[data-reference-kind]")) {
            pushReferenceSegment(
                result,
                {
                    kind: node.dataset.referenceKind,
                    label: node.dataset.referenceLabel,
                    reference: node.dataset.referenceValue || "",
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
                appendSerializedSegment(result, segment);
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

    function editorToDocument(editor, entryKind = "normal") {
        const blocks = [];
        Array.from(editor.childNodes).forEach((node) => {
            if (
                node.nodeType === Node.ELEMENT_NODE
                && ["ul", "ol"].includes(node.tagName.toLowerCase())
            ) {
                const items = Array.from(node.children)
                    .filter((item) => item.tagName.toLowerCase() === "li")
                    .map((item) => ({segments: editableBlockSegments(item)}));
                blocks.push({
                    type: node.tagName.toLowerCase() === "ul" ? "bullet_list" : "ordered_list",
                    items,
                });
                return;
            }
            blocks.push({type: "paragraph", segments: editableBlockSegments(node)});
        });
        return normalizeDocument({
            schema_version: SCHEMA_VERSION,
            entry_kind: normalizeEntryKind(entryKind),
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
        if (fallback) {
            fallback.dispatchEvent(new Event(type, {bubbles: true}));
        }
    }

    function syncController(controller, emitInput = false) {
        const documentPayload = editorToDocument(controller.editor, controller.entryKind);
        controller.documentPayload = writeFormState(controller.form, documentPayload);
        controller.entryKind = controller.documentPayload.entry_kind;
        renderEntryKindBadge(controller);
        updateEmptyState(controller.editor);
        if (emitInput) {
            dispatchFallbackEvent(controller, "input");
        }
        updateToolbarState(controller);
        return controller.documentPayload;
    }

    function queryCommandState(command) {
        try {
            return document.queryCommandState(command);
        } catch (error) {
            return false;
        }
    }

    function commandButtons() {
        return Array.from(document.querySelectorAll("[data-editor-command]"));
    }

    function isRangeInsideEditor(range, editor) {
        return Boolean(
            range
            && editor?.isConnected
            && editor.contains(range.startContainer)
            && editor.contains(range.endContainer),
        );
    }

    function selectionController() {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            return null;
        }
        const range = selection.getRangeAt(0);
        const node = range.commonAncestorContainer;
        const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
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
        const time = controller.row.querySelector("[data-quick-time]")?.value || "—";
        const sequence = controller.row.querySelector("[data-draft-version]")?.textContent?.trim() || "";
        return sequence ? `Запись ${time} · ${sequence}` : `Запись ${time}`;
    }

    function setActiveController(controller) {
        if (activeController === controller) {
            updateToolbarState(controller);
            return;
        }
        document.querySelectorAll("[data-draft-card].is-editor-active").forEach((row) => {
            row.classList.remove("is-editor-active");
        });
        activeController = controller;
        if (controller) {
            controller.row.classList.add("is-editor-active");
            if (ribbonStatus) {
                ribbonStatus.textContent = recordLabel(controller);
            }
        } else if (ribbonStatus) {
            ribbonStatus.textContent = "Выбери запись для редактирования";
        }
        updateToolbarState(controller);
    }

    function restoreSelection(controller) {
        if (!controller?.savedRange || !isRangeInsideEditor(controller.savedRange, controller.editor)) {
            return false;
        }
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(controller.savedRange.cloneRange());
        return true;
    }

    function captureSelection(controller = null) {
        const resolved = selectionController();
        if (!resolved || (controller && resolved.controller !== controller)) {
            return null;
        }
        resolved.controller.savedRange = resolved.range.cloneRange();
        setActiveController(resolved.controller);
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
        floatingToolbar.hidden = false;
        const rect = range.getBoundingClientRect();
        const toolbarRect = floatingToolbar.getBoundingClientRect();
        const margin = 8;
        const left = Math.max(
            margin,
            Math.min(
                window.innerWidth - toolbarRect.width - margin,
                rect.left + (rect.width - toolbarRect.width) / 2,
            ),
        );
        const topAbove = rect.top - toolbarRect.height - 8;
        const top = topAbove >= margin ? topAbove : rect.bottom + 8;
        floatingToolbar.style.left = `${Math.round(left)}px`;
        floatingToolbar.style.top = `${Math.round(top)}px`;
    }

    function refreshSelectionUi() {
        selectionFrame = null;
        const resolved = captureSelection();
        if (!resolved || resolved.range.collapsed) {
            hideFloatingToolbar();
            updateToolbarState(activeController);
            return;
        }
        positionFloatingToolbar(resolved.range);
        updateToolbarState(resolved.controller);
    }

    function scheduleSelectionUi() {
        if (selectionFrame !== null) {
            window.cancelAnimationFrame(selectionFrame);
        }
        selectionFrame = window.requestAnimationFrame(refreshSelectionUi);
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
                    active = queryCommandState("insertUnorderedList");
                } else if (command === "ordered_list") {
                    active = queryCommandState("insertOrderedList");
                }
            }
            button.classList.toggle("is-active", active);
            if (["bold", "underline", "bullet_list", "ordered_list"].includes(command)) {
                button.setAttribute("aria-pressed", String(active));
            }
        });
        document.querySelectorAll("[data-reference-trigger]").forEach((button) => {
            button.disabled = !controller;
        });
        document.querySelectorAll("[data-entry-kind-trigger]").forEach((button) => {
            button.disabled = !controller;
            const label = button.querySelector("[data-entry-kind-current]");
            if (label) {
                label.textContent = controller
                    ? ENTRY_KINDS[controller.entryKind].short
                    : "Тип записи";
            }
        });
        document.querySelectorAll("[data-entry-kind-option]").forEach((button) => {
            const active = Boolean(controller && button.dataset.entryKindOption === controller.entryKind);
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-checked", String(active));
        });
        ribbon?.classList.toggle("has-active-editor", Boolean(controller));
    }

    function positionPopover(popover, anchorRect, preferredWidth = 360) {
        if (!popover || !anchorRect) {
            return;
        }
        popover.hidden = false;
        const rect = popover.getBoundingClientRect();
        const margin = 8;
        const width = rect.width || preferredWidth;
        const left = Math.max(
            margin,
            Math.min(window.innerWidth - width - margin, anchorRect.left),
        );
        let top = anchorRect.bottom + 8;
        if (top + rect.height > window.innerHeight - margin) {
            top = Math.max(margin, anchorRect.top - rect.height - 8);
        }
        popover.style.left = `${Math.round(left)}px`;
        popover.style.top = `${Math.round(top)}px`;
    }

    function hideEntryKindMenu() {
        if (!entryKindMenu) {
            return;
        }
        entryKindMenu.hidden = true;
        entryKindMenu.style.removeProperty("left");
        entryKindMenu.style.removeProperty("top");
        entryKindTrigger?.setAttribute("aria-expanded", "false");
        entryKindTrigger = null;
    }

    function openEntryKindMenu(trigger) {
        if (!entryKindMenu || !activeController || !trigger) {
            return;
        }
        const reopening = !entryKindMenu.hidden && entryKindTrigger === trigger;
        hideEntryKindMenu();
        if (reopening) {
            return;
        }
        entryKindTrigger = trigger;
        trigger.setAttribute("aria-expanded", "true");
        positionPopover(entryKindMenu, trigger.getBoundingClientRect(), 260);
        updateToolbarState(activeController);
    }

    function setEntryKind(controller, kind) {
        const normalized = normalizeEntryKind(kind);
        if (!controller || controller.entryKind === normalized) {
            hideEntryKindMenu();
            return;
        }
        controller.entryKind = normalized;
        syncController(controller, true);
        hideEntryKindMenu();
        controller.editor.focus({preventScroll: true});
    }

    function hideReferencePicker() {
        if (!referencePicker) {
            return;
        }
        referencePicker.hidden = true;
        referencePicker.style.removeProperty("left");
        referencePicker.style.removeProperty("top");
        referenceTrigger?.setAttribute("aria-expanded", "false");
        referenceTrigger = null;
        referenceState = null;
    }

    function editableBlock(node, editor) {
        const element = node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
        const block = element?.closest?.("p, li");
        return block && editor.contains(block) ? block : null;
    }

    function selectionIsSingleBlock(range, editor) {
        return Boolean(
            range
            && editableBlock(range.startContainer, editor)
            && editableBlock(range.startContainer, editor) === editableBlock(range.endContainer, editor),
        );
    }

    function selectedTextForState(state) {
        if (state.token) {
            return state.token.dataset.referenceLabel || "";
        }
        return normalizeSingleLine(state.range?.toString() || "", 500);
    }

    function catalogFor(kind) {
        const items = referenceCatalog?.[kind];
        return Array.isArray(items) ? items : [];
    }

    function renderReferenceResults() {
        if (!referenceResults || !referenceState) {
            return;
        }
        referenceResults.replaceChildren();
        const selected = selectedTextForState(referenceState);
        if (referenceSelection) {
            referenceSelection.textContent = selected
                ? `В тексте: ${selected}`
                : "Текст будет вставлен из выбранного объекта";
        }
        referencePicker?.querySelectorAll("[data-reference-kind-option]").forEach((button) => {
            const active = button.dataset.referenceKindOption === referenceKind;
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });

        if (referenceKind === "event_time") {
            const value = selected || new Intl.DateTimeFormat("ru-RU", {
                hour: "2-digit",
                minute: "2-digit",
            }).format(new Date());
            const button = document.createElement("button");
            button.type = "button";
            button.className = "draft-reference-result";
            button.dataset.referenceResult = "event-time";
            button.dataset.referenceLabel = value;
            button.dataset.referenceValue = `event-time:${value}`;
            const strong = document.createElement("strong");
            strong.textContent = value;
            const small = document.createElement("small");
            small.textContent = "Вставить как время события";
            button.append(strong, small);
            referenceResults.append(button);
            if (referenceHint) {
                referenceHint.textContent = "Время вставляется сразу в выделенный фрагмент или в позицию курсора.";
            }
            return;
        }

        const query = normalizeSingleLine(referenceSearch?.value || "", 200).toLocaleLowerCase("ru-RU");
        const items = catalogFor(referenceKind)
            .filter((item) => {
                if (!query) {
                    return true;
                }
                const haystack = `${item.label || ""} ${item.meta || ""} ${item.keywords || ""}`
                    .toLocaleLowerCase("ru-RU");
                return haystack.includes(query);
            })
            .slice(0, 12);
        items.forEach((item, index) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "draft-reference-result";
            button.dataset.referenceResult = String(index);
            button.dataset.referenceLabel = String(item.label || "");
            button.dataset.referenceValue = String(item.reference || "");
            const strong = document.createElement("strong");
            strong.textContent = String(item.label || "");
            const small = document.createElement("small");
            small.textContent = String(item.meta || REFERENCE_KINDS[referenceKind].label);
            button.append(strong, small);
            referenceResults.append(button);
        });
        if (!items.length) {
            const empty = document.createElement("p");
            empty.className = "draft-reference-empty";
            empty.textContent = query
                ? "Совпадений в справочнике нет."
                : "В справочнике пока нет доступных объектов.";
            referenceResults.append(empty);
        }
        if (referenceHint) {
            referenceHint.textContent = selected
                ? "Выбранный объект будет связан с уже выделенным текстом."
                : "Выбранное наименование будет вставлено в позицию курсора.";
        }
    }

    function openReferencePicker(trigger, token = null) {
        if (!referencePicker || !activeController) {
            return;
        }
        hideEntryKindMenu();
        let range = null;
        if (token) {
            range = document.createRange();
            range.selectNode(token);
        } else {
            restoreSelection(activeController);
            const resolved = selectionController();
            range = resolved?.controller === activeController
                ? resolved.range.cloneRange()
                : activeController.savedRange?.cloneRange();
        }
        if (!range || !isRangeInsideEditor(range, activeController.editor)) {
            activeController.editor.focus({preventScroll: true});
            range = document.createRange();
            range.selectNodeContents(activeController.editor);
            range.collapse(false);
        }
        if (!token && !selectionIsSingleBlock(range, activeController.editor)) {
            activeController.editor.setCustomValidity?.("");
            return;
        }
        referenceState = {
            controller: activeController,
            range: range.cloneRange(),
            token,
        };
        referenceKind = token?.dataset.referenceKind || "equipment";
        referenceTrigger = trigger;
        trigger?.setAttribute("aria-expanded", "true");
        if (referenceSearch) {
            referenceSearch.value = token
                ? ""
                : normalizeSingleLine(range.toString(), 120);
            if (referenceSearchLabel) {
                referenceSearchLabel.hidden = referenceKind === "event_time";
            }
        }
        if (referenceRemove) {
            referenceRemove.hidden = !token;
        }
        renderReferenceResults();
        const anchorRect = token?.getBoundingClientRect()
            || (!range.collapsed ? range.getBoundingClientRect() : trigger?.getBoundingClientRect());
        positionPopover(referencePicker, anchorRect || activeController.editor.getBoundingClientRect(), 430);
        window.requestAnimationFrame(() => {
            if (referenceKind !== "event_time") {
                referenceSearch?.focus({preventScroll: true});
                referenceSearch?.select();
            }
        });
    }

    function placeCaretAfter(node) {
        const selection = window.getSelection();
        const range = document.createRange();
        range.setStartAfter(node);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
        return range;
    }

    function applyReference(reference) {
        if (!referenceState) {
            return;
        }
        const controller = referenceState.controller;
        const normalized = normalizeReference(reference);
        if (!normalized) {
            return;
        }
        if (referenceState.token?.isConnected) {
            const replacement = referenceToken(normalized);
            referenceState.token.replaceWith(replacement);
            controller.savedRange = placeCaretAfter(replacement).cloneRange();
        } else {
            const range = referenceState.range.cloneRange();
            const visibleLabel = normalizeSingleLine(range.toString(), 500) || normalized.label;
            const tokenReference = {...normalized, label: visibleLabel};
            const token = referenceToken(tokenReference);
            const insertionAtCaret = range.collapsed;
            range.deleteContents();
            range.insertNode(token);
            if (insertionAtCaret) {
                const spacer = document.createTextNode(" ");
                token.after(spacer);
                controller.savedRange = placeCaretAfter(spacer).cloneRange();
            } else {
                controller.savedRange = placeCaretAfter(token).cloneRange();
            }
        }
        setActiveController(controller);
        controller.editor.focus({preventScroll: true});
        syncController(controller, true);
        hideReferencePicker();
        hideFloatingToolbar();
    }

    function removeReference() {
        if (!referenceState?.token?.isConnected) {
            hideReferencePicker();
            return;
        }
        const controller = referenceState.controller;
        const text = document.createTextNode(referenceState.token.dataset.referenceLabel || "");
        referenceState.token.replaceWith(text);
        controller.savedRange = placeCaretAfter(text).cloneRange();
        controller.editor.focus({preventScroll: true});
        syncController(controller, true);
        hideReferencePicker();
    }

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

        const kindBadge = document.createElement("span");
        kindBadge.className = "draft-entry-kind-badge";
        kindBadge.dataset.entryKind = "normal";
        kindBadge.hidden = true;

        const editor = document.createElement("div");
        editor.className = "draft-rich-editor";
        editor.contentEditable = "true";
        editor.spellcheck = true;
        editor.dataset.richEditor = "true";
        editor.dataset.empty = "true";
        editor.setAttribute("role", "textbox");
        editor.setAttribute("aria-multiline", "true");
        editor.setAttribute("aria-label", fallback.getAttribute("aria-label") || "Содержание записи");
        editor.setAttribute("data-placeholder", "Содержание записи…");
        host.replaceChildren(kindBadge, editor);

        const controller = {
            form,
            row,
            host,
            kindBadge,
            editor,
            composing: false,
            savedRange: null,
            entryKind: "normal",
            documentPayload: emptyDocument(),
        };
        controllers.set(form, controller);
        const payload = payloadField(form);
        if (payload) {
            payload.hidden = true;
            payload.setAttribute("aria-hidden", "true");
            payload.setAttribute("tabindex", "-1");
            payload.style.setProperty("display", "none", "important");
        }
        renderDocument(controller, parseStoredDocument(form));
        writeFormState(form, controller.documentPayload);
        form.classList.add("is-rich-editor-ready");

        editor.addEventListener("focus", () => {
            setActiveController(controller);
            window.requestAnimationFrame(() => captureSelection(controller));
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
            window.requestAnimationFrame(() => captureSelection(controller));
        });
        editor.addEventListener("paste", (event) => {
            event.preventDefault();
            insertPlainText(editor, event.clipboardData?.getData("text/plain") || "");
        });
        editor.addEventListener("drop", (event) => {
            event.preventDefault();
            insertPlainText(editor, event.dataTransfer?.getData("text/plain") || "");
        });
        editor.addEventListener("dblclick", (event) => {
            const token = event.target.closest?.("[data-reference-kind]");
            if (!token || !editor.contains(token)) {
                return;
            }
            event.preventDefault();
            setActiveController(controller);
            openReferencePicker(
                document.querySelector("[data-reference-trigger]"),
                token,
            );
        });
        editor.addEventListener("keydown", (event) => {
            const token = event.target.closest?.("[data-reference-kind]");
            if (token && ["Enter", " "].includes(event.key)) {
                event.preventDefault();
                setActiveController(controller);
                openReferencePicker(
                    document.querySelector("[data-reference-trigger]"),
                    token,
                );
                return;
            }
            const modifier = event.ctrlKey || event.metaKey;
            const key = event.key.toLowerCase();
            if (modifier && (event.code === "KeyB" || key === "b")) {
                event.preventDefault();
                executeEditorCommand(controller, "bold");
                return;
            }
            if (modifier && (event.code === "KeyU" || key === "u")) {
                event.preventDefault();
                executeEditorCommand(controller, "underline");
                return;
            }
            if (modifier && (event.code === "KeyI" || key === "i")) {
                event.preventDefault();
                return;
            }
            if (modifier && event.shiftKey && event.code === "Digit7") {
                event.preventDefault();
                executeEditorCommand(controller, "ordered_list");
                return;
            }
            if (modifier && event.shiftKey && event.code === "Digit8") {
                event.preventDefault();
                executeEditorCommand(controller, "bullet_list");
                return;
            }
            if (modifier && event.shiftKey && event.code === "KeyM") {
                event.preventDefault();
                captureSelection(controller);
                openReferencePicker(document.querySelector("[data-reference-trigger]"));
                return;
            }
            if (modifier && (event.code === "Backslash" || key === "\\")) {
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
                executeEditorCommand(activeController, button.dataset.editorCommand);
            });
        });

        scope.querySelectorAll("[data-entry-kind-trigger]").forEach((button) => {
            if (button.dataset.entryKindBound === "true") {
                return;
            }
            button.dataset.entryKindBound = "true";
            button.addEventListener("click", () => openEntryKindMenu(button));
        });
        scope.querySelectorAll("[data-entry-kind-option]").forEach((button) => {
            if (button.dataset.entryKindOptionBound === "true") {
                return;
            }
            button.dataset.entryKindOptionBound = "true";
            button.addEventListener("click", () => {
                if (activeController) {
                    setEntryKind(activeController, button.dataset.entryKindOption);
                }
            });
        });
        scope.querySelectorAll("[data-reference-trigger]").forEach((button) => {
            if (button.dataset.referenceBound === "true") {
                return;
            }
            button.dataset.referenceBound = "true";
            button.addEventListener("mousedown", (event) => {
                event.preventDefault();
                captureSelection(activeController);
            });
            button.addEventListener("click", () => {
                if (activeController) {
                    openReferencePicker(button);
                }
            });
        });
    }

    referencePicker?.querySelectorAll("[data-reference-kind-option]").forEach((button) => {
        button.addEventListener("click", () => {
            referenceKind = button.dataset.referenceKindOption;
            if (referenceSearch) {
                if (referenceSearchLabel) {
                    referenceSearchLabel.hidden = referenceKind === "event_time";
                }
                if (referenceKind !== "event_time") {
                    referenceSearch.focus({preventScroll: true});
                }
            }
            renderReferenceResults();
        });
    });
    referenceSearch?.addEventListener("input", renderReferenceResults);
    referenceResults?.addEventListener("click", (event) => {
        const button = event.target.closest?.("[data-reference-result]");
        if (!button) {
            return;
        }
        applyReference({
            kind: referenceKind,
            label: button.dataset.referenceLabel,
            reference: button.dataset.referenceValue || "",
        });
    });
    referenceRemove?.addEventListener("click", removeReference);
    referencePicker?.querySelectorAll("[data-reference-close]").forEach((button) => {
        button.addEventListener("click", hideReferencePicker);
    });

    document.addEventListener("selectionchange", scheduleSelectionUi);
    document.addEventListener("mouseup", scheduleSelectionUi);
    document.addEventListener("keyup", scheduleSelectionUi);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            hideFloatingToolbar();
            hideEntryKindMenu();
            hideReferencePicker();
        }
    });
    document.addEventListener("mousedown", (event) => {
        if (
            floatingToolbar?.contains(event.target)
            || entryKindMenu?.contains(event.target)
            || referencePicker?.contains(event.target)
            || ribbon?.contains(event.target)
            || event.target.closest?.("[data-rich-editor]")
        ) {
            return;
        }
        hideFloatingToolbar();
        hideEntryKindMenu();
        hideReferencePicker();
    });
    window.addEventListener("scroll", () => {
        hideFloatingToolbar();
        hideEntryKindMenu();
        hideReferencePicker();
    }, true);
    window.addEventListener("resize", () => {
        hideFloatingToolbar();
        hideEntryKindMenu();
        hideReferencePicker();
    });

    bindToolbar(document);
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
            const documentPayload = plainTextDocument(content);
            const controller = controllers.get(form);
            writeFormState(form, documentPayload);
            if (controller) {
                renderDocument(controller, documentPayload);
            }
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
            const normalized = writeFormState(form, payload.editor_payload);
            const controller = controllers.get(form);
            if (controller) {
                controller.documentPayload = normalized;
                controller.entryKind = normalized.entry_kind;
                renderEntryKindBadge(controller);
            }
        },
    });
})();
