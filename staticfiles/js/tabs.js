const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");
const payloadElement = document.getElementById("qa-graph-data");

let payload = { branches: [], nodes: [], domain_overrides: {} };
if (payloadElement?.textContent) {
    try {
        payload = JSON.parse(payloadElement.textContent);
    } catch (_error) {
        payload = { branches: [], nodes: [], domain_overrides: {} };
    }
}

let BRANCHES = [];
let BASE_NODES = [];
let DOMAIN_OVERRIDES = {};

const FALLBACK_BRANCHES = [
    "Documentation",
    "Tech Stack Requirements",
    "Research Papers",
    "GitHub Repositories",
    "Other Resources",
];

const BRANCH_ICONS = {
    Documentation: "DOC",
    "Tech Stack Requirements": "STACK",
    "Research Papers": "PAPER",
    "GitHub Repositories": "GIT",
    "Other Resources": "RES",
};

const workspaceRegistry = {};

function applyPayload(nextPayload) {
    payload = nextPayload || { branches: [], nodes: [], domain_overrides: {} };
    BRANCHES = payload.branches?.length ? payload.branches : FALLBACK_BRANCHES;
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
        window.history.replaceState(null, "", `#${targetId}`);
    }
}

tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const targetId = button.dataset.tab;
        if (!targetId) return;
        activateTab(targetId);
    });
});

function buildDomainNodes(domain) {
    const overrides = DOMAIN_OVERRIDES[domain] || {};
    return BASE_NODES.map((node) => {
        const update = overrides[node.node_id] || {};
        return {
            ...node,
            ...update,
            links: update.links || node.links || [],
            resources: update.resources || node.resources || [],
            tech_stack: update.tech_stack || node.tech_stack || [],
            cookbooks: update.cookbooks || node.cookbooks || [],
            domain: node.domain || "shared",
        };
    });
}

function dedupeByNodeId(nodes) {
    const seen = new Set();
    return nodes.filter((node) => {
        if (!node || seen.has(node.node_id)) return false;
        seen.add(node.node_id);
        return true;
    });
}

function mapResourcesByType(resources) {
    const mapped = {};
    resources.forEach((resource) => {
        const key = resource.type || "resource";
        if (!mapped[key]) {
            mapped[key] = [];
        }
        mapped[key].push(resource);
    });
    return mapped;
}

function renderResourceSection(title, rows) {
    if (!rows || !rows.length) return "";

    const cards = rows
        .map((entry) => {
            const source = entry.source || "source";
            const summary = entry.summary || "";
            const linkTitle = entry.url
                ? `<a href="${entry.url}" target="_blank" rel="noreferrer">${entry.title}</a>`
                : entry.title;

            return `
                <article class="qa-resource-card">
                    <h6>${linkTitle}</h6>
                    <p>${summary}</p>
                    <span>${source}</span>
                </article>
            `;
        })
        .join("");

    return `
        <section class="qa-resource-wrap">
            <h5>${title}</h5>
            <div class="qa-resource-grid">${cards}</div>
        </section>
    `;
}

function renderTechStackSection(rows) {
    if (!rows || !rows.length) return "";

    const cards = rows
        .map((entry) => {
            const docs = entry.docs_url
                ? `<a href="${entry.docs_url}" target="_blank" rel="noreferrer">Docs</a>`
                : "-";
            const homepage = entry.homepage_url
                ? `<a href="${entry.homepage_url}" target="_blank" rel="noreferrer">Home</a>`
                : "-";
            const role = entry.is_primary ? "Primary" : "Support";

            return `
                <article class="qa-stack-card${entry.is_primary ? " primary" : ""}">
                    <p>${entry.category}</p>
                    <h6>${entry.name}</h6>
                    <div class="qa-stack-meta">
                        <span>${role}</span>
                        <span>${docs}</span>
                        <span>${homepage}</span>
                    </div>
                </article>
            `;
        })
        .join("");

    return `
        <section class="qa-resource-wrap">
            <h5>Tech Stack</h5>
            <div class="qa-stack-grid">${cards}</div>
        </section>
    `;
}

