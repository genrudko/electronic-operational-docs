(() => {
    const stylesheetId = "personnel-authority-followup-css";
    if (!document.getElementById(stylesheetId)) {
        const stylesheet = document.createElement("link");
        stylesheet.id = stylesheetId;
        stylesheet.rel = "stylesheet";
        stylesheet.href = "/static/organizations/personnel_authority_followup.css?v=pa001r6";
        document.head.append(stylesheet);
    }

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
})();
