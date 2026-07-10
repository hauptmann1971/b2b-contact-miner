(function () {
    const STORAGE_KEY = "bcm_theme";

    function getStoredTheme() {
        return localStorage.getItem(STORAGE_KEY);
    }

    function getDefaultTheme() {
        const el = document.documentElement;
        return el.getAttribute("data-default-theme") || "light";
    }

    function applyTheme(theme) {
        const resolved = theme === "dark" ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", resolved);
        document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
            btn.classList.toggle("is-active", btn.getAttribute("data-theme-choice") === resolved);
        });
    }

    function setTheme(theme, persist) {
        applyTheme(theme);
        if (persist !== false) {
            localStorage.setItem(STORAGE_KEY, theme);
        }
    }

    window.BCMTheme = {
        get: () => document.documentElement.getAttribute("data-theme") || "light",
        set: (theme) => setTheme(theme, true),
        toggle: () => setTheme(window.BCMTheme.get() === "dark" ? "light" : "dark", true),
    };

    document.addEventListener("DOMContentLoaded", () => {
        const initial = getStoredTheme() || getDefaultTheme();
        applyTheme(initial);

        document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
            btn.addEventListener("click", () => {
                setTheme(btn.getAttribute("data-theme-choice"), true);
            });
        });

        const toggleBtn = document.getElementById("themeToggleBtn");
        if (toggleBtn) {
            toggleBtn.addEventListener("click", () => window.BCMTheme.toggle());
        }
    });
})();
