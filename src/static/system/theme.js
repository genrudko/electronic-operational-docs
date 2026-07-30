(() => {
    "use strict";

    const root = document.documentElement;
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
    const allowed = new Set(["light", "dark", "system"]);

    function normalize(value) {
        const normalized = String(value || "system").toLowerCase();
        return allowed.has(normalized) ? normalized : "system";
    }

    function resolve(preference) {
        return preference === "system"
            ? (systemTheme.matches ? "dark" : "light")
            : preference;
    }

    function apply(value, source = "api") {
        const preference = normalize(value);
        const theme = resolve(preference);
        root.dataset.themePreference = preference;
        root.dataset.theme = theme;
        root.style.colorScheme = theme;
        window.dispatchEvent(new CustomEvent("eod:themechange", {
            detail: {preference, theme, source},
        }));
        return {preference, theme};
    }

    window.EODTheme = Object.freeze({apply, normalize, resolve});
    systemTheme.addEventListener?.("change", () => {
        if (root.dataset.themePreference === "system") {
            apply("system", "system");
        }
    });

    apply(root.dataset.themePreference, "controller");

    document.querySelectorAll("[data-interface-settings] select[name='theme']")
        .forEach((select) => {
            select.addEventListener("change", () => apply(select.value, "account"));
        });
})();