function initWorkspace(shell) {
    const domain = shell.dataset.domain;
    const graphEndpoint = shell.dataset.graphEndpoint;
    const branchesEl = shell.querySelector(".qa-branches");
    const branchTitleEl = shell.querySelector(".qa-branch-title");
    const heroEl = shell.querySelector(".qa-live-hero");
    const listEl = shell.querySelector(".qa-node-list");
    const detailEl = shell.querySelector(".qa-node-detail");
    const relatedEl = shell.querySelector(".qa-related");
    const statsEl = shell.querySelector(".qa-stats");
    const graphEl = shell.querySelector(".qa-graph");

    if (!branchesEl || !branchTitleEl || !listEl || !detailEl || !relatedEl || !graphEl) return;

    let nodes = [];
    let nodeMap = new Map();
    let activeBranch = BRANCHES[0];
    let activeNodeId = null;

    function reloadGraphData() {
        nodes = buildDomainNodes(domain);
        nodeMap = new Map(nodes.map((node) => [node.node_id, node]));
    }

    function getBranchNodes(branch) {
        return nodes.filter((node) => {
            const branchMatch = node.branch === branch;
            const domainMatch = node.domain === domain || node.domain === "shared";
            return branchMatch && domainMatch;
        });
    }

    function findEntangledNodes(node) {
        if (!node) return [];
        const linked = (node.links || []).map((id) => nodeMap.get(id)).filter(Boolean);
        const reverseLinked = nodes.filter((candidate) => (candidate.links || []).includes(node.node_id));
        const sameBranchCrossDomain = nodes.filter(
            (candidate) =>
                candidate.branch === node.branch &&
                candidate.node_id !== node.node_id &&
                candidate.domain !== node.domain &&
                candidate.domain !== "shared",
        );

        return dedupeByNodeId([...linked, ...reverseLinked, ...sameBranchCrossDomain]).filter(
            (candidate) => candidate.node_id !== node.node_id,
        );
    }

    function hasCrossDomainEntanglement(node) {
        if (!node) return false;
        if (node.is_live_entangled) return true;

        const hasOutgoing = (node.links || []).some((targetNodeId) => {
            const target = nodeMap.get(targetNodeId);
            return !!target && target.domain !== node.domain && target.domain !== "shared";
        });

        const hasIncoming = nodes.some(
            (candidate) =>
                (candidate.links || []).includes(node.node_id) &&
                candidate.domain !== node.domain &&
                candidate.domain !== "shared",
        );

        const hasBranchPair = nodes.some(
            (candidate) =>
                candidate.branch === node.branch &&
                candidate.node_id !== node.node_id &&
                candidate.domain !== node.domain &&
                candidate.domain !== "shared",
        );

        return hasOutgoing || hasIncoming || hasBranchPair;
    }

    function formatDomainBadge(nodeDomain) {
        if (nodeDomain === "ai") {
            return "<span class='qa-domain-badge ai'>AI</span>";
        }
        if (nodeDomain === "quantum") {
            return "<span class='qa-domain-badge quantum'>Quantum</span>";
        }
        return "<span class='qa-domain-badge shared'>Shared</span>";
    }

    function findFirstEntangledNode() {
        for (const branch of BRANCHES) {
            const candidates = getBranchNodes(branch);
            const entangledCandidate = candidates.find((candidate) => hasCrossDomainEntanglement(candidate));
            if (entangledCandidate) {
                return entangledCandidate;
            }
        }
        return null;
    }

    function renderLiveHero(node, linkedNodes) {
        if (!heroEl || !node) return;
        const crossDomainTargets = linkedNodes.filter(
            (linked) => linked.domain !== node.domain && linked.domain !== "shared",
        );

        if (!crossDomainTargets.length) {
            heroEl.innerHTML = `
                <div class="qa-live-hero-card">
                    <p>Live Entanglement</p>
                    <strong>${node.title}</strong>
                    <span>No cross-domain entanglements for this node yet.</span>
                </div>
            `;
            return;
        }

        heroEl.innerHTML = `
            <div class="qa-live-hero-card hot">
                <p>Live Entanglement Active</p>
                <strong>${node.title}</strong>
                <span>Connected to ${crossDomainTargets.map((target) => target.title).join(", ")} </span>
            </div>
        `;
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

        activeBranch = targetNode.branch;
        activeNodeId = targetNode.node_id;
        renderAll();
    }

    function renderBranches() {
        branchesEl.innerHTML = BRANCHES.map(
            (branch) => `
                <button class="qa-branch-btn${branch === activeBranch ? " active" : ""}" data-branch="${branch}">
                    <span>${BRANCH_ICONS[branch] || "NODE"}</span>
                    ${branch}
                </button>
            `,
        ).join("");

        branchesEl.querySelectorAll(".qa-branch-btn").forEach((button) => {
            button.addEventListener("click", () => {
                activeBranch = button.dataset.branch || BRANCHES[0];
                const branchNodes = getBranchNodes(activeBranch);
                activeNodeId = branchNodes[0]?.node_id || null;
                renderAll();
            });
        });
    }

    function renderNodeList() {
        const branchNodes = getBranchNodes(activeBranch);
        listEl.innerHTML = branchNodes
            .map((node) => {
                const liveSymbol = hasCrossDomainEntanglement(node)
                    ? "<span class='qa-entangled-live' title='Live entangled link' aria-label='Live entangled link'>&#8734;</span>"
                    : "";
                const badge = formatDomainBadge(node.domain);
                return `
                    <button class="qa-node-card${node.node_id === activeNodeId ? " active" : ""}" data-node-id="${node.node_id}">
                        <p>${node.type}</p>
                        <h4>${node.title} ${liveSymbol}</h4>
                        <div>${badge}</div>
                        <span>Open Node</span>
                    </button>
                `;
            })
            .join("");

        listEl.querySelectorAll(".qa-node-card").forEach((button) => {
            button.addEventListener("click", () => {
                activeNodeId = button.dataset.nodeId;
                renderAll();
            });
        });
    }

    function renderDetail() {
        const node = nodeMap.get(activeNodeId);
        if (!node) {
            detailEl.innerHTML = "<p>Select a node to explore its content.</p>";
            return;
        }

        const linkedNodes = findEntangledNodes(node);
        const linkPills = linkedNodes
            .map((linked) => {
                const entangled = linked.domain !== node.domain && linked.domain !== "shared";
                const symbol = entangled ? " <span class='qa-entangled-live'>&#8734;</span>" : "";
                return `<button class=\"qa-chip\" data-node-id=\"${linked.node_id}\">${linked.title}${symbol}</button>`;
            })
            .join("");

        const sourceLink = node.url
            ? `<p class=\"qa-source\"><a href=\"${node.url}\" target=\"_blank\" rel=\"noreferrer\">Open source</a></p>`
            : "";

        const crossDomainTargets = linkedNodes.filter(
            (linked) => linked.domain !== node.domain && linked.domain !== "shared",
        );

        const entangledWith = crossDomainTargets.length
            ? `
                <section class="qa-entangled-banner">
                    <p>Live Entangled To</p>
                    <div>
                        ${crossDomainTargets
                            .map(
                                (target) =>
                                    `<button class="qa-chip qa-chip-entangled" data-node-id="${target.node_id}">${target.title} <span class='qa-entangled-live'>&#8734;</span></button>`,
                            )
                            .join("")}
                    </div>
                </section>
            `
            : "";

        const resourcesByType = mapResourcesByType(node.resources || []);
        const resourceSections = [
            renderResourceSection("Research Papers", resourcesByType.paper),
            renderResourceSection("GitHub Repositories", resourcesByType.repo),
            renderResourceSection("Documentation", resourcesByType.doc),
            renderResourceSection("Courses", resourcesByType.course),
            renderResourceSection("Cookbooks", resourcesByType.cookbook),
            renderResourceSection("Other Resources", resourcesByType.resource),
            renderResourceSection("Videos", resourcesByType.video),
            renderResourceSection("Blogs", resourcesByType.blog),
        ].join("");

        const techSection = renderTechStackSection(node.tech_stack || []);
        renderLiveHero(node, linkedNodes);

        detailEl.innerHTML = `
            <article class="qa-detail-card">
                <p class="qa-detail-type">${node.type}</p>
                <h4>${node.title}</h4>
                <p>${node.content}</p>
                ${sourceLink}
                ${entangledWith}
                <section>
                    <p class="qa-detail-subhead">Live Entangled Links</p>
                    <div class="qa-chip-row">${linkPills || "<span class='qa-muted'>No linked nodes yet.</span>"}</div>
                </section>
                ${techSection}
                ${resourceSections}
            </article>
        `;

        detailEl.querySelectorAll(".qa-chip").forEach((chip) => {
            chip.addEventListener("click", () => {
                const targetNodeId = chip.dataset.nodeId;
                const targetNode = nodeMap.get(targetNodeId);
                navigateToNode(targetNode);
            });
        });
    }

    function renderRelated() {
        const node = nodeMap.get(activeNodeId);
        const related = findEntangledNodes(node);

        relatedEl.innerHTML = `
            <p class="qa-related-head">Triggered by: <strong>${node?.title || "-"}</strong></p>
            <div class="qa-related-list">
                ${related
                    .map((entry) => {
                        const symbol = entry.domain !== domain && entry.domain !== "shared"
                            ? "<span class='qa-entangled-live'>&#8734;</span>"
                            : "";
                        return `
                            <button class="qa-related-item" data-node-id="${entry.node_id}">
                                <span>${entry.branch}</span>
                                <strong>${entry.title} ${symbol}</strong>
                            </button>
                        `;
                    })
                    .join("") || "<p class='qa-muted'>No entangled nodes found.</p>"}
            </div>
        `;

        relatedEl.querySelectorAll(".qa-related-item").forEach((button) => {
            button.addEventListener("click", () => {
                const targetNode = nodeMap.get(button.dataset.nodeId);
                navigateToNode(targetNode);
            });
        });
    }

    function renderGraph() {
        const node = nodeMap.get(activeNodeId);
        const related = findEntangledNodes(node).slice(0, 6);

        const positions = [
            { x: 180, y: 110 },
            { x: 50, y: 45 },
            { x: 310, y: 45 },
            { x: 45, y: 175 },
            { x: 310, y: 175 },
            { x: 180, y: 30 },
            { x: 180, y: 195 },
        ];

        const graphNodes = [node, ...related].filter(Boolean);

        const lines = graphNodes
            .slice(1)
            .map((entry, index) => {
                const from = positions[0];
                const to = positions[index + 1];
                const cls = entry.domain !== domain && entry.domain !== "shared" ? "entangled" : "regular";
                return `<line class="${cls}" x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" />`;
            })
            .join("");

        const circles = graphNodes
            .map((entry, index) => {
                const pos = positions[index] || positions[0];
                const label = entry.title.length > 16 ? `${entry.title.slice(0, 16)}...` : entry.title;
                const cls = index === 0 ? "core" : "leaf";
                return `
                    <g class="${cls}" data-node-id="${entry.node_id}">
                        <circle cx="${pos.x}" cy="${pos.y}" r="${index === 0 ? 18 : 12}" />
                        <text x="${pos.x}" y="${pos.y + 30}" text-anchor="middle">${label}</text>
                    </g>
                `;
            })
            .join("");

        graphEl.innerHTML = `<g class="qa-graph-lines">${lines}</g><g>${circles}</g>`;

        graphEl.querySelectorAll("g[data-node-id]").forEach((nodeGroup) => {
            nodeGroup.addEventListener("click", () => {
                const targetNode = nodeMap.get(nodeGroup.dataset.nodeId);
                navigateToNode(targetNode);
            });
        });
    }

    function renderStats() {
        if (!statsEl) return;

        const node = nodeMap.get(activeNodeId);
        const branchNodes = getBranchNodes(activeBranch);
        const entangledOnBranch = branchNodes.filter((item) => hasCrossDomainEntanglement(item)).length;
        const totalVisible = nodes.filter((item) => item.domain === domain || item.domain === "shared").length;
        const linkedCount = node ? findEntangledNodes(node).length : 0;

        const allResourceTimes = nodes
            .flatMap((item) => item.resources || [])
            .map((resource) => resource.last_checked_at)
            .filter(Boolean)
            .map((value) => new Date(value))
            .filter((date) => !Number.isNaN(date.getTime()));

        const latestResourceCheck = allResourceTimes.length
            ? new Date(Math.max(...allResourceTimes.map((date) => date.getTime())))
            : null;

        const refreshedAt = latestResourceCheck
            ? latestResourceCheck.toLocaleString([], { year: "numeric", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" })
            : "Not available";

        statsEl.innerHTML = `
            <h4>Live Stats</h4>
            <div class="qa-stats-grid">
                <article class="qa-stat-card">
                    <p>Visible Nodes</p>
                    <strong>${totalVisible}</strong>
                </article>
                <article class="qa-stat-card">
                    <p>Branch Entanglements</p>
                    <strong>${entangledOnBranch}</strong>
                </article>
                <article class="qa-stat-card">
                    <p>Active Node Links</p>
                    <strong>${linkedCount}</strong>
                </article>
            </div>
            <p class="qa-stats-foot">Last data refresh: ${refreshedAt}</p>
        `;
    }

    function ensureValidSelection() {
        const branchNodes = getBranchNodes(activeBranch);
        if (!branchNodes.length) {
            activeBranch = BRANCHES[0];
        }

        if (!activeNodeId) {
            const firstEntangled = findFirstEntangledNode();
            if (firstEntangled) {
                activeBranch = firstEntangled.branch;
                activeNodeId = firstEntangled.node_id;
            }
        }

        const validNode = nodeMap.get(activeNodeId);
        if (!validNode || !getBranchNodes(activeBranch).some((item) => item.node_id === activeNodeId)) {
            activeNodeId = getBranchNodes(activeBranch)[0]?.node_id || null;
        }
    }

    function renderAll() {
        reloadGraphData();
        ensureValidSelection();
        branchTitleEl.textContent = activeBranch;
        renderBranches();
        renderNodeList();
        renderDetail();
        renderRelated();
        renderStats();
        renderGraph();
    }

    async function refreshFromApi() {
        if (!graphEndpoint) return;
        try {
            const response = await fetch(graphEndpoint, { cache: "no-store" });
            if (!response.ok) return;
            const latestPayload = await response.json();
            applyPayload(latestPayload);
            Object.values(workspaceRegistry).forEach((workspace) => workspace.rerender());
        } catch (_error) {
            // Network hiccups should not break the current UI state.
        }
    }

    function focusNode(nodeId) {
        const target = nodeMap.get(nodeId);
        if (!target) return;
        activeBranch = target.branch;
        activeNodeId = target.node_id;
        renderAll();
    }

    workspaceRegistry[domain] = {
        focusNode,
        rerender: renderAll,
    };

    activeNodeId = null;
    renderAll();
    setInterval(refreshFromApi, 120000);
}

applyPayload(payload);

const initialTabFromHash = window.location.hash.replace("#", "").trim();
if (initialTabFromHash && Array.from(tabButtons).some((button) => button.dataset.tab === initialTabFromHash)) {
    activateTab(initialTabFromHash);
}

document.querySelectorAll(".qa-shell").forEach((shell) => {
    initWorkspace(shell);
});
