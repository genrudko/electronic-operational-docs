(() => {
    "use strict";

    const selector = "details.help-tip";
    const tips = Array.from(document.querySelectorAll(selector));
    let activeTip = null;

    function summaryFor(tip) {
        return tip.querySelector(":scope > summary");
    }

    function panelFor(tip) {
        return tip.querySelector(":scope > div");
    }

    function setExpanded(tip, expanded) {
        const summary = summaryFor(tip);
        if (summary) {
            summary.setAttribute("aria-expanded", expanded ? "true" : "false");
        }
    }

    function closeTip(tip, restoreFocus = false) {
        if (!tip) {
            return;
        }
        const summary = summaryFor(tip);
        tip.open = false;
        setExpanded(tip, false);
        if (activeTip === tip) {
            activeTip = null;
        }
        if (restoreFocus && summary) {
            summary.focus();
        }
    }

    function closeOtherTips(current) {
        for (const tip of tips) {
            if (tip !== current && tip.open) {
                closeTip(tip);
            }
        }
    }

    function positionTip(tip) {
        if (!tip || !tip.open) {
            return;
        }
        const summary = summaryFor(tip);
        const panel = panelFor(tip);
        if (!summary || !panel) {
            return;
        }

        panel.style.removeProperty("left");
        panel.style.removeProperty("right");
        panel.style.removeProperty("top");
        panel.style.removeProperty("bottom");
        panel.style.removeProperty("width");
        tip.dataset.placement = "";

        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        if (viewportWidth <= 760) {
            tip.dataset.placement = "bottom-sheet";
            return;
        }

        const margin = 16;
        const gap = 12;
        const preferredWidth = Math.min(360, viewportWidth - margin * 2);
        panel.style.width = `${preferredWidth}px`;

        const anchor = summary.getBoundingClientRect();
        const panelRect = panel.getBoundingClientRect();
        let left = anchor.right + gap;
        let placement = "right";

        if (left + panelRect.width > viewportWidth - margin) {
            left = anchor.left - panelRect.width - gap;
            placement = "left";
        }
        if (left < margin) {
            left = Math.min(
                Math.max(anchor.left, margin),
                viewportWidth - panelRect.width - margin,
            );
            placement = "below";
        }

        let top = anchor.top - 10;
        if (top + panelRect.height > viewportHeight - margin) {
            top = viewportHeight - panelRect.height - margin;
        }
        if (top < margin) {
            top = margin;
        }

        panel.style.left = `${Math.round(left)}px`;
        panel.style.top = `${Math.round(top)}px`;
        tip.dataset.placement = placement;
    }

    tips.forEach((tip, index) => {
        const summary = summaryFor(tip);
        const panel = panelFor(tip);
        if (!summary || !panel) {
            return;
        }

        const panelId = panel.id || `context-help-${index + 1}`;
        panel.id = panelId;
        panel.setAttribute("role", "tooltip");
        summary.setAttribute("aria-controls", panelId);
        summary.setAttribute("aria-haspopup", "true");
        setExpanded(tip, tip.open);

        tip.addEventListener("toggle", () => {
            if (tip.open) {
                closeOtherTips(tip);
                activeTip = tip;
                setExpanded(tip, true);
                window.requestAnimationFrame(() => positionTip(tip));
            } else {
                setExpanded(tip, false);
                if (activeTip === tip) {
                    activeTip = null;
                }
            }
        });
    });

    document.addEventListener("pointerdown", (event) => {
        if (activeTip && !activeTip.contains(event.target)) {
            closeTip(activeTip);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && activeTip) {
            event.preventDefault();
            closeTip(activeTip, true);
        }
    });

    window.addEventListener("resize", () => positionTip(activeTip));
    window.addEventListener(
        "scroll",
        () => positionTip(activeTip),
        { passive: true },
    );
})();
