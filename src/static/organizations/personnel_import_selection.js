(() => {
    const root = document.querySelector("[data-personnel-import-preview]");
    if (!root) return;

    const rowCheckboxes = [...root.querySelectorAll("[data-import-row]")];
    const groupCheckboxes = [...root.querySelectorAll("[data-import-group]")];
    const selectAll = root.querySelector("[data-import-select-all]");

    const normalize = (value) => (value || "")
        .toLocaleLowerCase("ru-RU")
        .replaceAll("ё", "е")
        .replace(/\s+/g, " ")
        .trim();

    const rowGroup = (checkbox) => normalize(checkbox.dataset.importRow);

    const syncGroup = (groupCheckbox) => {
        const group = normalize(groupCheckbox.dataset.importGroup);
        const rows = rowCheckboxes.filter((item) => rowGroup(item) === group);
        const selected = rows.filter((item) => item.checked).length;
        groupCheckbox.checked = rows.length > 0 && selected === rows.length;
        groupCheckbox.indeterminate = selected > 0 && selected < rows.length;
    };

    const syncAll = () => {
        const selected = rowCheckboxes.filter((item) => item.checked).length;
        if (selectAll) {
            selectAll.checked = rowCheckboxes.length > 0 && selected === rowCheckboxes.length;
            selectAll.indeterminate = selected > 0 && selected < rowCheckboxes.length;
        }
        groupCheckboxes.forEach(syncGroup);
    };

    groupCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            const group = normalize(checkbox.dataset.importGroup);
            rowCheckboxes
                .filter((item) => rowGroup(item) === group)
                .forEach((item) => {
                    item.checked = checkbox.checked;
                });
            syncAll();
        });
    });

    rowCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", syncAll);
    });

    selectAll?.addEventListener("change", () => {
        rowCheckboxes.forEach((checkbox) => {
            checkbox.checked = selectAll.checked;
        });
        syncAll();
    });

    root.querySelectorAll("[data-import-recommended]").forEach((button) => {
        button.addEventListener("click", () => {
            const recommendedMarkers = [
                "диспетчер",
                "оператив",
                "руковод",
                "цус",
                "центр управления сетями",
                "невинномысск",
                "коммерческ",
            ];
            rowCheckboxes.forEach((checkbox) => {
                const haystack = normalize(checkbox.dataset.importSearch);
                checkbox.checked = recommendedMarkers.some((marker) => haystack.includes(marker));
            });
            syncAll();
        });
    });

    syncAll();
})();
