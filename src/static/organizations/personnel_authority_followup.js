(() => {
    // Progressive enhancement only. Layout-critical authority CSS is linked
    // synchronously by the server-rendered page and must never be injected here.
    const interactiveSelector = [
        "a",
        "button",
        "input",
        "select",
        "textarea",
        "label",
        "summary",
        "details",
        "[contenteditable='true']",
    ].join(",");

    const hasSelectedText = () => Boolean(
        window.getSelection?.().toString().trim(),
    );

    const employeeLinkFromRow = (row) => [...row.querySelectorAll("a[href]")]
        .find((link) => link.pathname.includes("/organization/employees/"));

    document.querySelectorAll("tr[data-authority-row]").forEach((row) => {
        const employeeLink = employeeLinkFromRow(row);
        if (!employeeLink) return;

        row.classList.add("is-authority-row-link");
        row.tabIndex = 0;
        row.setAttribute("role", "link");
        row.setAttribute(
            "aria-label",
            `Открыть карточку сотрудника ${employeeLink.textContent.trim()}`,
        );

        row.addEventListener("click", (event) => {
            if (event.target.closest(interactiveSelector) || hasSelectedText()) return;
            if (event.ctrlKey || event.metaKey) {
                window.open(employeeLink.href, "_blank", "noopener");
                return;
            }
            window.location.assign(employeeLink.href);
        });

        row.addEventListener("keydown", (event) => {
            if (event.target !== row || !["Enter", " "].includes(event.key)) return;
            event.preventDefault();
            window.location.assign(employeeLink.href);
        });
    });

    const categoryLabels = {
        "АТП": "Административно-технический персонал",
        "ОП": "Оперативный персонал",
        "ОРП": "Оперативно-ремонтный персонал",
        "РП": "Ремонтный персонал",
        "АТП/ОП": "Совмещённая категория",
    };
    const categoryPattern = /^(АТП\/ОП|АТП|ОП|ОРП|РП)\s*·\s*(.+)$/u;
    let primaryCategory = null;

    document.querySelectorAll(".authority-source-item > strong").forEach((heading) => {
        const match = heading.textContent.trim().match(categoryPattern);
        if (!match) return;

        const [, category, description] = match;
        primaryCategory ||= category;
        heading.closest(".authority-source-item")?.setAttribute(
            "data-category",
            category,
        );

        const chip = document.createElement("span");
        chip.className = "personnel-category-chip";
        chip.textContent = category;
        chip.title = categoryLabels[category];

        heading.classList.add("authority-qualification-heading");
        heading.replaceChildren(chip, document.createTextNode(description));
    });

    const hero = document.querySelector(".authority-person-hero");
    const heroCopy = hero?.querySelector(":scope > div:nth-child(2)");
    if (hero && heroCopy && primaryCategory) {
        hero.setAttribute("data-category", primaryCategory);
        const categoryRow = document.createElement("div");
        categoryRow.className = "authority-person-category-row";

        const chip = document.createElement("span");
        chip.className = "personnel-category-chip";
        chip.textContent = primaryCategory;

        const label = document.createElement("small");
        label.textContent = categoryLabels[primaryCategory];

        categoryRow.append(chip, label);
        heroCopy.append(categoryRow);
    }

    const authorityRoot = document.querySelector("[data-authority-page]");
    const compactMedia = window.matchMedia("(max-width: 61.25rem)");
    const mobileMedia = window.matchMedia("(max-width: 47.99rem)");
    if (!authorityRoot) return;

    let preambleBuilt = false;
    let mobileMatrixBuilt = false;
    let disclosureCompactState = null;
    let treeDisclosure = null;
    let legendDisclosure = null;
    let activeMobileCondition = null;
    const mobileRows = [];

    const makeSummary = (label) => {
        const summary = document.createElement("summary");
        summary.textContent = label;
        summary.setAttribute("aria-expanded", "false");
        return summary;
    };

    const syncDisclosureMode = () => {
        if (!preambleBuilt) return;
        const isCompact = compactMedia.matches;
        if (disclosureCompactState === isCompact) return;
        disclosureCompactState = isCompact;
        [treeDisclosure, legendDisclosure].forEach((details) => {
            if (!details) return;
            const summary = details.querySelector(":scope > summary");
            if (isCompact) {
                details.style.removeProperty("display");
                details.open = false;
                if (summary) {
                    summary.hidden = false;
                    summary.setAttribute("aria-expanded", "false");
                }
            } else {
                details.style.display = "contents";
                details.open = true;
                if (summary) {
                    summary.hidden = true;
                    summary.setAttribute("aria-expanded", "true");
                }
            }
        });
    };

    const enhancePreamble = () => {
        const tree = authorityRoot.querySelector(".authority-org-tree");
        if (!tree || tree.dataset.responsiveEnhanced === "true") return;

        const heading = tree.querySelector(":scope > .authority-tree-heading");
        const allOrganization = tree.querySelector(":scope > [data-division-filter='']");
        const treeList = tree.querySelector(":scope > .authority-tree-list");
        const reference = tree.querySelector(":scope > .authority-tree-reference");
        if (!heading || !allOrganization || !treeList || !reference) return;

        treeDisclosure = document.createElement("details");
        treeDisclosure.className = "authority-mobile-preamble-disclosure authority-mobile-tree-disclosure";
        const treeSummary = makeSummary("Структура и фильтр");
        treeDisclosure.append(treeSummary, heading, allOrganization, treeList);

        legendDisclosure = document.createElement("details");
        legendDisclosure.className = "authority-mobile-preamble-disclosure authority-mobile-legend-disclosure";
        const legendSummary = makeSummary("Обозначения");
        legendDisclosure.append(legendSummary, reference);

        [treeDisclosure, legendDisclosure].forEach((details) => {
            const summary = details.querySelector(":scope > summary");
            details.addEventListener("toggle", () => {
                summary?.setAttribute("aria-expanded", String(details.open));
            });
        });

        tree.replaceChildren(treeDisclosure, legendDisclosure);
        tree.dataset.responsiveEnhanced = "true";
        preambleBuilt = true;
    };

    const rightMetadata = () => {
        const byCode = new Map();
        const headers = [...authorityRoot.querySelectorAll(".authority-right-header th[data-right-column]")];
        const categoryCells = [...authorityRoot.querySelectorAll(".authority-category-header th")].slice(1);
        let offset = 0;
        categoryCells.forEach((categoryCell) => {
            const category = categoryCell.textContent.trim() || "Прочие права";
            const count = Number(categoryCell.colSpan || 1);
            for (let index = 0; index < count; index += 1) {
                const header = headers[offset];
                offset += 1;
                if (!header) continue;
                const code = header.dataset.rightColumn;
                const button = header.querySelector("button");
                byCode.set(code, {
                    category,
                    name: button?.title?.trim() || button?.textContent?.trim() || code,
                });
            }
        });
        return byCode;
    };

    const makeQualification = (sourceCell) => {
        const block = document.createElement("div");
        block.className = "authority-mobile-qualification";

        const chip = sourceCell.querySelector(".personnel-category-chip")?.cloneNode(true);
        if (chip) block.append(chip);

        const primary = sourceCell.querySelector(".authority-qualification-primary")?.textContent.trim();
        const scope = sourceCell.querySelector(".authority-qualification-scope")?.textContent.trim();
        if (primary) {
            const value = document.createElement("span");
            value.textContent = primary;
            block.append(value);
        }
        if (scope) {
            const value = document.createElement("small");
            value.textContent = scope;
            block.append(value);
        }
        sourceCell.querySelectorAll(".special-qualification-chip").forEach((item) => {
            block.append(item.cloneNode(true));
        });
        if (!block.children.length) {
            const empty = document.createElement("small");
            empty.textContent = "Квалификация не опубликована";
            block.append(empty);
        }
        return block;
    };

    const buildMobileEmployee = (sourceRow, metadata, rowIndex) => {
        const card = document.createElement("details");
        card.className = "authority-mobile-employee";
        card.dataset.mobileAuthorityEmployee = String(rowIndex);

        const summary = document.createElement("summary");
        const identity = document.createElement("div");
        identity.className = "authority-mobile-identity";

        const sourceName = sourceRow.querySelector(".matrix-sticky-name a");
        if (sourceName) identity.append(sourceName.cloneNode(true));

        const position = document.createElement("span");
        position.textContent = sourceRow.querySelector(".matrix-sticky-position")?.textContent.trim() || "Должность не указана";
        identity.append(position);

        const qualificationCell = sourceRow.querySelector(".matrix-sticky-qualification");
        if (qualificationCell) identity.append(makeQualification(qualificationCell));
        summary.append(identity);

        const grantedCells = [...sourceRow.querySelectorAll(".authority-right-cell")]
            .filter((cell) => cell.querySelector("a"));
        const conditionalCount = grantedCells.filter((cell) => cell.classList.contains("is-conditional")).length;
        const counts = document.createElement("div");
        counts.className = "authority-mobile-counts";
        const provided = document.createElement("span");
        provided.textContent = `Предоставлено ${grantedCells.length}`;
        const conditional = document.createElement("span");
        conditional.textContent = `С условием ${conditionalCount}`;
        counts.append(provided, conditional);
        summary.append(counts);
        card.append(summary);

        const rights = document.createElement("div");
        rights.className = "authority-mobile-rights";
        const groups = new Map();

        grantedCells.forEach((cell, cellIndex) => {
            const sourceLink = cell.querySelector("a");
            const code = cell.dataset.rightCell || "";
            const meta = metadata.get(code) || { category: "Прочие права", name: sourceLink?.getAttribute("aria-label")?.split(":")[0] || code };
            if (!groups.has(meta.category)) {
                const group = document.createElement("section");
                group.className = "authority-mobile-right-group";
                const heading = document.createElement("h3");
                heading.textContent = meta.category;
                group.append(heading);
                groups.set(meta.category, group);
                rights.append(group);
            }

            const row = document.createElement("div");
            row.className = "authority-mobile-right-row";
            const name = document.createElement("span");
            name.textContent = meta.name;
            row.append(name);

            const markerText = cell.querySelector(".authority-cell-marker")?.textContent.trim() || "+";
            if (cell.classList.contains("is-conditional")) {
                const detailId = `authority-mobile-condition-${rowIndex}-${cellIndex}`;
                const button = document.createElement("button");
                button.type = "button";
                button.className = "authority-mobile-marker is-conditional";
                button.textContent = markerText;
                button.dataset.mobileConditionTrigger = detailId;
                button.setAttribute("aria-expanded", "false");
                button.setAttribute("aria-controls", detailId);
                button.setAttribute("aria-label", `${meta.name}: показать условие ${markerText}`);
                row.append(button);

                const detail = document.createElement("div");
                detail.className = "authority-mobile-condition-detail";
                detail.id = detailId;
                detail.hidden = true;
                const sourcePopover = cell.querySelector(".authority-condition-popover");
                if (sourcePopover) {
                    [...sourcePopover.children].forEach((child) => detail.append(child.cloneNode(true)));
                }
                if (sourceLink?.href) {
                    const open = document.createElement("a");
                    open.href = sourceLink.href;
                    open.textContent = "Открыть право в карточке сотрудника";
                    detail.append(open);
                }
                row.append(detail);
            } else {
                const marker = document.createElement("span");
                marker.className = "authority-mobile-marker is-granted";
                marker.textContent = markerText;
                marker.setAttribute("aria-label", `${meta.name}: право предоставлено`);
                row.append(marker);
            }
            groups.get(meta.category).append(row);
        });

        const note = document.createElement("p");
        note.className = "authority-mobile-matrix-note";
        note.textContent = "Непредоставленные права скрыты в мобильном обзоре; здесь показаны только действующие права сотрудника.";
        rights.append(note);
        card.append(rights);
        card.hidden = sourceRow.hidden;

        const observer = new MutationObserver(() => {
            card.hidden = sourceRow.hidden;
        });
        observer.observe(sourceRow, { attributes: true, attributeFilter: ["hidden"] });
        mobileRows.push({ card, sourceRow, observer });
        return card;
    };

    const buildMobileMatrix = () => {
        if (mobileMatrixBuilt || !mobileMedia.matches) return;
        const panel = authorityRoot.querySelector('[data-authority-panel="matrix"]');
        const table = panel?.querySelector(".authority-matrix");
        const scroll = panel?.querySelector(".authority-matrix-scroll");
        if (!panel || !table || !scroll || panel.querySelector(".authority-mobile-matrix")) return;

        const metadata = rightMetadata();
        const container = document.createElement("div");
        container.className = "authority-mobile-matrix";
        container.setAttribute("aria-label", "Права сотрудников");
        [...table.querySelectorAll(".authority-matrix-person[data-matrix-row]")].forEach((row, index) => {
            container.append(buildMobileEmployee(row, metadata, index));
        });
        scroll.insertAdjacentElement("afterend", container);
        mobileMatrixBuilt = true;
    };

    const closeMobileCondition = () => {
        if (!activeMobileCondition) return;
        const target = document.getElementById(activeMobileCondition.dataset.mobileConditionTrigger);
        if (target) target.hidden = true;
        activeMobileCondition.setAttribute("aria-expanded", "false");
        activeMobileCondition = null;
    };

    const destroyMobileMatrix = () => {
        closeMobileCondition();
        mobileRows.forEach(({ observer }) => observer.disconnect());
        mobileRows.length = 0;
        authorityRoot.querySelector(".authority-mobile-matrix")?.remove();
        mobileMatrixBuilt = false;
    };

    authorityRoot.addEventListener("click", (event) => {
        const trigger = event.target.closest("[data-mobile-condition-trigger]");
        if (!trigger) return;
        event.preventDefault();
        const target = document.getElementById(trigger.dataset.mobileConditionTrigger);
        if (!target) return;
        const opening = target.hidden;
        if (activeMobileCondition && activeMobileCondition !== trigger) closeMobileCondition();
        target.hidden = !opening;
        trigger.setAttribute("aria-expanded", String(opening));
        activeMobileCondition = opening ? trigger : null;
    });

    authorityRoot.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || !activeMobileCondition) return;
        const trigger = activeMobileCondition;
        closeMobileCondition();
        trigger.focus({ preventScroll: true });
    });

    const ensureAuthorityPresentation = () => {
        if (!preambleBuilt) enhancePreamble();
        syncDisclosureMode();
        if (mobileMedia.matches) buildMobileMatrix();
        else if (mobileMatrixBuilt) destroyMobileMatrix();
        mobileRows.forEach(({ card, sourceRow }) => {
            card.hidden = sourceRow.hidden;
        });
    };

    ensureAuthorityPresentation();
    compactMedia.addEventListener("change", ensureAuthorityPresentation);
    mobileMedia.addEventListener("change", ensureAuthorityPresentation);
})();
