const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");
const headerEntangledToggle = document.querySelector(".entangled-symbol");
const payloadElement = document.getElementById("qa-graph-data");
const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

let payload = { branches: [], nodes: [], domain_overrides: {} };
if (payloadElement?.textContent) {
    try {
        payload = JSON.parse(payloadElement.textContent);
    } catch (_error) {
        payload = { branches: [], nodes: [], domain_overrides: {} };
    }
}

let BASE_NODES = [];
let DOMAIN_OVERRIDES = {};
const workspaceRegistry = {};

function applyPayload(nextPayload) {
    payload = nextPayload || { branches: [], nodes: [], domain_overrides: {} };
    BASE_NODES = payload.nodes || [];
    DOMAIN_OVERRIDES = payload.domain_overrides || {};
}

function activateTab(targetId) {
    if (!targetId || !Array.from(tabPanels).some((panel) => panel.id === targetId)) {
        return;
    }

    tabButtons.forEach((button) => {
        if (!button.dataset.tab) return;
        button.classList.toggle("active", button.dataset.tab === targetId);
    });

    tabPanels.forEach((panel) => {
        panel.classList.toggle("active", panel.id === targetId);
    });

    if (window.location.hash !== `#${targetId}`) {
        const url = `${window.location.pathname}${window.location.search}#${targetId}`;
        window.history.replaceState(null, "", url);
    }
}

function readDomainQueryState(domain) {
    const params = new URLSearchParams(window.location.search);
    return {
        letter: params.get(`${domain}Letter`) || null,
        search: params.get(`${domain}Search`) || "",
        nodeId: params.get(`${domain}Node`) || null,
    };
}

function writeDomainQueryState(domain, state) {
    const params = new URLSearchParams(window.location.search);
    const mappings = [
        { key: `${domain}Letter`, value: state.letter || "" },
        { key: `${domain}Search`, value: state.search || "" },
        { key: `${domain}Node`, value: state.nodeId || "" },
    ];

    mappings.forEach(({ key, value }) => {
        if (value) {
            params.set(key, value);
        } else {
            params.delete(key);
        }
    });

    const query = params.toString();
    const hash = window.location.hash || "";
    const url = `${window.location.pathname}${query ? `?${query}` : ""}${hash}`;
    window.history.replaceState(null, "", url);
}

function isTextInputTarget(target) {
    if (!target) return false;
    if (target.isContentEditable) return true;
    const tag = (target.tagName || "").toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select";
}

function triggerPanelAnimation(element) {
    if (!element) return;
    element.classList.remove("qa-panel-anim");
    // Force reflow to restart animation class reliably.
    void element.offsetWidth;
    element.classList.add("qa-panel-anim");
}

function buildDomainNodes(domain) {
    const overrides = DOMAIN_OVERRIDES[domain] || {};
    return BASE_NODES
        .map((node) => {
            const update = overrides[node.node_id] || {};
            const merged = {
                ...node,
                ...update,
                links: update.links || node.links || [],
                resources: update.resources || node.resources || [],
                tech_stack: update.tech_stack || node.tech_stack || [],
                domain: node.domain || "shared",
            };
            return merged;
        })
        .filter((node) => node.domain === domain || node.domain === "shared");
}

function dedupeByNodeId(nodes) {
    const seen = new Set();
    return nodes.filter((node) => {
        if (!node || seen.has(node.node_id)) return false;
        seen.add(node.node_id);
        return true;
    });
}

function nodeCategory(node) {
    const candidate = (node.category || node.branch || node.title || "").trim();
    const letter = candidate.charAt(0).toUpperCase();
    return /^[A-Z]$/.test(letter) ? letter : "O";
}

function sortNodes(nodes) {
    return [...nodes].sort((a, b) => {
        const byTitle = (a.title || "").localeCompare(b.title || "");
        if (byTitle !== 0) return byTitle;
        return (a.node_id || "").localeCompare(b.node_id || "");
    });
}

function badgeForDomain(domain) {
    if (domain === "quantum") return "Quantum";
    if (domain === "ai") return "AI";
    return "Shared";
}

function mapResourcesByType(resources) {
    const mapped = {};
    (resources || []).forEach((resource) => {
        const key = resource.type || "resource";
        if (!mapped[key]) mapped[key] = [];
        mapped[key].push(resource);
    });
    return mapped;
}

