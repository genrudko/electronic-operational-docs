(() => {
    "use strict";

    const SCHEMA_VERSION = "operational-draft-editor.v4";
    const RUNTIME_REVISION = "011342";
    const LEGACY_SCHEMA_VERSIONS = new Set([
        "operational-draft-editor.v1",
        "operational-draft-editor.v2",
        "operational-draft-editor.v3",
    ]);
    const ENTRY_KINDS = Object.freeze({
        normal: {label: "Обычная запись", short: "Обычная", prefix: ""},
        command: {label: "Команда", short: "Команда", prefix: "Команда: "},
        permission: {label: "Разрешение", short: "Разрешение", prefix: "Разрешение: "},
        message: {label: "Сообщение", short: "Сообщение", prefix: "Сообщение: "},
        warning: {label: "Предупреждение", short: "Предупреждение", prefix: "Предупреждение: "},
        carryover: {label: "На следующую смену", short: "На смену", prefix: "На следующую смену: "},
    });
    const NORMATIVE_KINDS = Object.freeze({
        emergency: {label: "Аварийное событие", tone: "red", scope: "row"},
        zn_on: {label: "Включён ЗН", tone: "red", scope: "text", family: "zn"},
        zn_off: {label: "Отключён ЗН", tone: "blue", scope: "text", family: "zn", closes: "zn_on"},
        pz_install: {label: "Установлено ПЗ", tone: "red", scope: "text", family: "pz"},
        pz_remove: {label: "Снято ПЗ", tone: "blue", scope: "text", family: "pz", closes: "pz_install"},
    });
    const REFERENCE_KINDS = Object.freeze({
        equipment: {label: "Оборудование", icon: "Э"},
        document: {label: "Документ", icon: "Д"},
        person: {label: "Сотрудник / должность", icon: "Л"},
        related_entry: {label: "Связанная запись", icon: "№"},
        event_time: {label: "Время события", icon: "В"},
    });
    const controllers = new WeakMap();
    const controllerList = [];
    const workspace = document.querySelector("[data-draft-workspace]");
    const ribbon = document.querySelector("[data-editor-ribbon]");
    const ribbonStatus = document.querySelector("[data-editor-ribbon-status]");
    const floatingToolbar = document.querySelector("[data-editor-floating-toolbar]");
    const entryKindMenu = document.querySelector("[data-entry-kind-menu]");
    const referencePicker = document.querySelector("[data-reference-picker]");
    const normativeMenu = document.querySelector("[data-normative-menu]");
    const normativeMenuStatus = normativeMenu?.querySelector("[data-normative-menu-status]");
    const normativeActions = normativeMenu?.querySelector("[data-normative-actions]");
    const normativeMainFooter = normativeMenu?.querySelector(
        "[data-normative-main-footer]",
    );
    const pzNumberPanel = normativeMenu?.querySelector("[data-pz-number-panel]");
    const pzNumberTitle = normativeMenu?.querySelector("[data-pz-number-title]");
    const pzNumberInput = normativeMenu?.querySelector("[data-pz-number-input]");
    const pzNumberPreview = normativeMenu?.querySelector("[data-pz-number-preview]");
    const pzNumberError = normativeMenu?.querySelector("[data-pz-number-error]");
    const normativeSourcePanel = normativeMenu?.querySelector(
        "[data-normative-source-panel]",
    );
    const normativeSourceList = normativeMenu?.querySelector(
        "[data-normative-source-list]",
    );
    const normativeSourceError = normativeMenu?.querySelector(
        "[data-normative-source-error]",
    );
    const referenceSearch = referencePicker?.querySelector("[data-reference-search]");
    const referenceSearchLabel = referenceSearch?.closest(".draft-reference-search-label");
    const referenceResults = referencePicker?.querySelector("[data-reference-results]");
    const referenceSelection = referencePicker?.querySelector("[data-reference-selection]");
    const referenceHint = referencePicker?.querySelector("[data-reference-hint]");
    const referenceRemove = referencePicker?.querySelector("[data-reference-remove]");
    const autoReferenceToggle = document.querySelector(
        "[data-auto-reference-toggle]",
    );
    const autoReferenceScan = document.querySelector(
        "[data-auto-reference-scan]",
    );
    const autoReferenceLabel = document.querySelector(
        "[data-auto-reference-label]",
    );
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
    let entryKindViewport = null;
    let normativeState = null;
    const autoReferenceTimers = new WeakMap();
    let autoReferencesEnabled = readAutoReferencePreference();
    let simplifiedTimeEnabled = (
        workspace?.dataset.simplifiedTimeInput === "true"
        || workspace?.dataset.initialSimplifiedTime === "true"
    );

    function emptyDocument() {
        return {
            schema_version: SCHEMA_VERSION,
            entry_kind: "normal",
            blocks: [{type: "paragraph", segments: []}],
            annotations: [],
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
                segments: line ? [{text: line, marks: [], annotations: []}] : [],
            })),
            annotations: [],
        };
    }

    function normalizeMarks(value) {
        const source = Array.isArray(value) ? value : [];
        return ["bold", "italic", "underline", "strike", "text_red", "text_blue"]
            .filter((mark) => source.includes(mark));
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

    function normalizeAnnotationId(value) {
        const normalized = normalizeSingleLine(value, 64);
        return /^[A-Za-z0-9_-]{8,64}$/.test(normalized) ? normalized : "";
    }

    function normalizeNormativeAnnotation(value) {
        if (!value || typeof value !== "object") {
            return null;
        }
        const id = normalizeAnnotationId(value.id);
        const kind = String(value.kind || "");
        const label = normalizeSingleLine(value.label, 500);
        if (!id || !NORMATIVE_KINDS[kind] || !label) {
            return null;
        }
        const pzNumber = normalizeSingleLine(value.pz_number, 32)
            .replace(/^№\s*/u, "");
        const sourceEntry = normalizeSingleLine(value.source_entry, 200);
        const sourceAnnotation = normalizeAnnotationId(value.source_annotation);
        if (["pz_install", "pz_remove"].includes(kind) && !pzNumber) {
            return null;
        }
        if (["zn_off", "pz_remove"].includes(kind)) {
            if (!sourceEntry.startsWith("draft:") || !sourceAnnotation) {
                return null;
            }
        }
        return {
            id,
            kind,
            label,
            ...(pzNumber ? {pz_number: pzNumber} : {}),
            ...(sourceEntry ? {source_entry: sourceEntry} : {}),
            ...(sourceAnnotation ? {source_annotation: sourceAnnotation} : {}),
        };
    }

    function normalizeNormativeAnnotations(value) {
        const result = [];
        const seen = new Set();
        (Array.isArray(value) ? value : []).forEach((raw) => {
            const annotation = normalizeNormativeAnnotation(raw);
            if (!annotation || seen.has(annotation.id) || result.length >= 100) {
                return;
            }
            seen.add(annotation.id);
            result.push(annotation);
        });
        return result;
    }

    function normalizeSegmentAnnotations(value, allowedIds = null) {
        const result = [];
        (Array.isArray(value) ? value : []).forEach((raw) => {
            const id = normalizeAnnotationId(raw);
            if (!id || result.includes(id) || (allowedIds && !allowedIds.has(id))) {
                return;
            }
            result.push(id);
        });
        return result;
    }

    function newAnnotationId() {
        if (window.crypto?.randomUUID) {
            return window.crypto.randomUUID();
        }
        return `nm_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 12)}`;
    }

    function readAutoReferencePreference() {
        try {
            return window.localStorage.getItem("eod-auto-references") !== "off";
        } catch (error) {
            return true;
        }
    }

    function writeAutoReferencePreference(value) {
        try {
            window.localStorage.setItem(
                "eod-auto-references",
                value ? "on" : "off",
            );
        } catch (error) {
            // Настройка остаётся действующей в текущей вкладке.
        }
    }

    function normalizeSearchText(value) {
        return String(value || "")
            .toLocaleLowerCase("ru-RU")
            .replaceAll("ё", "е")
            .replace(/[^\p{L}\p{N}№]+/gu, " ")
            .trim()
            .replace(/\s+/g, " ");
    }

    function russianSearchStem(value) {
        let token = normalizeSearchText(value).replace(/\s+/g, "");
        if (token.length < 4) {
            return token;
        }
        const surnameEndings = [
            "овыми", "евыми", "инами", "ыными",
            "ового", "евого", "иного", "ыного",
            "овому", "евому", "иному", "ыному",
            "овыми", "евыми", "иными", "ыными",
            "овой", "евой", "иной", "ыной",
            "овым", "евым", "иным", "ыным",
            "овою", "евою", "иною", "ыною",
            "ова", "ева", "ина", "ына",
            "ову", "еву", "ину", "ыну",
            "ове", "еве", "ине", "ыне",
        ];
        const matched = surnameEndings.find((ending) => (
            token.endsWith(ending)
            && token.length - ending.length >= 3
        ));
        if (matched) {
            const baseEnding = matched.slice(0, 2);
            return token.slice(0, token.length - matched.length) + baseEnding;
        }
        const adjectiveEndings = [
            "ского", "скому", "ским", "ских", "ская", "скую", "ской",
            "цкого", "цкому", "цким", "цких", "цкая", "цкую", "цкой",
        ];
        const adjective = adjectiveEndings.find((ending) => token.endsWith(ending));
        if (adjective) {
            return token.slice(0, token.length - adjective.length + 2);
        }
        return token;
    }

    function searchTokens(value) {
        return normalizeSearchText(value)
            .split(" ")
            .filter(Boolean);
    }

    function levenshteinDistance(left, right, limit = 2) {
        if (Math.abs(left.length - right.length) > limit) {
            return limit + 1;
        }
        const previous = Array.from({length: right.length + 1}, (_, index) => index);
        for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
            const current = [leftIndex];
            let rowMinimum = current[0];
            for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
                const cost = left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1;
                current[rightIndex] = Math.min(
                    previous[rightIndex] + 1,
                    current[rightIndex - 1] + 1,
                    previous[rightIndex - 1] + cost,
                );
                rowMinimum = Math.min(rowMinimum, current[rightIndex]);
            }
            if (rowMinimum > limit) {
                return limit + 1;
            }
            previous.splice(0, previous.length, ...current);
        }
        return previous[right.length];
    }

    function referenceTerms(item, {includeMetadata = true} = {}) {
        const terms = Array.isArray(item?.terms) ? item.terms : [];
        const source = [item?.label, ...terms];
        if (includeMetadata) {
            source.push(item?.keywords, item?.meta);
        }
        return Array.from(
            new Set(
                source.map((value) => normalizeSingleLine(value)).filter(Boolean),
            ),
        );
    }

    function scoreReferenceItem(item, query) {
        const normalizedQuery = normalizeSearchText(query);
        if (!normalizedQuery) {
            return 100;
        }
        const terms = referenceTerms(item);
        const normalizedTerms = terms.map(normalizeSearchText).filter(Boolean);
        if (normalizedTerms.some((term) => term === normalizedQuery)) {
            return 0;
        }
        if (normalizedTerms.some((term) => term.startsWith(normalizedQuery))) {
            return 10;
        }
        if (normalizedTerms.some((term) => term.includes(normalizedQuery))) {
            return 20;
        }
        const queryTokens = searchTokens(normalizedQuery);
        const queryStems = queryTokens.map(russianSearchStem);
        const termTokens = normalizedTerms.flatMap(searchTokens);
        const termStems = termTokens.map(russianSearchStem);
        if (
            queryStems.length
            && queryStems.every((stem) => termStems.some((candidate) => (
                candidate === stem
                || candidate.startsWith(stem)
                || stem.startsWith(candidate)
            )))
        ) {
            return 30;
        }
        if (
            queryTokens.length === 1
            && queryTokens[0].length >= 4
            && termTokens.some((token) => (
                levenshteinDistance(queryTokens[0], token, 2) <= 2
            ))
        ) {
            return 40;
        }
        return null;
    }

    function updateAutoReferenceControls() {
        if (autoReferenceToggle) {
            autoReferenceToggle.classList.toggle(
                "is-active",
                autoReferencesEnabled,
            );
            autoReferenceToggle.setAttribute(
                "aria-pressed",
                String(autoReferencesEnabled),
            );
            autoReferenceToggle.title = autoReferencesEnabled
                ? "Автосвязи включены; нажмите, чтобы отключить"
                : "Автосвязи выключены; нажмите, чтобы включить";
        }
        if (autoReferenceLabel) {
            autoReferenceLabel.textContent = autoReferencesEnabled
                ? "Связь · авто включено"
                : "Связь · авто выключено";
        }
        if (autoReferenceScan) {
            autoReferenceScan.disabled = !activeController;
        }
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

    function pushTextSegment(result, text, marks, annotations = []) {
        if (!text) {
            return;
        }
        const normalizedMarks = normalizeMarks(marks);
        const normalizedAnnotations = normalizeSegmentAnnotations(annotations);
        const previous = result.at(-1);
        if (
            previous
            && !previous.reference
            && JSON.stringify(previous.marks) === JSON.stringify(normalizedMarks)
            && JSON.stringify(previous.annotations || []) === JSON.stringify(normalizedAnnotations)
        ) {
            previous.text += text;
        } else {
            result.push({text, marks: normalizedMarks, annotations: normalizedAnnotations});
        }
    }

    function pushReferenceSegment(result, reference, marks, annotations = []) {
        const normalized = normalizeReference(reference);
        if (!normalized) {
            return;
        }
        result.push({
            text: normalized.label,
            marks: normalizeMarks(marks),
            annotations: normalizeSegmentAnnotations(annotations),
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
                pushReferenceSegment(result, reference, marks, segment.annotations);
                return;
            }
            if (typeof segment.text !== "string") {
                return;
            }
            pushTextSegment(
                result,
                segment.text.replace(/\r\n/g, "\n").replace(/\r/g, "\n"),
                marks,
                segment.annotations,
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
        const annotations = sourceVersion === SCHEMA_VERSION
            ? normalizeNormativeAnnotations(value.annotations)
            : [];
        const annotationIds = new Set(annotations.map((item) => item.id));
        const state = {
            entryKind: [SCHEMA_VERSION, "operational-draft-editor.v3"].includes(sourceVersion)
                ? normalizeEntryKind(value.entry_kind)
                : "normal",
        };
        const blocks = [];
        value.blocks.forEach((block) => {
            if (!block || typeof block !== "object") {
                return;
            }
            let segmentNormalizer;
            if (sourceVersion === "operational-draft-editor.v2") {
                segmentNormalizer = (segments) => upgradeLegacySegments(segments, state);
            } else if (sourceVersion === SCHEMA_VERSION) {
                segmentNormalizer = (segments) => normalizeSegments(segments).map((segment) => ({
                    ...segment,
                    annotations: normalizeSegmentAnnotations(segment.annotations, annotationIds),
                }));
            } else {
                segmentNormalizer = (segments) => normalizeSegments(segments).map((segment) => ({
                    ...segment,
                    annotations: [],
                }));
            }
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
        const used = new Set();
        blocks.forEach((block) => {
            const groups = block.type === "paragraph"
                ? [block.segments]
                : block.items.map((item) => item.segments);
            groups.forEach((segments) => segments.forEach((segment) => {
                (segment.annotations || []).forEach((id) => used.add(id));
            }));
        });
        const retainedAnnotations = annotations.filter((item) => (
            item.kind === "emergency" || used.has(item.id)
        ));
        return {
            schema_version: SCHEMA_VERSION,
            entry_kind: state.entryKind,
            blocks: blocks.length ? blocks : emptyDocument().blocks,
            annotations: retainedAnnotations,
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

    function annotationDefinition(controller, id) {
        return controller?.annotationMap?.get(id) || null;
    }

    function appendSegment(parent, segment, controller) {
        let node = segment.reference
            ? referenceToken(segment.reference)
            : document.createTextNode(segment.text);
        if (segment.marks.includes("underline")) {
            const underline = document.createElement("u");
            underline.append(node);
            node = underline;
        }
        if (segment.marks.includes("strike")) {
            const strike = document.createElement("s");
            strike.append(node);
            node = strike;
        }
        if (segment.marks.includes("italic")) {
            const italic = document.createElement("em");
            italic.append(node);
            node = italic;
        }
        if (segment.marks.includes("bold")) {
            const strong = document.createElement("strong");
            strong.append(node);
            node = strong;
        }
        if (segment.marks.includes("text_red") || segment.marks.includes("text_blue")) {
            const color = document.createElement("span");
            color.className = segment.marks.includes("text_red")
                ? "draft-text-red"
                : "draft-text-blue";
            color.append(node);
            node = color;
        }
        const annotationIds = normalizeSegmentAnnotations(segment.annotations);
        if (annotationIds.length) {
            const wrapper = document.createElement("span");
            wrapper.className = "draft-normative-text";
            wrapper.dataset.normativeAnnotationIds = annotationIds.join(" ");
            const definitions = annotationIds
                .map((id) => annotationDefinition(controller, id))
                .filter(Boolean);
            if (definitions.some((item) => ["zn_on", "pz_install"].includes(item.kind))) {
                wrapper.classList.add("is-normative-open");
            }
            if (definitions.some((item) => ["zn_off", "pz_remove"].includes(item.kind))) {
                wrapper.classList.add("is-normative-close");
            }
            wrapper.append(node);
            node = wrapper;
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
        controller.annotations = normalized.annotations;
        controller.annotationMap = new Map(
            normalized.annotations.map((item) => [item.id, item]),
        );
        controller.entryKind = normalized.entry_kind;
        renderEntryKindBadge(controller);
        const editor = controller.editor;
        editor.replaceChildren();
        normalized.blocks.forEach((block) => {
            if (block.type === "paragraph") {
                const paragraph = document.createElement("p");
                block.segments.forEach((segment) => appendSegment(paragraph, segment, controller));
                if (!paragraph.hasChildNodes()) {
                    paragraph.append(document.createElement("br"));
                }
                editor.append(paragraph);
                return;
            }
            const list = document.createElement(block.type === "bullet_list" ? "ul" : "ol");
            block.items.forEach((item) => {
                const listItem = document.createElement("li");
                item.segments.forEach((segment) => appendSegment(listItem, segment, controller));
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
        window.requestAnimationFrame(refreshNormativePresentation);
    }

    function appendSerializedSegment(result, segment) {
        if (segment.reference) {
            pushReferenceSegment(result, segment.reference, segment.marks, segment.annotations);
        } else {
            pushTextSegment(result, segment.text, segment.marks, segment.annotations);
        }
    }

    function segmentsFromNode(node, inheritedMarks = [], inheritedAnnotations = []) {
        const result = [];
        if (node.nodeType === Node.TEXT_NODE) {
            pushTextSegment(result, node.nodeValue || "", inheritedMarks, inheritedAnnotations);
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
                inheritedAnnotations,
            );
            return result;
        }
        if (tag === "br") {
            pushTextSegment(result, "\n", inheritedMarks, inheritedAnnotations);
            return result;
        }
        const marks = [...inheritedMarks];
        if (["strong", "b"].includes(tag) && !marks.includes("bold")) {
            marks.push("bold");
        }
        if (["em", "i"].includes(tag) && !marks.includes("italic")) {
            marks.push("italic");
        }
        if (tag === "u" && !marks.includes("underline")) {
            marks.push("underline");
        }
        if (["s", "strike"].includes(tag) && !marks.includes("strike")) {
            marks.push("strike");
        }
        const rawColor = String(
            node.getAttribute?.("color") || node.style.color || "",
        ).toLocaleLowerCase("ru-RU").replace(/\s+/g, "");
        const redColor = ["#b42318", "rgb(180,35,24)"].includes(rawColor);
        const blueColor = ["#175cd3", "rgb(23,92,211)"].includes(rawColor);
        if (
            (node.classList.contains("draft-text-red") || redColor)
            && !marks.includes("text_red")
        ) {
            marks.push("text_red");
        }
        if (
            (node.classList.contains("draft-text-blue") || blueColor)
            && !marks.includes("text_blue")
        ) {
            marks.push("text_blue");
        }
        const annotations = [...inheritedAnnotations];
        normalizeSegmentAnnotations(
            String(node.dataset.normativeAnnotationIds || "").split(/\s+/),
        ).forEach((id) => {
            if (!annotations.includes(id)) {
                annotations.push(id);
            }
        });
        node.childNodes.forEach((child) => {
            segmentsFromNode(child, marks, annotations).forEach((segment) => {
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

    function editorToDocument(controller) {
        const editor = controller.editor;
        const entryKind = controller.entryKind;
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
            annotations: controller.annotations || [],
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
        const documentPayload = editorToDocument(controller);
        controller.documentPayload = writeFormState(controller.form, documentPayload);
        controller.entryKind = controller.documentPayload.entry_kind;
        renderEntryKindBadge(controller);
        updateEmptyState(controller.editor);
        if (emitInput) {
            dispatchFallbackEvent(controller, "input");
        }
        updateToolbarState(controller);
        refreshNormativePresentation();
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
        if (resolved.controller.deactivated) {
            return null;
        }
        resolved.controller.savedRange = resolved.range.cloneRange();
        setActiveController(resolved.controller);
        return resolved;
    }

    function selectEntireEditor(controller) {
        if (!controller?.editor?.isConnected) {
            return false;
        }
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(controller.editor);
        selection.removeAllRanges();
        selection.addRange(range);
        controller.savedRange = range.cloneRange();
        setActiveController(controller);
        scheduleSelectionUi();
        return true;
    }

    function finishEditorInteraction(controller, shortcut) {
        if (!controller) {
            return;
        }
        applyAutomaticReferences(controller);
        syncController(controller, false);
        hideFloatingToolbar();
        hideEntryKindMenu();
        hideReferencePicker();
        controller.form.dispatchEvent(
            new CustomEvent("eod:finish-draft-edit", {
                bubbles: true,
                detail: {
                    shortcut,
                    save: true,
                },
            }),
        );
    }

    function captureEntryKindViewport(controller = activeController) {
        const row = controller?.row;
        entryKindViewport = {
            x: window.scrollX,
            y: window.scrollY,
            row,
            rowTop: row?.getBoundingClientRect().top ?? null,
        };
    }

    function restoreEntryKindViewport(controller = activeController) {
        const snapshot = entryKindViewport;
        entryKindViewport = null;
        if (!snapshot) {
            return;
        }
        const restore = () => {
            if (controller?.editor?.isConnected) {
                controller.editor.focus({preventScroll: true});
            }
            if (snapshot.row?.isConnected && snapshot.rowTop !== null) {
                const delta = snapshot.row.getBoundingClientRect().top - snapshot.rowTop;
                if (Math.abs(delta) > 0.5) {
                    window.scrollBy(0, delta);
                }
                return;
            }
            window.scrollTo(snapshot.x, snapshot.y);
        };
        window.requestAnimationFrame(() => {
            restore();
            window.requestAnimationFrame(restore);
        });
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
                } else if (command === "italic") {
                    active = queryCommandState("italic");
                } else if (command === "underline") {
                    active = queryCommandState("underline");
                } else if (command === "strike") {
                    active = queryCommandState("strikeThrough");
                } else if (command === "bullet_list") {
                    active = queryCommandState("insertUnorderedList");
                } else if (command === "ordered_list") {
                    active = queryCommandState("insertOrderedList");
                }
            }
            button.classList.toggle("is-active", active);
            if (["bold", "italic", "underline", "strike", "bullet_list", "ordered_list"].includes(command)) {
                button.setAttribute("aria-pressed", String(active));
            }
        });
        document.querySelectorAll("[data-normative-trigger]").forEach((button) => {
            button.disabled = !controller;
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
        if (autoReferenceScan) {
            autoReferenceScan.disabled = !controller;
        }
        updateAutoReferenceControls();
    }

    function isEditorOverlayTarget(node) {
        return Boolean(
            node?.closest?.(
                "[data-editor-ribbon], "
                + "[data-editor-floating-toolbar], "
                + "[data-entry-kind-menu], "
                + "[data-normative-menu], "
                + "[data-reference-picker], "
                + "[data-reference-preview]",
            ),
        );
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
            return false;
        }
        const wasOpen = !entryKindMenu.hidden;
        if (wasOpen) {
            entryKindMenu.hidden = true;
        }
        entryKindMenu.style.removeProperty("left");
        entryKindMenu.style.removeProperty("top");
        entryKindTrigger?.setAttribute("aria-expanded", "false");
        entryKindTrigger = null;
        return wasOpen;
    }

    function openEntryKindMenu(trigger) {
        if (!entryKindMenu || !activeController || !trigger) {
            return;
        }
        const reopening = !entryKindMenu.hidden && entryKindTrigger === trigger;
        if (!entryKindViewport) {
            captureEntryKindViewport(activeController);
        }
        hideEntryKindMenu();
        if (reopening) {
            restoreEntryKindViewport(activeController);
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
            restoreEntryKindViewport(controller);
            return;
        }
        controller.entryKind = normalized;
        syncController(controller, true);
        hideEntryKindMenu();
        controller.editor.focus({preventScroll: true});
        restoreEntryKindViewport(controller);
    }

    function hideReferencePicker() {
        if (!referencePicker) {
            return;
        }
        if (!referencePicker.hidden) {
            referencePicker.hidden = true;
        }
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
        if (kind === "related_entry") {
            refreshRelatedEntryCatalog();
        }
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

        const query = normalizeSingleLine(referenceSearch?.value || "", 200);
        const items = catalogFor(referenceKind)
            .map((item, index) => ({
                item,
                index,
                score: scoreReferenceItem(item, query),
            }))
            .filter((row) => row.score !== null)
            .sort((left, right) => (
                left.score - right.score
                || left.index - right.index
            ))
            .slice(0, 12)
            .map((row) => row.item);
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

    function isWordCharacter(value) {
        return Boolean(value && /[\p{L}\p{N}]/u.test(value));
    }

    function escapedReferencePattern(term) {
        return String(term || "")
            .trim()
            .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
            .replace(/[её]/giu, "[её]")
            .replace(/\s+/g, "[\\s\\u00a0]+");
    }

    function exactTermMatches(textValue, term, candidate, priority = 40) {
        const pattern = escapedReferencePattern(term);
        if (!pattern || normalizeSearchText(term).length < 3) {
            return [];
        }
        const matches = [];
        const expression = new RegExp(pattern, "giu");
        let match = expression.exec(textValue);
        while (match) {
            const start = match.index;
            const end = start + match[0].length;
            if (
                !isWordCharacter(textValue[start - 1])
                && !isWordCharacter(textValue[end])
            ) {
                matches.push({start, end, candidate, priority});
            }
            if (match[0].length === 0) {
                expression.lastIndex += 1;
            }
            match = expression.exec(textValue);
        }
        return matches;
    }

    function equipmentLetterPattern(character) {
        const normalized = character.toLocaleLowerCase("ru-RU");
        const alternatives = {
            а: "[аa]", в: "[вv]", е: "[еёe]", к: "[кk]",
            м: "[мm]", н: "[нh]", о: "[оo]", п: "[пp]",
            р: "[рr]", с: "[сc]", т: "[тt]", у: "[уy]",
            х: "[хx]",
        };
        return alternatives[normalized]
            || normalized.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function equipmentTermPattern(term) {
        const tokens = String(term || "").match(/[\p{L}]+|\d+/gu) || [];
        if (!tokens.length) {
            return "";
        }
        return tokens.map((token) => {
            if (/^\d+$/.test(token)) {
                const numeric = String(Number.parseInt(token, 10));
                return `0*${numeric}`;
            }
            return Array.from(token).map(equipmentLetterPattern).join("");
        }).join("[\\s\\u00a0№#\\-–—._/]*");
    }

    function equipmentTermMatches(textValue, term, candidate) {
        const pattern = equipmentTermPattern(term);
        if (!pattern || normalizeSearchText(term).length < 3) {
            return [];
        }
        const matches = [];
        const expression = new RegExp(pattern, "giu");
        let match = expression.exec(textValue);
        while (match) {
            const start = match.index;
            const end = start + match[0].length;
            const trailingNumericPart = textValue
                .slice(end)
                .match(/^[\s\u00a0№#\-–—._/]*\d/u);
            if (
                !isWordCharacter(textValue[start - 1])
                && !isWordCharacter(textValue[end])
                && !trailingNumericPart
            ) {
                matches.push({
                    start,
                    end,
                    candidate,
                    priority: 80,
                });
            }
            if (match[0].length === 0) {
                expression.lastIndex += 1;
            }
            match = expression.exec(textValue);
        }
        return matches;
    }

    function personSurnameMatches(textValue, candidate) {
        const surname = candidate.item?.surname
            || searchTokens(candidate.item?.label || "")[0]
            || "";
        const surnameStem = russianSearchStem(surname);
        if (surnameStem.length < 4) {
            return [];
        }
        const matches = [];
        const expression = /[\p{L}][\p{L}-]*/gu;
        let match = expression.exec(textValue);
        while (match) {
            if (russianSearchStem(match[0]) === surnameStem) {
                matches.push({
                    start: match.index,
                    end: match.index + match[0].length,
                    candidate,
                    priority: 30,
                });
            }
            match = expression.exec(textValue);
        }
        return matches;
    }

    function personCompositeMatches(textValue, candidate) {
        const surname = candidate.item?.surname
            || searchTokens(candidate.item?.label || "")[0]
            || "";
        const surnameStem = russianSearchStem(surname);
        const positionTerms = Array.isArray(candidate.item?.position_terms)
            ? candidate.item.position_terms
            : [candidate.item?.position].filter(Boolean);
        if (surnameStem.length < 4 || !positionTerms.length) {
            return [];
        }
        const matches = [];
        positionTerms.forEach((position) => {
            const positionPattern = escapedReferencePattern(position);
            if (!positionPattern) {
                return;
            }
            const forward = new RegExp(
                `(${positionPattern})[\\s\\u00a0]+([\\p{L}][\\p{L}-]*)`,
                "giu",
            );
            let match = forward.exec(textValue);
            while (match) {
                if (russianSearchStem(match[2]) === surnameStem) {
                    matches.push({
                        start: match.index,
                        end: match.index + match[0].length,
                        candidate,
                        priority: 110,
                    });
                }
                match = forward.exec(textValue);
            }
            const reverse = new RegExp(
                `([\\p{L}][\\p{L}-]*)[\\s\\u00a0,]+(${positionPattern})`,
                "giu",
            );
            match = reverse.exec(textValue);
            while (match) {
                if (russianSearchStem(match[1]) === surnameStem) {
                    matches.push({
                        start: match.index,
                        end: match.index + match[0].length,
                        candidate,
                        priority: 105,
                    });
                }
                match = reverse.exec(textValue);
            }
        });
        return matches;
    }

    function rowVisibleText(row) {
        const editor = row.querySelector("[data-rich-editor]");
        const fallback = row.querySelector("[data-editor-fallback]");
        return normalizeSingleLine(
            editor?.innerText || fallback?.value || "",
            500,
        );
    }

    function refreshRelatedEntryCatalog() {
        const items = [];
        document.querySelectorAll(
            "[data-draft-card][data-draft-id]",
        ).forEach((row) => {
            if (row.classList.contains("is-undo-pending")) {
                return;
            }
            const draftId = row.dataset.draftId || "";
            const eventAt = row.dataset.entryAt || "";
            const eventDate = row.dataset.entryDate || eventAt.slice(0, 10);
            const eventTime = eventAt.slice(11, 16);
            if (!draftId || !eventDate || !eventTime) {
                return;
            }
            const dateParts = eventDate.split("-");
            const displayDate = dateParts.length === 3
                ? `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`
                : eventDate;
            const content = rowVisibleText(row) || "Пустая черновая запись";
            const position = Number.parseInt(
                row.dataset.entryPosition || "0",
                10,
            );
            const version = Number.parseInt(row.dataset.entryVersion || "1", 10);
            items.push({
                label: `Запись ${displayDate} ${eventTime}`,
                reference: `draft:${draftId}`,
                meta: content,
                keywords: `${displayDate} ${eventTime} ${content}`,
                event_date: eventDate,
                event_time: eventTime,
                event_at: eventAt,
                position,
                terms: [`Запись ${displayDate} ${eventTime}`, eventTime],
                preview: {
                    summary: content,
                    status: `${row.dataset.entryStatus || "Сохранена"} · версия ${version}`,
                    facts: [
                        {label: "Дата и время", value: `${displayDate} ${eventTime}`},
                        {label: "Тип записи", value: row.dataset.entryKindLabel || "Обычная запись"},
                        {label: "Автор", value: row.dataset.entryAuthor || "—"},
                        {label: "Позиция", value: String(position || "—")},
                    ],
                },
            });
        });
        referenceCatalog.related_entry = items;
        workspace?.dispatchEvent(
            new CustomEvent("eod:reference-catalog-updated", {
                detail: {catalog: referenceCatalog},
            }),
        );
        return items;
    }

    function relatedEntryCueBefore(textValue, start) {
        return textValue.slice(Math.max(0, start - 48), start).match(
            /(?:за|по\s+записи(?:\s+(?:от|за))?|в\s+записи(?:\s+(?:от|за))?|согласно\s+записи(?:\s+(?:от|за))?|запись\s+(?:от|за))\s*$/iu,
        );
    }

    function relatedEntryTimeMatches(textValue, controller) {
        const matches = [];
        const rows = refreshRelatedEntryCatalog();
        const currentReference = controller?.row?.dataset.draftId
            ? `draft:${controller.row.dataset.draftId}`
            : "";
        const currentAt = controller?.row?.dataset.entryAt || "";
        const expression = /(?:[01]?\d|2[0-3])[:.][0-5]\d/gu;
        let match = expression.exec(textValue);
        while (match) {
            const start = match.index;
            if (!relatedEntryCueBefore(textValue, start)) {
                match = expression.exec(textValue);
                continue;
            }
            const digits = match[0].replace(/\D/g, "").padStart(4, "0");
            const eventTime = `${digits.slice(0, 2)}:${digits.slice(2)}`;
            let candidates = rows.filter((item) => (
                item.event_time === eventTime
                && item.reference !== currentReference
                && (!currentAt || item.event_at < currentAt)
            ));
            const currentDate = controller?.row?.dataset.entryDate || "";
            const sameDate = candidates.filter(
                (item) => item.event_date === currentDate,
            );
            if (sameDate.length) {
                candidates = sameDate;
            }
            const mapped = candidates.map((item) => ({
                kind: "related_entry",
                item,
            }));
            if (mapped.length) {
                matches.push({
                    start,
                    end: start + match[0].length,
                    candidates: mapped,
                    priority: 130,
                });
            }
            match = expression.exec(textValue);
        }
        return matches;
    }

    function automaticReferenceCandidates() {
        refreshRelatedEntryCatalog();
        const result = [];
        ["equipment", "document", "person", "related_entry"].forEach((kind) => {
            catalogFor(kind).forEach((item) => {
                if (!item?.reference || !item?.label) {
                    return;
                }
                result.push({kind, item});
            });
        });
        return result;
    }

    function resolveAutomaticMatches(textValue, controller) {
        const rawMatches = relatedEntryTimeMatches(textValue, controller);
        automaticReferenceCandidates().forEach((candidate) => {
            const terms = referenceTerms(
                candidate.item,
                {includeMetadata: false},
            ).filter((term) => normalizeSearchText(term).length >= 3);
            terms.forEach((term) => {
                if (candidate.kind === "equipment") {
                    rawMatches.push(
                        ...equipmentTermMatches(textValue, term, candidate),
                    );
                } else if (
                    candidate.kind !== "related_entry"
                    || normalizeSearchText(term).startsWith("запись ")
                ) {
                    rawMatches.push(
                        ...exactTermMatches(textValue, term, candidate),
                    );
                }
            });
            if (candidate.kind === "person") {
                rawMatches.push(
                    ...personCompositeMatches(textValue, candidate),
                    ...personSurnameMatches(textValue, candidate),
                );
            }
        });
        const grouped = new Map();
        rawMatches.forEach((match) => {
            if (Array.isArray(match.candidates)) {
                const key = `${match.start}:${match.end}`;
                if (!grouped.has(key)) {
                    grouped.set(key, {
                        start: match.start,
                        end: match.end,
                        priority: match.priority || 0,
                        candidates: new Map(),
                    });
                }
                match.candidates.forEach((candidate) => {
                    grouped.get(key).candidates.set(
                        candidate.item.reference,
                        candidate,
                    );
                });
                grouped.get(key).priority = Math.max(
                    grouped.get(key).priority,
                    match.priority || 0,
                );
                return;
            }
            const key = `${match.start}:${match.end}`;
            if (!grouped.has(key)) {
                grouped.set(key, {
                    start: match.start,
                    end: match.end,
                    priority: match.priority || 0,
                    candidates: new Map(),
                });
            }
            grouped.get(key).candidates.set(
                match.candidate.item.reference,
                match.candidate,
            );
            grouped.get(key).priority = Math.max(
                grouped.get(key).priority,
                match.priority || 0,
            );
        });
        const ordered = Array.from(grouped.values())
            .map((match) => ({
                ...match,
                candidates: Array.from(match.candidates.values()),
            }))
            .sort((left, right) => (
                left.start - right.start
                || (right.end - right.start) - (left.end - left.start)
                || right.priority - left.priority
            ));
        const accepted = [];
        ordered.forEach((match) => {
            if (accepted.some((current) => (
                match.start < current.end && match.end > current.start
            ))) {
                return;
            }
            accepted.push(match);
        });
        return accepted;
    }

    function automaticReferenceTextNodes(editor) {
        const nodes = [];
        const walker = document.createTreeWalker(
            editor,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode(node) {
                    if (!node.nodeValue?.trim()) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    const parent = node.parentElement;
                    if (
                        parent?.closest?.(
                            "[data-reference-kind], "
                            + "[data-auto-reference-suggestion]",
                        )
                    ) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                },
            },
        );
        let node = walker.nextNode();
        while (node) {
            nodes.push(node);
            node = walker.nextNode();
        }
        return nodes;
    }

    function selectionTextBookmark(editor) {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0 || !selection.isCollapsed) {
            return null;
        }
        const range = selection.getRangeAt(0);
        if (!isRangeInsideEditor(range, editor)) {
            return null;
        }
        const prefix = document.createRange();
        prefix.selectNodeContents(editor);
        prefix.setEnd(range.startContainer, range.startOffset);
        return prefix.toString().length;
    }

    function restoreTextBookmark(editor, offset) {
        if (!Number.isInteger(offset) || offset < 0) {
            return false;
        }
        const walker = document.createTreeWalker(
            editor,
            NodeFilter.SHOW_TEXT,
        );
        let remaining = offset;
        let node = walker.nextNode();
        while (node) {
            const parentToken = node.parentElement?.closest?.(
                "[data-reference-kind]",
            );
            const visibleValue = parentToken
                ? parentToken.dataset.referenceLabel || ""
                : node.nodeValue || "";
            if (remaining <= visibleValue.length) {
                const range = document.createRange();
                if (parentToken) {
                    if (remaining === 0) {
                        range.setStartBefore(parentToken);
                    } else {
                        range.setStartAfter(parentToken);
                    }
                } else {
                    range.setStart(node, Math.min(remaining, node.length));
                }
                range.collapse(true);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                return true;
            }
            remaining -= visibleValue.length;
            if (parentToken) {
                while (
                    node
                    && node.parentElement?.closest?.("[data-reference-kind]") === parentToken
                ) {
                    node = walker.nextNode();
                }
                continue;
            }
            node = walker.nextNode();
        }
        const range = document.createRange();
        range.selectNodeContents(editor);
        range.collapse(false);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        return true;
    }

    function automaticReferenceSuggestion(visibleText, candidates) {
        const suggestion = document.createElement("span");
        suggestion.className = "draft-reference-suggestion";
        suggestion.dataset.autoReferenceSuggestion = "true";
        suggestion.dataset.autoReferenceKind = candidates[0]?.kind || "person";
        suggestion.dataset.autoReferenceCandidates = JSON.stringify(
            candidates.map(({kind, item}) => ({
                kind,
                label: item.label,
                reference: item.reference,
                meta: item.meta || "",
            })),
        );
        suggestion.title = (
            `Найдено вариантов: ${candidates.length}. `
            + "Нажмите, чтобы выбрать связь."
        );
        suggestion.textContent = visibleText;
        return suggestion;
    }

    function applyMatchesToTextNode(node, matches) {
        if (!matches.length || !node.isConnected) {
            return false;
        }
        const value = node.nodeValue || "";
        const fragment = document.createDocumentFragment();
        let cursor = 0;
        matches.forEach((match) => {
            if (match.start > cursor) {
                fragment.append(document.createTextNode(value.slice(cursor, match.start)));
            }
            const visibleText = value.slice(match.start, match.end);
            if (match.candidates.length === 1) {
                const candidate = match.candidates[0];
                fragment.append(referenceToken({
                    kind: candidate.kind,
                    label: visibleText,
                    reference: candidate.item.reference,
                }));
            } else {
                fragment.append(
                    automaticReferenceSuggestion(visibleText, match.candidates),
                );
            }
            cursor = match.end;
        });
        if (cursor < value.length) {
            fragment.append(document.createTextNode(value.slice(cursor)));
        }
        node.replaceWith(fragment);
        return true;
    }

    function applyAutomaticReferences(controller, {force = false} = {}) {
        if (
            !controller?.editor?.isConnected
            || controller.composing
            || controller.autoReferenceApplying
            || (!autoReferencesEnabled && !force)
        ) {
            return false;
        }
        const bookmark = selectionTextBookmark(controller.editor);
        controller.autoReferenceApplying = true;
        let changed = false;
        try {
            automaticReferenceTextNodes(controller.editor).forEach((node) => {
                const matches = resolveAutomaticMatches(
                    node.nodeValue || "",
                    controller,
                );
                changed = applyMatchesToTextNode(node, matches) || changed;
            });
            if (changed) {
                restoreTextBookmark(controller.editor, bookmark);
                syncController(controller, true);
                captureSelection(controller);
            }
        } finally {
            controller.autoReferenceApplying = false;
        }
        return changed;
    }

    function scheduleAutomaticReferences(controller, delay = 850) {
        const activeTimer = autoReferenceTimers.get(controller);
        if (activeTimer) {
            window.clearTimeout(activeTimer);
        }
        if (!autoReferencesEnabled) {
            autoReferenceTimers.delete(controller);
            return;
        }
        const timer = window.setTimeout(() => {
            autoReferenceTimers.delete(controller);
            applyAutomaticReferences(controller);
        }, delay);
        autoReferenceTimers.set(controller, timer);
    }

    function openAutomaticReferenceSuggestion(controller, suggestion) {
        if (!controller || !suggestion?.isConnected) {
            return;
        }
        const range = document.createRange();
        range.selectNode(suggestion);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        controller.savedRange = range.cloneRange();
        setActiveController(controller);
        referenceKind = suggestion.dataset.autoReferenceKind || "person";
        if (referenceSearch) {
            referenceSearch.value = suggestion.textContent || "";
        }
        openReferencePicker(
            document.querySelector("[data-reference-trigger]"),
            null,
            suggestion.dataset.autoReferenceKind || "person",
        );
    }

    function openReferencePicker(trigger, token = null, preferredKind = null) {
        if (!referencePicker || !activeController) {
            return;
        }
        hideEntryKindMenu();
        entryKindViewport = null;
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
        referenceKind = preferredKind || token?.dataset.referenceKind || "equipment";
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

    function referenceWheelPixels(event) {
        if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) {
            return event.deltaY * 32;
        }
        if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) {
            return event.deltaY * Math.max(120, window.innerHeight * 0.75);
        }
        return event.deltaY;
    }

    function handleReferencePickerWheel(event) {
        if (!referencePicker || referencePicker.hidden) {
            return;
        }
        const target = event.target;
        const results = target.closest?.("[data-reference-results]");
        const surface = results || referencePicker;
        const maximum = Math.max(0, surface.scrollHeight - surface.clientHeight);
        if (maximum > 0) {
            surface.scrollTop = Math.max(
                0,
                Math.min(
                    maximum,
                    surface.scrollTop + referenceWheelPixels(event),
                ),
            );
        }
        event.preventDefault();
        event.stopPropagation();
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
            italic: "italic",
            underline: "underline",
            strike: "strikeThrough",
            text_red: "foreColor",
            text_blue: "foreColor",
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
        if (["bold", "italic", "underline", "strike"].includes(command)) {
            document.execCommand("styleWithCSS", false, false);
        }
        if (["text_red", "text_blue"].includes(command)) {
            document.execCommand("styleWithCSS", false, true);
            document.execCommand(
                nativeCommand,
                false,
                command === "text_red" ? "#b42318" : "#175cd3",
            );
        } else {
            document.execCommand(nativeCommand, false, null);
        }
        captureSelection(controller);
        syncController(controller, true);
        scheduleSelectionUi();
    }

    function insertPlainText(editor, text) {
        editor.focus();
        document.execCommand("insertText", false, text);
    }

    function simplifiedTimeValue(value) {
        const digits = String(value || "").replace(/\D/g, "");
        if (![3, 4].includes(digits.length)) {
            return null;
        }
        if (digits.length === 4) {
            const numeric = Number.parseInt(digits, 10);
            if (numeric >= 1900 && numeric <= 2099) {
                return null;
            }
        }
        const padded = digits.padStart(4, "0");
        const hours = Number.parseInt(padded.slice(0, 2), 10);
        const minutes = Number.parseInt(padded.slice(2), 10);
        if (hours > 23 || minutes > 59) {
            return null;
        }
        return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
    }

    function simplifiedTimeCommitKey(event) {
        return [" ", "Enter", "Tab", ",", ";", "."].includes(event.key);
    }

    function simplifiedTimeCommitInput(event) {
        return (
            ["insertParagraph", "insertLineBreak"].includes(event.inputType)
            || (
                event.inputType === "insertText"
                && [" ", ",", ";", "."].includes(event.data)
            )
        );
    }

    function lastEditableTextDescendant(node) {
        if (!node) {
            return null;
        }
        if (node.nodeType === Node.TEXT_NODE) {
            return node.parentElement?.closest?.(
                "[data-reference-kind], [data-auto-reference-suggestion]",
            ) ? null : node;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return null;
        }
        if (node.matches?.(
            "[data-reference-kind], [data-auto-reference-suggestion]",
        )) {
            return null;
        }
        const walker = document.createTreeWalker(
            node,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode(candidate) {
                    return candidate.parentElement?.closest?.(
                        "[data-reference-kind], [data-auto-reference-suggestion]",
                    )
                        ? NodeFilter.FILTER_REJECT
                        : NodeFilter.FILTER_ACCEPT;
                },
            },
        );
        let last = null;
        let candidate = walker.nextNode();
        while (candidate) {
            last = candidate;
            candidate = walker.nextNode();
        }
        return last;
    }

    function editableTextPositionBeforeCaret(range, editor) {
        if (range.startContainer.nodeType === Node.TEXT_NODE) {
            return {
                node: range.startContainer,
                offset: range.startOffset,
            };
        }
        let container = range.startContainer;
        let offset = range.startOffset;
        while (container && editor.contains(container)) {
            let sibling = container.childNodes?.[offset - 1] || null;
            while (sibling) {
                const node = lastEditableTextDescendant(sibling);
                if (node) {
                    return {
                        node,
                        offset: node.nodeValue?.length || 0,
                    };
                }
                sibling = sibling.previousSibling;
            }
            if (container === editor) {
                break;
            }
            const parent = container.parentNode;
            offset = parent ? Array.prototype.indexOf.call(
                parent.childNodes,
                container,
            ) : 0;
            container = parent;
        }
        return null;
    }

    function simplifiedTimeCandidate(position, trailingCommit = false) {
        const {node, offset} = position;
        if (node.parentElement?.closest?.("[data-reference-kind]")) {
            return null;
        }
        const before = (node.nodeValue || "").slice(0, offset);
        const match = trailingCommit
            ? before.match(/(^|[\s(])([0-9]{3,4})([ \t,;.])$/u)
            : before.match(/(^|[\s(])([0-9]{3,4})$/u);
        if (!match) {
            return null;
        }
        const suffix = trailingCommit ? match[3] : "";
        const start = offset - suffix.length - match[2].length;
        const preceding = (node.nodeValue || "")[start - 1] || "";
        const contextBefore = before
            .slice(0, before.length - suffix.length - match[2].length)
            .trimEnd();
        if (
            /[\p{L}\p{N}№#\-–—./]/u.test(preceding)
            || /(?:№|#|[-–—./])$/u.test(contextBefore)
            || /(?:номер|документ|приказ|заявка|распоряжение|наряд|ктп)$/iu.test(
                contextBefore,
            )
        ) {
            return null;
        }
        const formatted = simplifiedTimeValue(match[2]);
        return formatted
            ? {node, offset, start, digits: match[2], formatted}
            : null;
    }

    function formatSimplifiedTimeAtCaret(
        controller,
        {trailingCommit = false} = {},
    ) {
        if (!simplifiedTimeEnabled || !controller?.editor) {
            return false;
        }
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0 || !selection.isCollapsed) {
            return false;
        }
        const range = selection.getRangeAt(0);
        if (!isRangeInsideEditor(range, controller.editor)) {
            return false;
        }
        const position = editableTextPositionBeforeCaret(
            range,
            controller.editor,
        );
        if (!position) {
            return false;
        }
        const candidate = simplifiedTimeCandidate(position, trailingCommit);
        if (!candidate) {
            return false;
        }
        candidate.node.replaceData(
            candidate.start,
            candidate.digits.length,
            candidate.formatted,
        );
        const delta = candidate.formatted.length - candidate.digits.length;
        const caret = document.createRange();
        caret.setStart(candidate.node, candidate.offset + delta);
        caret.collapse(true);
        selection.removeAllRanges();
        selection.addRange(caret);
        controller.savedRange = caret.cloneRange();
        syncController(controller, true);
        scheduleAutomaticReferences(controller, 40);
        return true;
    }

    function formatSimplifiedTimeBeforeCaret(controller) {
        return formatSimplifiedTimeAtCaret(controller);
    }

    function formatSimplifiedTimeAfterCommit(controller) {
        return formatSimplifiedTimeAtCaret(
            controller,
            {trailingCommit: true},
        );
    }

    function allNormativeAnnotations() {
        const rows = [];
        controllerList.forEach((controller) => {
            (controller.annotations || []).forEach((annotation) => {
                rows.push({
                    ...annotation,
                    entry_reference: `draft:${controller.row.dataset.draftId || ""}`,
                    entry_time: controller.row.dataset.entryAt?.slice(11, 16) || "",
                    controller,
                });
            });
        });
        return rows;
    }

    function closedNormativeIds() {
        return new Set(
            allNormativeAnnotations()
                .filter((item) => ["zn_off", "pz_remove"].includes(item.kind))
                .map((item) => item.source_annotation)
                .filter(Boolean),
        );
    }

    function normativeMarker(annotation, isClosed) {
        const marker = document.createElement("span");
        marker.className = `draft-normative-marker is-${annotation.kind}`;
        marker.dataset.normativeMarkerId = annotation.id;
        marker.title = annotation.label;
        const top = document.createElement("span");
        top.className = "draft-normative-marker-top";
        top.textContent = annotation.kind.startsWith("pz_") ? "ПЗ" : "ЗН";
        const bolt = document.createElement("span");
        bolt.className = "draft-normative-marker-bolt";
        bolt.textContent = "ϟ";
        const bottom = document.createElement("span");
        bottom.className = "draft-normative-marker-bottom";
        bottom.textContent = annotation.pz_number ? `№${annotation.pz_number}` : "";
        const cross = document.createElement("span");
        cross.className = "draft-normative-marker-cross";
        cross.setAttribute("aria-hidden", "true");
        marker.append(top, bolt, bottom, cross);
        marker.classList.toggle("is-cleared", Boolean(isClosed));
        return marker;
    }

    function renderNormativeVisas(controller, closedIds) {
        const visas = controller.row.querySelector("[data-draft-visas]");
        if (!visas) {
            return;
        }
        visas.replaceChildren();
        (controller.annotations || [])
            .filter((item) => item.kind !== "emergency")
            .forEach((annotation) => {
                visas.append(
                    normativeMarker(annotation, closedIds.has(annotation.id)),
                );
            });
        visas.classList.toggle("has-normative-markers", visas.childElementCount > 0);
    }

    function refreshNormativePresentation() {
        const closedIds = closedNormativeIds();
        controllerList.forEach((controller) => {
            const emergency = (controller.annotations || []).some(
                (item) => item.kind === "emergency",
            );
            controller.row.classList.toggle("is-emergency-event", emergency);
            controller.editor.querySelectorAll("[data-normative-annotation-ids]")
                .forEach((node) => {
                    const ids = normalizeSegmentAnnotations(
                        String(node.dataset.normativeAnnotationIds || "").split(/\s+/),
                    );
                    node.classList.toggle(
                        "is-normative-cleared",
                        ids.some((id) => closedIds.has(id)),
                    );
                });
            renderNormativeVisas(controller, closedIds);
        });
    }

    function activeNormativeSources(closeKind, pzNumber = "") {
        const sourceKind = NORMATIVE_KINDS[closeKind]?.closes;
        const closedIds = closedNormativeIds();
        return allNormativeAnnotations().filter((item) => (
            item.kind === sourceKind
            && !closedIds.has(item.id)
            && (!pzNumber || item.pz_number === pzNumber)
        ));
    }

    function selectionLabel(range) {
        return normalizeSingleLine(range?.toString() || "", 500);
    }

    function normalizePzNumber(value) {
        return normalizeSingleLine(value, 32)
            .replace(/^№\s*/u, "")
            .replace(/\s+/g, "");
    }

    function setNormativeStep(step = "main") {
        const main = step === "main";
        if (normativeActions) {
            normativeActions.hidden = !main;
        }
        if (normativeMainFooter) {
            normativeMainFooter.hidden = !main;
        }
        if (pzNumberPanel) {
            pzNumberPanel.hidden = step !== "pz-number";
        }
        if (normativeSourcePanel) {
            normativeSourcePanel.hidden = step !== "source";
        }
        if (pzNumberError) {
            pzNumberError.textContent = "";
        }
        if (normativeSourceError) {
            normativeSourceError.textContent = "";
        }
        if (normativeState) {
            normativeState.step = step;
        }
    }

    function updatePzNumberPreview() {
        const normalized = normalizePzNumber(pzNumberInput?.value || "");
        if (pzNumberPreview) {
            pzNumberPreview.textContent = normalized ? `№${normalized}` : "№—";
        }
    }

    function showPzNumberStep(kind, preserveValue = false) {
        if (!normativeState || !pzNumberPanel || !pzNumberInput) {
            return;
        }
        normativeState.pendingKind = kind;
        setNormativeStep("pz-number");
        if (pzNumberTitle) {
            pzNumberTitle.textContent = kind === "pz_remove"
                ? "Какое ПЗ снято?"
                : "Какое ПЗ установлено?";
        }
        if (!preserveValue) {
            pzNumberInput.value = "";
        }
        updatePzNumberPreview();
        positionPopover(
            normativeMenu,
            normativeState.trigger?.getBoundingClientRect()
                || normativeMenu.getBoundingClientRect(),
            430,
        );
        window.requestAnimationFrame(() => {
            pzNumberInput.focus({preventScroll: true});
            pzNumberInput.select();
        });
    }

    function normativeSourceButton(item, kind, pzNumber) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "draft-normative-source-option";

        const marker = document.createElement("span");
        marker.className = "draft-normative-source-marker";
        marker.textContent = item.pz_number ? `ПЗ №${item.pz_number}` : "ЗН";

        const body = document.createElement("span");
        const title = document.createElement("strong");
        title.textContent = item.label;
        const meta = document.createElement("small");
        meta.textContent = item.entry_time
            ? `Исходная запись в ${item.entry_time}`
            : "Исходная запись";
        body.append(title, meta);
        button.append(marker, body);
        button.addEventListener("click", () => {
            commitNormativeAction(kind, pzNumber, item);
        });
        return button;
    }

    function showNormativeSourceStep(kind, pzNumber, candidates) {
        if (!normativeState || !normativeSourceList) {
            return;
        }
        normativeState.pendingKind = kind;
        normativeState.pendingPzNumber = pzNumber;
        normativeSourceList.replaceChildren(
            ...candidates.map((item) => (
                normativeSourceButton(item, kind, pzNumber)
            )),
        );
        setNormativeStep("source");
        positionPopover(
            normativeMenu,
            normativeState.trigger?.getBoundingClientRect()
                || normativeMenu.getBoundingClientRect(),
            430,
        );
        window.requestAnimationFrame(() => {
            normativeSourceList.querySelector("button")?.focus({
                preventScroll: true,
            });
        });
    }

    function wrapRangeWithNormativeAnnotation(controller, range, annotation) {
        if (!range || range.collapsed || !isRangeInsideEditor(range, controller.editor)) {
            window.alert("Сначала выделите фрагмент записи, к которому относится отметка.");
            return false;
        }
        const wrapper = document.createElement("span");
        wrapper.className = "draft-normative-text";
        wrapper.dataset.normativeAnnotationIds = annotation.id;
        wrapper.classList.add(
            ["zn_on", "pz_install"].includes(annotation.kind)
                ? "is-normative-open"
                : "is-normative-close",
        );
        try {
            wrapper.append(range.extractContents());
            range.insertNode(wrapper);
        } catch (_error) {
            window.alert("Не удалось применить отметку к этому выделению. Выделите текст внутри одной записи повторно.");
            return false;
        }
        controller.annotations = [...(controller.annotations || []), annotation];
        controller.annotationMap.set(annotation.id, annotation);
        const selection = window.getSelection();
        const caret = document.createRange();
        caret.selectNodeContents(wrapper);
        caret.collapse(false);
        selection.removeAllRanges();
        selection.addRange(caret);
        controller.savedRange = caret.cloneRange();
        syncController(controller, true);
        return true;
    }

    function toggleEmergencyAnnotation(controller) {
        const existing = (controller.annotations || []).find(
            (item) => item.kind === "emergency",
        );
        if (existing) {
            controller.annotations = controller.annotations.filter(
                (item) => item.id !== existing.id,
            );
            controller.annotationMap.delete(existing.id);
        } else {
            const annotation = {
                id: newAnnotationId(),
                kind: "emergency",
                label: "Аварийное событие",
            };
            controller.annotations = [...(controller.annotations || []), annotation];
            controller.annotationMap.set(annotation.id, annotation);
        }
        syncController(controller, true);
    }

    function removeNormativeFromSelection(controller, range) {
        const nodes = new Set();
        controller.editor.querySelectorAll("[data-normative-annotation-ids]")
            .forEach((node) => {
                try {
                    if (range.intersectsNode(node)) {
                        nodes.add(node);
                    }
                } catch (_error) {
                    // Detached node is ignored.
                }
            });
        if (!nodes.size) {
            const ancestor = range.startContainer.nodeType === Node.ELEMENT_NODE
                ? range.startContainer
                : range.startContainer.parentElement;
            const wrapper = ancestor?.closest?.("[data-normative-annotation-ids]");
            if (wrapper && controller.editor.contains(wrapper)) {
                nodes.add(wrapper);
            }
        }
        const removed = new Set();
        nodes.forEach((node) => {
            normalizeSegmentAnnotations(
                String(node.dataset.normativeAnnotationIds || "").split(/\s+/),
            ).forEach((id) => removed.add(id));
            node.replaceWith(...node.childNodes);
        });
        if (!removed.size) {
            window.alert("В выделенном фрагменте нет нормативной отметки.");
            return;
        }
        controller.annotations = (controller.annotations || []).filter(
            (item) => !removed.has(item.id),
        );
        removed.forEach((id) => controller.annotationMap.delete(id));
        syncController(controller, true);
    }

    function commitNormativeAction(kind, pzNumber = "", source = null) {
        const state = normativeState;
        if (!state?.controller) {
            return;
        }
        const controller = state.controller;
        const range = state.range?.cloneRange()
            || controller.savedRange?.cloneRange();
        const label = selectionLabel(range);
        if (!label) {
            window.alert("Сначала выделите текст включения, установки, отключения или снятия.");
            return;
        }
        const annotation = {
            id: newAnnotationId(),
            kind,
            label,
            ...(pzNumber ? {pz_number: pzNumber} : {}),
            ...(source ? {
                source_entry: source.entry_reference,
                source_annotation: source.id,
            } : {}),
        };
        if (wrapRangeWithNormativeAnnotation(controller, range, annotation)) {
            hideNormativeMenu();
        }
    }

    function continueNormativeAction(kind, pzNumber = "") {
        if (["zn_off", "pz_remove"].includes(kind)) {
            const candidates = activeNormativeSources(kind, pzNumber);
            if (!candidates.length) {
                const target = normativeState?.step === "pz-number"
                    ? pzNumberError
                    : normativeSourceError;
                if (target) {
                    target.textContent = pzNumber
                        ? `Действующая установка ПЗ №${pzNumber} не найдена.`
                        : "Действующая исходная отметка не найдена.";
                } else {
                    window.alert("Не найдена действующая исходная отметка для снятия или отключения.");
                }
                return;
            }
            if (candidates.length > 1) {
                showNormativeSourceStep(kind, pzNumber, candidates);
                return;
            }
            commitNormativeAction(kind, pzNumber, candidates[0]);
            return;
        }
        commitNormativeAction(kind, pzNumber);
    }

    function applyNormativeAction(kind) {
        const state = normativeState;
        if (
            !state?.controller
            || (kind !== "remove" && !NORMATIVE_KINDS[kind])
        ) {
            return;
        }
        const controller = state.controller;
        const range = state.range?.cloneRange()
            || controller.savedRange?.cloneRange();
        if (kind === "emergency") {
            toggleEmergencyAnnotation(controller);
            hideNormativeMenu();
            return;
        }
        if (kind === "remove") {
            if (range) {
                removeNormativeFromSelection(controller, range);
            }
            hideNormativeMenu();
            return;
        }
        if (!selectionLabel(range)) {
            window.alert("Сначала выделите текст включения, установки, отключения или снятия.");
            return;
        }
        if (["pz_install", "pz_remove"].includes(kind)) {
            showPzNumberStep(kind);
            return;
        }
        continueNormativeAction(kind);
    }

    function applyPzNumberStep() {
        const kind = normativeState?.pendingKind;
        if (!["pz_install", "pz_remove"].includes(kind)) {
            return;
        }
        const pzNumber = normalizePzNumber(pzNumberInput?.value || "");
        if (!pzNumber) {
            if (pzNumberError) {
                pzNumberError.textContent = "Укажите номер ПЗ.";
            }
            pzNumberInput?.focus({preventScroll: true});
            return;
        }
        continueNormativeAction(kind, pzNumber);
    }

    function hideNormativeMenu() {
        if (!normativeMenu) {
            normativeState = null;
            return;
        }
        normativeMenu.hidden = true;
        normativeMenu.style.removeProperty("left");
        normativeMenu.style.removeProperty("top");
        normativeState?.trigger?.setAttribute("aria-expanded", "false");
        setNormativeStep("main");
        normativeState = null;
    }

    function openNormativeMenu(trigger) {
        if (!normativeMenu || !activeController || !trigger) {
            return;
        }
        captureSelection(activeController);
        const range = activeController.savedRange?.cloneRange() || null;
        normativeState = {
            controller: activeController,
            range,
            trigger,
            step: "main",
            pendingKind: "",
            pendingPzNumber: "",
        };
        setNormativeStep("main");
        if (normativeMenuStatus) {
            normativeMenuStatus.textContent = range && !range.collapsed
                ? `Выделено: ${selectionLabel(range)}`
                : "Для ПЗ/ЗН сначала выделите относящийся к операции текст";
        }
        trigger.setAttribute("aria-expanded", "true");
        positionPopover(normativeMenu, trigger.getBoundingClientRect(), 430);
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
            deactivated: false,
            entryKind: "normal",
            documentPayload: emptyDocument(),
            annotations: [],
            annotationMap: new Map(),
            autoReferenceApplying: false,
        };
        controllers.set(form, controller);
        controllerList.push(controller);
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
            controller.deactivated = false;
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
        editor.addEventListener("beforeinput", (event) => {
            if (
                !controller.composing
                && simplifiedTimeCommitInput(event)
            ) {
                formatSimplifiedTimeBeforeCaret(controller);
            }
        });
        editor.addEventListener("input", () => {
            hideFloatingToolbar();
            if (!controller.composing) {
                formatSimplifiedTimeAfterCommit(controller);
            }
            syncController(controller, !controller.composing);
            if (!controller.autoReferenceApplying) {
                scheduleAutomaticReferences(controller);
            }
            window.requestAnimationFrame(() => captureSelection(controller));
        });
        editor.addEventListener("click", (event) => {
            const suggestion = event.target.closest?.(
                "[data-auto-reference-suggestion]",
            );
            if (!suggestion || !editor.contains(suggestion)) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            openAutomaticReferenceSuggestion(controller, suggestion);
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
            if (modifier && event.key === "Enter") {
                event.preventDefault();
                event.stopPropagation();
                finishEditorInteraction(controller, "ctrl-enter");
                return;
            }
            if (
                !modifier
                && simplifiedTimeCommitKey(event)
            ) {
                formatSimplifiedTimeBeforeCaret(controller);
            }
            if (
                event.key === "Escape"
                && (referencePicker?.hidden ?? true)
                && (entryKindMenu?.hidden ?? true)
                && (normativeMenu?.hidden ?? true)
            ) {
                event.preventDefault();
                event.stopPropagation();
                finishEditorInteraction(controller, "escape");
                return;
            }
            if (modifier && (event.code === "KeyA" || key === "a")) {
                event.preventDefault();
                selectEntireEditor(controller);
                return;
            }
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
                executeEditorCommand(controller, "italic");
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
            button.addEventListener("mousedown", (event) => {
                event.preventDefault();
                if (!entryKindViewport) {
                    captureEntryKindViewport(activeController);
                }
            });
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
        scope.querySelectorAll("[data-normative-trigger]").forEach((button) => {
            if (button.dataset.normativeBound === "true") {
                return;
            }
            button.dataset.normativeBound = "true";
            button.addEventListener("mousedown", (event) => {
                event.preventDefault();
                captureSelection(activeController);
            });
            button.addEventListener("click", () => openNormativeMenu(button));
        });
        scope.querySelectorAll("[data-normative-action]").forEach((button) => {
            if (button.dataset.normativeActionBound === "true") {
                return;
            }
            button.dataset.normativeActionBound = "true";
            button.addEventListener("click", () => {
                applyNormativeAction(button.dataset.normativeAction);
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
        scope.querySelectorAll("[data-auto-reference-toggle]").forEach((button) => {
            if (button.dataset.autoReferenceBound === "true") {
                return;
            }
            button.dataset.autoReferenceBound = "true";
            button.addEventListener("click", () => {
                autoReferencesEnabled = !autoReferencesEnabled;
                writeAutoReferencePreference(autoReferencesEnabled);
                updateAutoReferenceControls();
                if (autoReferencesEnabled && activeController) {
                    applyAutomaticReferences(activeController);
                }
            });
        });
        scope.querySelectorAll("[data-auto-reference-scan]").forEach((button) => {
            if (button.dataset.autoReferenceScanBound === "true") {
                return;
            }
            button.dataset.autoReferenceScanBound = "true";
            button.addEventListener("mousedown", (event) => {
                event.preventDefault();
            });
            button.addEventListener("click", () => {
                if (activeController) {
                    applyAutomaticReferences(activeController, {force: true});
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
    workspace?.addEventListener("eod:simplified-time-setting", (event) => {
        simplifiedTimeEnabled = Boolean(event.detail?.enabled);
    });

    referenceSearch?.addEventListener("input", renderReferenceResults);
    referencePicker?.addEventListener(
        "wheel",
        handleReferencePickerWheel,
        {passive: false},
    );
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
        button.addEventListener("click", () => hideReferencePicker());
    });
    normativeMenu?.querySelectorAll("[data-normative-close]").forEach((button) => {
        button.addEventListener("click", () => hideNormativeMenu());
    });
    pzNumberInput?.addEventListener("input", updatePzNumberPreview);
    pzNumberInput?.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            applyPzNumberStep();
        }
    });
    normativeMenu?.querySelector("[data-pz-number-apply]")
        ?.addEventListener("click", applyPzNumberStep);
    normativeMenu?.querySelector("[data-pz-number-cancel]")
        ?.addEventListener("click", () => setNormativeStep("main"));
    normativeMenu?.querySelector("[data-normative-source-cancel]")
        ?.addEventListener("click", () => {
            if (normativeState?.pendingKind === "pz_remove") {
                showPzNumberStep("pz_remove", true);
            } else {
                setNormativeStep("main");
            }
        });

    document.addEventListener("selectionchange", scheduleSelectionUi);
    document.addEventListener("mouseup", scheduleSelectionUi);
    document.addEventListener("keyup", scheduleSelectionUi);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            hideFloatingToolbar();
            const menuClosed = hideEntryKindMenu();
            hideReferencePicker();
            hideNormativeMenu();
            if (menuClosed) {
                restoreEntryKindViewport(activeController);
            }
        }
    });
    document.addEventListener("mousedown", (event) => {
        if (
            floatingToolbar?.contains(event.target)
            || entryKindMenu?.contains(event.target)
            || referencePicker?.contains(event.target)
            || normativeMenu?.contains(event.target)
            || ribbon?.contains(event.target)
            || event.target.closest?.("[data-rich-editor]")
        ) {
            return;
        }
        hideFloatingToolbar();
        const menuClosed = hideEntryKindMenu();
        hideReferencePicker();
        hideNormativeMenu();
        if (menuClosed) {
            restoreEntryKindViewport(activeController);
        }
        const previousController = activeController;
        window.setTimeout(() => {
            if (
                previousController
                && previousController === activeController
                && !previousController.form.contains(document.activeElement)
                && !isEditorOverlayTarget(document.activeElement)
            ) {
                previousController.deactivated = true;
                previousController.savedRange = null;
                previousController.form.dispatchEvent(
                    new CustomEvent("eod:editor-deactivate", {
                        bubbles: true,
                    }),
                );
                setActiveController(null);
            }
        }, 0);
    });
    window.addEventListener("scroll", () => {
        hideFloatingToolbar();
        if (referencePicker && !referencePicker.hidden) {
            return;
        }
        const menuClosed = hideEntryKindMenu();
        hideReferencePicker();
        hideNormativeMenu();
        if (menuClosed) {
            restoreEntryKindViewport(activeController);
        }
    }, true);
    window.addEventListener("resize", () => {
        hideFloatingToolbar();
        const menuClosed = hideEntryKindMenu();
        hideReferencePicker();
        hideNormativeMenu();
        if (menuClosed) {
            restoreEntryKindViewport(activeController);
        }
    });

    bindToolbar(document);
    refreshNormativePresentation();
    refreshRelatedEntryCatalog();
    updateAutoReferenceControls();
    updateToolbarState(null);
    document.documentElement.dataset.eodDraftEditorRevision = RUNTIME_REVISION;

    window.EODDraftEditor = Object.freeze({
        schemaVersion: SCHEMA_VERSION,
        runtimeRevision: RUNTIME_REVISION,
        initializeRow,
        bindToolbar,
        applyAutomaticReferences(form, force = false) {
            const controller = controllers.get(form);
            return applyAutomaticReferences(controller, {force});
        },
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
            controller.deactivated = false;
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
        deactivate(form) {
            const controller = controllers.get(form);
            if (!controller) {
                return false;
            }
            controller.deactivated = true;
            controller.form.dispatchEvent(
                new CustomEvent("eod:editor-deactivate", {
                    bubbles: true,
                }),
            );
            hideFloatingToolbar();
            hideEntryKindMenu();
            hideReferencePicker();
            if (document.activeElement === controller.editor) {
                controller.editor.blur();
            }
            const selection = window.getSelection();
            if (selection && selection.rangeCount) {
                const range = selection.getRangeAt(0);
                if (isRangeInsideEditor(range, controller.editor)) {
                    selection.removeAllRanges();
                }
            }
            controller.savedRange = null;
            if (activeController === controller) {
                setActiveController(null);
            }
            window.requestAnimationFrame(() => {
                if (!controller.deactivated) {
                    return;
                }
                controller.row.classList.remove("is-editor-active");
                if (activeController === controller) {
                    activeController = null;
                    updateToolbarState(null);
                }
            });
            return true;
        },
        selectAll(form) {
            const controller = controllers.get(form);
            return selectEntireEditor(controller);
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
