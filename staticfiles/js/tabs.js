const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");
const searches = document.querySelectorAll(".resource-search");
const toggles = document.querySelectorAll(".entangled-toggle");
const entangleButtons = document.querySelectorAll(".entangle-trigger");

function activateTab(targetId) {
    tabButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === targetId);
    });

    tabPanels.forEach((panel) => {
        panel.classList.toggle("active", panel.id === targetId);
    });
}

tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
        activateTab(button.dataset.tab);
    });
});

function updateFilters(domain) {
    const panel = document.getElementById(domain);
    if (!panel) return;

    const query = (
        panel.querySelector(`.resource-search[data-domain=\"${domain}\"]`)?.value || ""
    )
        .trim()
        .toLowerCase();
    const onlyEntangled = panel.querySelector(`.entangled-toggle[data-domain=\"${domain}\"]`)?.checked;

    panel.querySelectorAll(".resource-item").forEach((item) => {
        const text = `${item.dataset.title || ""} ${item.dataset.description || ""}`;
        const matchQuery = !query || text.includes(query);
        const matchEntangled = !onlyEntangled || item.dataset.entangled === "true";
        item.style.display = matchQuery && matchEntangled ? "block" : "none";
    });
}

searches.forEach((search) => {
    search.addEventListener("input", () => {
        updateFilters(search.dataset.domain);
    });
});

toggles.forEach((toggle) => {
    toggle.addEventListener("change", () => {
        updateFilters(toggle.dataset.domain);
    });
});

entangleButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const panel = document.getElementById(button.dataset.target);
        if (!panel) return;
        panel.hidden = !panel.hidden;
    });
});