function titleFromResourceType(type) {
    const labels = {
        paper: "Research Papers",
        repo: "GitHub Repositories",
        doc: "Documentation",
        course: "Courses",
        resource: "Resources",
        video: "Videos",
        blog: "Blogs",
        dataset: "Datasets",
        benchmark: "Benchmarks",
        cookbook: "Cookbooks",
    };
    return labels[type] || type.replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderResourceGroups(node) {
    const resourcesByType = mapResourcesByType(node.resources || []);
    const order = ["doc", "paper", "repo", "course", "video", "blog", "dataset", "benchmark", "cookbook", "resource"];
    const keys = Object.keys(resourcesByType);
    const ordered = [
        ...order.filter((item) => keys.includes(item)),
        ...keys.filter((item) => !order.includes(item)).sort(),
    ];

    return ordered
        .map((type) => {
            const rows = resourcesByType[type] || [];
            const items = rows
                .slice(0, 6)
                .map((entry) => {
                    const name = entry.url
                        ? `<a href="${entry.url}" target="_blank" rel="noreferrer">${entry.title}</a>`
                        : entry.title;
                    return `<li>${name}</li>`;
                })
                .join("");

            return `
                <section class="qa-mini-section">
                    <h4>${titleFromResourceType(type)}</h4>
                    <ul>${items}</ul>
                </section>
            `;
        })
        .join("");
}

function initWorkspace(shell) {
    const domain = shell.dataset.domain;
    const graphEndpoint = shell.dataset.graphEndpoint;
    const azNavEl = shell.querySelector(".qa-az-nav");
    const listEl = shell.querySelector(".qa-topic-list");
    const centerEl = shell.querySelector(".qa-center");
    const entangledEl = shell.querySelector(".qa-entangled-list");
    const searchEl = shell.querySelector(".qa-search-input");

    if (!azNavEl || !listEl || !centerEl || !entangledEl || !domain) return;

    let nodes = [];
    let nodeMap = new Map();
    let selectedLetter = null;
    let activeNodeId = null;
    let searchTerm = "";

    function hydrateNodes() {
        nodes = sortNodes(buildDomainNodes(domain));
        nodeMap = new Map(nodes.map((node) => [node.node_id, node]));
    }

    function filteredNodes() {
        return nodes.filter((node) => {
            const byLetter = selectedLetter ? nodeCategory(node) === selectedLetter : true;
            if (!byLetter) return false;

            if (!searchTerm) return true;
            const haystack = [
                node.title || "",
                node.content || "",
                node.branch || "",
                node.type || "",
            ]
                .join(" ")
                .toLowerCase();
            return haystack.includes(searchTerm.toLowerCase());
        });
    }

    function normalizeSelectedLetter(value) {
        if (!value) return null;
        const letter = String(value).trim().toUpperCase();
        return alphabet.includes(letter) ? letter : null;
    }

    function countsByLetter() {
        const counts = {};
        nodes.forEach((node) => {
            const key = nodeCategory(node);
            counts[key] = (counts[key] || 0) + 1;
        });
        return counts;
    }

    function findEntangledNodes(node) {
        if (!node) return [];
        const direct = (node.links || []).map((id) => BASE_NODES.find((entry) => entry.node_id === id)).filter(Boolean);
        const reverse = BASE_NODES.filter((entry) => (entry.links || []).includes(node.node_id));
        return dedupeByNodeId([...direct, ...reverse]).filter((entry) => entry.node_id !== node.node_id);
    }

    function ensureActiveNode() {
        let candidates = filteredNodes();
        if (!candidates.length && (selectedLetter || searchTerm)) {
            selectedLetter = null;
            searchTerm = "";
            candidates = filteredNodes();
        }

        if (!candidates.length) {
            activeNodeId = null;
            return;
        }

        const stillVisible = candidates.some((node) => node.node_id === activeNodeId);
        if (!stillVisible) {
            activeNodeId = candidates[0].node_id;
        }
    }

    function navigateToNode(targetNode) {
        if (!targetNode) return;
        const targetDomain = targetNode.domain === "shared" ? domain : targetNode.domain;
        const targetWorkspace = workspaceRegistry[targetDomain];

        if (targetWorkspace && targetDomain !== domain) {
            activateTab(targetDomain);
            targetWorkspace.focusNode(targetNode.node_id);
            return;
        }

        selectedLetter = nodeCategory(targetNode);
        activeNodeId = targetNode.node_id;
        renderAll();
    }

    function renderAlphabet() {
        const counts = countsByLetter();
        const letters = alphabet
            .map((letter) => {
                const count = counts[letter] || 0;
                const active = selectedLetter === letter;
                return `
                    <button class="qa-az-btn${active ? " active" : ""}" data-letter="${letter}">
                        <span>${letter}</span>
                        <small>${count}</small>
                    </button>
                `;
            })
            .join("");

        azNavEl.innerHTML = `
            <div class="qa-az-track">${letters}</div>
            <button class="qa-az-reset${selectedLetter ? " active" : ""}" data-reset="all">ALL</button>
        `;

        azNavEl.querySelectorAll(".qa-az-btn").forEach((button) => {
            button.addEventListener("click", () => {
                selectedLetter = button.dataset.letter || null;
                renderAll();
            });
        });

        const resetBtn = azNavEl.querySelector(".qa-az-reset");
        if (resetBtn) {
            resetBtn.addEventListener("click", () => {
                selectedLetter = null;
                renderAll();
            });
        }
    }

    function renderSearch() {
        if (!searchEl) return;
        if (searchEl.value !== searchTerm) {
            searchEl.value = searchTerm;
        }
    }

    function renderTopicList() {
        const rows = filteredNodes();
        if (!rows.length) {
            listEl.innerHTML = "<p class='qa-empty'>No topics found for this filter.</p>";
            return;
        }

        listEl.innerHTML = rows
            .map((node) => {
                const category = nodeCategory(node);
                return `
                    <button class="qa-topic-item${node.node_id === activeNodeId ? " active" : ""}" data-node-id="${node.node_id}">
                        <span class="qa-topic-letter">${category}</span>
                        <strong>${node.title}</strong>
                    </button>
                `;
            })
            .join("");

        listEl.querySelectorAll(".qa-topic-item").forEach((button) => {
            button.addEventListener("click", () => {
                activeNodeId = button.dataset.nodeId;
                renderAll();
            });
        });
    }

    function renderCenter() {
        const node = nodeMap.get(activeNodeId);
        if (!node) {
            centerEl.innerHTML = "<p class='qa-empty'>Select a topic to view content.</p>";
            triggerPanelAnimation(centerEl);
            return;
        }

        const links = findEntangledNodes(node);
        const chips = links
            .map((entry) => `<button class="qa-chip" data-node-id="${entry.node_id}">${entry.title}</button>`)
            .join("");

        const source = node.url
            ? `<a class="qa-source-link" href="${node.url}" target="_blank" rel="noreferrer">Open source</a>`
            : "";

        const resources = renderResourceGroups(node);

        centerEl.innerHTML = `
            <header class="qa-center-head">
                <h1>${node.title}</h1>
                <div class="qa-center-meta">
                    <span>${badgeForDomain(node.domain)}</span>
                    <span>${node.branch || "General"}</span>
                    <span>${nodeCategory(node)}</span>
                </div>
            </header>
            <p class="qa-center-content">${node.content || "No details yet."}</p>
            ${source}
            <section class="qa-chip-wrap">
                <h4>Entangled links</h4>
                <div class="qa-chip-row">${chips || "<span class='qa-empty-inline'>No direct links.</span>"}</div>
            </section>
            <section class="qa-mini-grid">${resources}</section>
        `;

        centerEl.querySelectorAll(".qa-chip").forEach((chip) => {
            chip.addEventListener("click", () => {
                const target = BASE_NODES.find((entry) => entry.node_id === chip.dataset.nodeId);
                navigateToNode(target);
            });
        });

        triggerPanelAnimation(centerEl);
    }

    function renderEntangledPanel() {
        const node = nodeMap.get(activeNodeId);
        const rows = findEntangledNodes(node);
        if (!rows.length) {
            entangledEl.innerHTML = "<p class='qa-empty'>No connections</p>";
            return;
        }

        entangledEl.innerHTML = rows
            .map((entry) => {
                const isCross = entry.domain !== domain && entry.domain !== "shared";
                return `
                    <button class="qa-entangled-item" data-node-id="${entry.node_id}">
                        <span>${entry.branch || "General"}</span>
                        <strong>${entry.title}</strong>
                        <small>${isCross ? "Cross Domain" : "Local"}</small>
                    </button>
                `;
            })
            .join("");

        entangledEl.querySelectorAll(".qa-entangled-item").forEach((button) => {
            button.addEventListener("click", () => {
                const target = BASE_NODES.find((entry) => entry.node_id === button.dataset.nodeId);
                navigateToNode(target);
            });
        });
    }

    function renderAll() {
        hydrateNodes();
        if (!nodes.length) {
            // Keep server-rendered fallback content when payload is unavailable.
            return;
        }
        ensureActiveNode();
        renderSearch();
        renderAlphabet();
        renderTopicList();
        renderCenter();
        renderEntangledPanel();
        writeDomainQueryState(domain, {
            letter: selectedLetter,
            search: searchTerm,
            nodeId: activeNodeId,
        });
    }

    async function refreshFromApi() {
        if (!graphEndpoint) return;
        try {
            const endpoint = `${graphEndpoint}?t=${Date.now()}`;
            const response = await fetch(endpoint, { cache: "default" });
            if (!response.ok) return;
            const latestPayload = await response.json();
            applyPayload(latestPayload);
            Object.values(workspaceRegistry).forEach((workspace) => workspace.rerender());
        } catch (_error) {
            // Keep existing UI state on request errors.
        }
    }

    function focusNode(nodeId) {
        const target = BASE_NODES.find((entry) => entry.node_id === nodeId);
        if (!target) return;
        selectedLetter = nodeCategory(target);
        activeNodeId = target.node_id;
        renderAll();
    }

    function focusSearch() {
        if (!searchEl) return;
        searchEl.focus();
        searchEl.select();
    }

    function moveSelection(direction) {
        const rows = filteredNodes();
        if (!rows.length) return;

        const currentIndex = rows.findIndex((node) => node.node_id === activeNodeId);
        const fallback = direction > 0 ? 0 : rows.length - 1;
        const fromIndex = currentIndex === -1 ? fallback : currentIndex;
        const nextIndex = Math.min(Math.max(fromIndex + direction, 0), rows.length - 1);

        activeNodeId = rows[nextIndex].node_id;
        renderAll();
    }

    function openFirstEntangled() {
        const current = nodeMap.get(activeNodeId);
        if (!current) return;
        const linked = findEntangledNodes(current);
        if (!linked.length) return;
        navigateToNode(linked[0]);
    }

    workspaceRegistry[domain] = {
        focusNode,
        rerender: renderAll,
        focusSearch,
        moveSelection,
        openFirstEntangled,
    };

    const initialState = readDomainQueryState(domain);
    selectedLetter = normalizeSelectedLetter(initialState.letter);
    searchTerm = initialState.search;
    activeNodeId = initialState.nodeId;

    if (searchEl) {
        searchEl.addEventListener("input", () => {
            searchTerm = searchEl.value.trim();
            renderAll();
        });
    }

    renderAll();
}

tabButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
        if ((button.tagName || "").toLowerCase() === "a") {
            event.preventDefault();
        }
        const targetId = button.dataset.tab;
        if (!targetId) return;
        activateTab(targetId);
    });
});

