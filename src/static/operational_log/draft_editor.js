(() => {
    "use strict";

    const SCHEMA_VERSION = "operational-draft-editor.v1";
    const controllers = new WeakMap();
    let activeController = null;

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

    function normalizeSegments(value) {
        const source = Array.isArray(value) ? value : [];
        const result = [];
        source.forEach((segment) => {
            if (!segment || typeof segment.text !== "string") {
                return;
            }
            const text = segment.text
                .replace(/\r\n/g, "\n")
                .replace(/\r/g, "\n");
            if (!text) {
                return;
            }
            const marks = normalizeMarks(segment.marks);
            const previous = result.at(-1);
            if (
                previous
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
            || value.schema_version !== SCHEMA_VERSION
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

    function appendSegment(parent, segment) {
        let node = document.createTextNode(segment.text);
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
            && JSON.stringify(previous.marks)
                === JSON.stringify(normalizedMarks)
        ) {
            previous.text += text;
        } else {
            result.push({text, marks: normalizedMarks});
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

    function updateToolbarState(controller) {
        controller.form
            .querySelectorAll("[data-editor-command]")
            .forEach((button) => {
                const command = button.dataset.editorCommand;
                let active = false;
                if (command === "bold") {
                    active = queryCommandState("bold");
                } else if (command === "underline") {
                    active = queryCommandState("underline");
                } else if (command === "bullet_list") {
                    active = queryCommandState("insertUnorderedList");
                } else if (command === "ordered_list") {
                    active = queryCommandState("insertOrderedList");
                }
                button.classList.toggle("is-active", active);
                if ([
                    "bold",
                    "underline",
                    "bullet_list",
                    "ordered_list",
                ].includes(command)) {
                    button.setAttribute("aria-pressed", String(active));
                }
            });
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
        controller.editor.focus();
        if (["bold", "underline"].includes(command)) {
            document.execCommand("styleWithCSS", false, false);
        }
        document.execCommand(nativeCommand, false, null);
        syncController(controller, true);
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
        };
        controllers.set(form, controller);
        renderDocument(editor, parseStoredDocument(form));
        form.classList.add("is-rich-editor-ready");

        editor.addEventListener("focus", () => {
            activeController = controller;
            updateToolbarState(controller);
        });
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
            syncController(controller, !controller.composing);
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
        editor.addEventListener("keydown", (event) => {
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
            });
            button.addEventListener("click", () => {
                const form = button.closest("[data-draft-form]");
                const controller = form ? controllers.get(form) : null;
                if (!controller || button.disabled) {
                    return;
                }
                executeEditorCommand(
                    controller,
                    button.dataset.editorCommand,
                );
            });
        });
    }

    document.addEventListener("selectionchange", () => {
        if (activeController) {
            updateToolbarState(activeController);
        }
    });

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
            controller.editor.focus();
            if (position === "end") {
                const selection = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(controller.editor);
                range.collapse(false);
                selection.removeAllRanges();
                selection.addRange(range);
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