if (headerEntangledToggle) {
    headerEntangledToggle.addEventListener("click", () => {
        const activePanel = Array.from(tabPanels).find((panel) => panel.classList.contains("active"));
        if (!activePanel || activePanel.id === "about") {
            activateTab("quantum");
            return;
        }

        if (activePanel.id === "quantum") {
            activateTab("ai");
            return;
        }

        activateTab("quantum");
    });
}

applyPayload(payload);

const initialTabFromHash = window.location.hash.replace("#", "").trim();
if (initialTabFromHash && Array.from(tabButtons).some((button) => button.dataset.tab === initialTabFromHash)) {
    activateTab(initialTabFromHash);
}

window.addEventListener("hashchange", () => {
    const tabFromHash = window.location.hash.replace("#", "").trim();
    if (!tabFromHash) return;
    if (Array.from(tabButtons).some((button) => button.dataset.tab === tabFromHash)) {
        activateTab(tabFromHash);
    }
});

document.querySelectorAll(".qa-shell").forEach((shell) => {
    initWorkspace(shell);
});

function getActiveWorkspace() {
    const activePanel = Array.from(tabPanels).find((panel) => panel.classList.contains("active"));
    if (!activePanel) return null;
    const domain = activePanel.id;
    if (domain !== "quantum" && domain !== "ai") return null;
    return workspaceRegistry[domain] || null;
}

document.addEventListener("keydown", (event) => {
    const workspace = getActiveWorkspace();
    if (!workspace) return;

    if (event.key === "/") {
        if (isTextInputTarget(event.target)) return;
        event.preventDefault();
        workspace.focusSearch();
        return;
    }

    if (event.key === "ArrowDown") {
        if (isTextInputTarget(event.target)) return;
        event.preventDefault();
        workspace.moveSelection(1);
        return;
    }

    if (event.key === "ArrowUp") {
        if (isTextInputTarget(event.target)) return;
        event.preventDefault();
        workspace.moveSelection(-1);
        return;
    }

    if (event.key === "Enter") {
        if (isTextInputTarget(event.target)) return;
        event.preventDefault();
        workspace.openFirstEntangled();
    }
});
