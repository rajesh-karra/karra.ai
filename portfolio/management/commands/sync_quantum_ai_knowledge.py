import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from portfolio.models import (
    KnowledgeBranch,
    KnowledgeNode,
    KnowledgeNodeLink,
    KnowledgeNodeResource,
    KnowledgeNodeTechStack,
    KnowledgeTopic,
    TechStackTool,
)


class Command(BaseCommand):
    help = "Sync normalized Quantum/AI knowledge graph data with real links, repos, and papers."

    BRANCHES = [
        ("documentation", "Documentation", 1),
        ("tech-stack-requirements", "Tech Stack Requirements", 2),
        ("research-papers", "Research Papers", 3),
        ("github-repositories", "GitHub Repositories", 4),
        ("other-resources", "Other Resources", 5),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-live",
            action="store_true",
            help="Skip live network pulls and use curated static resources only.",
        )

    def handle(self, *args, **options):
        skip_live = options["skip_live"]

        topics = self._upsert_topics()
        branches = self._upsert_branches(topics)
        nodes = self._upsert_nodes(topics, branches)
        self._upsert_tools_and_node_stack(nodes)
        self._upsert_static_resources(nodes)
        self._upsert_links(nodes)

        if not skip_live:
            self._sync_live_github_repos(nodes)
            self._sync_live_arxiv(nodes)

        self.stdout.write(self.style.SUCCESS("Quantum/AI knowledge graph sync complete."))

    def _upsert_topics(self):
        quantum_topic, _ = KnowledgeTopic.objects.update_or_create(
            domain=KnowledgeTopic.Domain.QUANTUM,
            defaults={
                "topic_key": "quantum-ai",
                "title": "Quantum AI",
                "overview": "Quantum-focused domain for circuits, QML, and hybrid architectures.",
                "url": "https://quantumai.google/",
            },
        )
        ai_topic, _ = KnowledgeTopic.objects.update_or_create(
            domain=KnowledgeTopic.Domain.AI,
            defaults={
                "topic_key": "ai-research",
                "title": "AI Research",
                "overview": "AI-focused domain for LLMs, sequence modeling, and applied ML systems.",
                "url": "https://research.google/",
            },
        )
        return {
            KnowledgeTopic.Domain.QUANTUM: quantum_topic,
            KnowledgeTopic.Domain.AI: ai_topic,
        }

    def _upsert_branches(self, topics):
        branches = {}
        for domain, topic in topics.items():
            for key, title, sort_order in self.BRANCHES:
                branch, _ = KnowledgeBranch.objects.update_or_create(
                    topic=topic,
                    branch_key=key,
                    defaults={
                        "title": title,
                        "sort_order": sort_order,
                    },
                )
                branches[(domain, key)] = branch
        return branches

    def _upsert_nodes(self, topics, branches):
        node_defs = [
            {
                "node_key": "ai_llm_particles",
                "topic": KnowledgeTopic.Domain.AI,
                "branch": "tech-stack-requirements",
                "domain": KnowledgeNode.Domain.AI,
                "node_type": "ai",
                "title": "AI-LLM (Sequence of Particles)",
                "summary": "LLM methods for particle-sequence style modeling tasks in physics-inspired domains.",
                "content": "Sequence modeling node for AI workflows that can entangle with QML for hybrid architecture experiments.",
                "canonical_url": "https://arxiv.org/abs/2402.13216",
                "is_live_entangled": True,
                "sort_order": 1,
            },
            {
                "node_key": "quantum_ml",
                "topic": KnowledgeTopic.Domain.QUANTUM,
                "branch": "tech-stack-requirements",
                "domain": KnowledgeNode.Domain.QUANTUM,
                "node_type": "tech",
                "title": "Quantum Machine Learning",
                "summary": "Hybrid quantum-classical modeling for optimization and scientific ML.",
                "content": "Central QML node connected to docs, papers, repos, and cookbooks across both AI and Quantum views.",
                "canonical_url": "https://pennylane.ai/qml/",
                "is_live_entangled": True,
                "sort_order": 2,
            },
            {
                "node_key": "doc_quantum_concepts",
                "topic": KnowledgeTopic.Domain.QUANTUM,
                "branch": "documentation",
                "domain": KnowledgeNode.Domain.QUANTUM,
                "node_type": "documentation",
                "title": "Quantum Concepts",
                "summary": "Qubits, superposition, entanglement, and variational circuits.",
                "content": "Core quantum concepts that power QML and hybrid model designs.",
                "canonical_url": "https://qiskit.org/learn",
                "is_live_entangled": True,
                "sort_order": 1,
            },
            {
                "node_key": "doc_ai_overview",
                "topic": KnowledgeTopic.Domain.AI,
                "branch": "documentation",
                "domain": KnowledgeNode.Domain.AI,
                "node_type": "documentation",
                "title": "AI Overview",
                "summary": "Modern AI workflows for sequence modeling, optimization, and evaluation.",
                "content": "AI documentation node tied to LLM and QML bridges.",
                "canonical_url": "https://ai.google/research/",
                "is_live_entangled": True,
                "sort_order": 1,
            },
            {
                "node_key": "qml_papers",
                "topic": KnowledgeTopic.Domain.QUANTUM,
                "branch": "research-papers",
                "domain": KnowledgeNode.Domain.QUANTUM,
                "node_type": "paper",
                "title": "Quantum ML Papers",
                "summary": "Peer-reviewed and preprint papers focused on QML and hybrid models.",
                "content": "Live-updated paper set from arXiv and research sources relevant to QML.",
                "canonical_url": "https://arxiv.org/",
                "is_live_entangled": True,
                "sort_order": 1,
            },
            {
                "node_key": "hybrid_models_papers",
                "topic": KnowledgeTopic.Domain.AI,
                "branch": "research-papers",
                "domain": KnowledgeNode.Domain.AI,
                "node_type": "paper",
                "title": "Hybrid Models Papers",
                "summary": "Hybrid quantum-classical model papers and benchmarks.",
                "content": "Research bridge across AI sequence models and QML circuits.",
                "canonical_url": "https://paperswithcode.com/",
                "is_live_entangled": True,
                "sort_order": 2,
            },
            {
                "node_key": "qml_github",
                "topic": KnowledgeTopic.Domain.QUANTUM,
                "branch": "github-repositories",
                "domain": KnowledgeNode.Domain.QUANTUM,
                "node_type": "repo",
                "title": "Quantum ML Repositories",
                "summary": "Curated GitHub repositories for QML and quantum stack implementation.",
                "content": "Live repository links fetched from GitHub Search API and curated sources.",
                "canonical_url": "https://github.com/topics/quantum-machine-learning",
                "is_live_entangled": True,
                "sort_order": 1,
            },
            {
                "node_key": "ml_github",
                "topic": KnowledgeTopic.Domain.AI,
                "branch": "github-repositories",
                "domain": KnowledgeNode.Domain.AI,
                "node_type": "repo",
                "title": "Machine Learning Repositories",
                "summary": "High-signal ML repositories and model engineering references.",
                "content": "GitHub repositories for AI model systems with links to QML-enabled projects.",
                "canonical_url": "https://github.com/topics/machine-learning",
                "is_live_entangled": True,
                "sort_order": 1,
            },
            {
                "node_key": "qml_courses",
                "topic": KnowledgeTopic.Domain.QUANTUM,
                "branch": "other-resources",
                "domain": KnowledgeNode.Domain.SHARED,
                "node_type": "course",
                "title": "QML Courses and Learning Paths",
                "summary": "Courses and structured pathways for Quantum ML.",
                "content": "Hands-on courses connecting QML concepts, libraries, and model building workflows.",
                "canonical_url": "https://quantumai.google/learn",
                "is_live_entangled": True,
                "sort_order": 1,
            },
        ]

        nodes = {}
        for row in node_defs:
            topic = topics[row["topic"]]
            branch = branches[(row["topic"], row["branch"])]
            defaults = {
                "topic": topic,
                "branch": branch,
                "node_type": row["node_type"],
                "domain": row["domain"],
                "title": row["title"],
                "summary": row["summary"],
                "content": row["content"],
                "canonical_url": row["canonical_url"],
                "is_live_entangled": row["is_live_entangled"],
                "sort_order": row["sort_order"],
            }
            node, _ = KnowledgeNode.objects.update_or_create(node_key=row["node_key"], defaults=defaults)
            nodes[row["node_key"]] = node

        return nodes

    def _upsert_tools_and_node_stack(self, nodes):
        tool_defs = [
            ("React", TechStackTool.Category.FRONTEND, "https://react.dev/", "https://react.dev/learn"),
            ("Tailwind CSS", TechStackTool.Category.FRONTEND, "https://tailwindcss.com/", "https://tailwindcss.com/docs"),
            ("FastAPI", TechStackTool.Category.BACKEND, "https://fastapi.tiangolo.com/", "https://fastapi.tiangolo.com/tutorial/"),
            ("JAX", TechStackTool.Category.ML, "https://github.com/jax-ml/jax", "https://jax.readthedocs.io/"),
            ("PyTorch", TechStackTool.Category.ML, "https://pytorch.org/", "https://pytorch.org/tutorials/"),
            ("Qiskit", TechStackTool.Category.QUANTUM, "https://qiskit.org/", "https://docs.quantum.ibm.com/"),
            ("Cirq", TechStackTool.Category.QUANTUM, "https://quantumai.google/cirq", "https://quantumai.google/cirq/tutorials"),
            ("PennyLane", TechStackTool.Category.QUANTUM, "https://pennylane.ai/", "https://docs.pennylane.ai/"),
        ]

        tools = {}
        for name, category, homepage, docs in tool_defs:
            tool, _ = TechStackTool.objects.update_or_create(
                name=name,
                defaults={
                    "category": category,
                    "homepage_url": homepage,
                    "docs_url": docs,
                },
            )
            tools[name] = tool

        stack_map = {
            "ai_llm_particles": ["JAX", "PyTorch", "FastAPI"],
            "quantum_ml": ["JAX", "PennyLane", "Qiskit", "Cirq", "PyTorch"],
            "qml_github": ["JAX", "PennyLane", "Qiskit"],
            "ml_github": ["JAX", "PyTorch", "React", "Tailwind CSS"],
            "doc_quantum_concepts": ["Qiskit", "Cirq", "PennyLane"],
            "doc_ai_overview": ["PyTorch", "JAX", "FastAPI"],
            "qml_courses": ["PennyLane", "Qiskit", "Cirq"],
            "qml_papers": ["JAX", "PennyLane", "PyTorch"],
            "hybrid_models_papers": ["JAX", "PyTorch", "PennyLane"],
        }

        KnowledgeNodeTechStack.objects.all().delete()
        for node_key, tool_names in stack_map.items():
            node = nodes[node_key]
            for index, tool_name in enumerate(tool_names):
                KnowledgeNodeTechStack.objects.create(
                    node=node,
                    tool=tools[tool_name],
                    is_primary=index == 0,
                    note="Primary stack" if index == 0 else "Supporting stack",
                )

    def _upsert_static_resources(self, nodes):
        KnowledgeNodeResource.objects.filter(source="curated").delete()
        now = timezone.now()

        resources = {
            "ai_llm_particles": [
                (KnowledgeNodeResource.ResourceType.PAPER, "Particle Transformer", "https://arxiv.org/abs/2202.03772", "curated", "Sequence modeling for particle data."),
                (KnowledgeNodeResource.ResourceType.DOC, "Hugging Face LLM Course", "https://huggingface.co/learn/llm-course/chapter1/1", "curated", "Practical LLM engineering course."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "OpenAI Cookbook", "https://github.com/openai/openai-cookbook", "curated", "Prompting and LLM implementation cookbook."),
            ],
            "quantum_ml": [
                (KnowledgeNodeResource.ResourceType.DOC, "PennyLane QML", "https://pennylane.ai/qml/", "curated", "QML theory and tutorials."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "Qiskit Learning Path", "https://learning.quantum.ibm.com/", "curated", "Hands-on quantum cookbook path."),
                (KnowledgeNodeResource.ResourceType.COURSE, "Google Quantum AI Learning", "https://quantumai.google/learn", "curated", "Courses and educational material."),
            ],
            "doc_quantum_concepts": [
                (KnowledgeNodeResource.ResourceType.DOC, "Qiskit Textbook", "https://qiskit.org/learn", "curated", "Foundations of quantum computing."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "Cirq Notebooks", "https://quantumai.google/cirq/tutorials", "curated", "Cirq tutorial cookbook."),
            ],
            "doc_ai_overview": [
                (KnowledgeNodeResource.ResourceType.DOC, "DeepLearning.AI Short Courses", "https://www.deeplearning.ai/short-courses/", "curated", "Modern AI workflow documentation and labs."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "PyTorch Recipes", "https://pytorch.org/tutorials/recipes/recipes_index.html", "curated", "Model engineering cookbook."),
            ],
            "qml_papers": [
                (KnowledgeNodeResource.ResourceType.PAPER, "Quantum Convolutional Neural Networks", "https://www.nature.com/articles/s41567-019-0648-8", "curated", "Foundational QCNN paper."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "PennyLane Demos", "https://pennylane.ai/qml/demonstrations", "curated", "Hands-on QML demos."),
            ],
            "hybrid_models_papers": [
                (KnowledgeNodeResource.ResourceType.PAPER, "Data re-uploading for a universal quantum classifier", "https://arxiv.org/abs/1907.02085", "curated", "Hybrid model strategy paper."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "JAX Sharp Bits", "https://jax.readthedocs.io/en/latest/notebooks/Common_Gotchas_in_JAX.html", "curated", "JAX implementation cookbook."),
            ],
            "qml_github": [
                (KnowledgeNodeResource.ResourceType.REPO, "PennyLaneAI/pennylane", "https://github.com/PennyLaneAI/pennylane", "curated", "Core QML framework repo."),
                (KnowledgeNodeResource.ResourceType.REPO, "Qiskit/qiskit", "https://github.com/Qiskit/qiskit", "curated", "Qiskit SDK repository."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "Qiskit Textbook Notebooks", "https://github.com/Qiskit/textbook", "curated", "Quantum algorithm cookbook notebooks."),
            ],
            "ml_github": [
                (KnowledgeNodeResource.ResourceType.REPO, "jax-ml/jax", "https://github.com/jax-ml/jax", "curated", "JAX core repository."),
                (KnowledgeNodeResource.ResourceType.REPO, "pytorch/pytorch", "https://github.com/pytorch/pytorch", "curated", "PyTorch core repository."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "PyTorch Examples", "https://github.com/pytorch/examples", "curated", "End-to-end ML cookbook examples."),
            ],
            "qml_courses": [
                (KnowledgeNodeResource.ResourceType.COURSE, "IBM Quantum Learning", "https://learning.quantum.ibm.com/", "curated", "Quantum courses from IBM."),
                (KnowledgeNodeResource.ResourceType.COURSE, "Xanadu Quantum Codebook", "https://pennylane.ai/codebook/", "curated", "Practical QML coursebook."),
                (KnowledgeNodeResource.ResourceType.COOKBOOK, "TensorFlow Quantum Tutorials", "https://www.tensorflow.org/quantum/tutorials", "curated", "Hybrid ML cookbook series."),
            ],
        }

        for node_key, rows in resources.items():
            node = nodes[node_key]
            for resource_type, title, url, source, summary in rows:
                KnowledgeNodeResource.objects.update_or_create(
                    node=node,
                    resource_type=resource_type,
                    url=url,
                    defaults={
                        "title": title,
                        "source": source,
                        "summary": summary,
                        "last_checked_at": now,
                    },
                )

        cookbook_fallback_url = "https://github.com/topics/machine-learning"
        for node in nodes.values():
            if not node.resources.filter(resource_type=KnowledgeNodeResource.ResourceType.COOKBOOK).exists():
                KnowledgeNodeResource.objects.update_or_create(
                    node=node,
                    resource_type=KnowledgeNodeResource.ResourceType.COOKBOOK,
                    url=f"{cookbook_fallback_url}?node={node.node_key}",
                    defaults={
                        "title": f"{node.title} Cookbook",
                        "source": "curated",
                        "summary": "General implementation cookbook linked to this node.",
                        "last_checked_at": now,
                    },
                )

    def _upsert_links(self, nodes):
        KnowledgeNodeLink.objects.all().delete()

        links = [
            ("ai_llm_particles", "quantum_ml", KnowledgeNodeLink.LinkType.ENTANGLED),
            ("quantum_ml", "ai_llm_particles", KnowledgeNodeLink.LinkType.ENTANGLED),
            ("ai_llm_particles", "qml_papers", KnowledgeNodeLink.LinkType.RELATED),
            ("quantum_ml", "doc_quantum_concepts", KnowledgeNodeLink.LinkType.RELATED),
            ("quantum_ml", "qml_papers", KnowledgeNodeLink.LinkType.RELATED),
            ("quantum_ml", "qml_github", KnowledgeNodeLink.LinkType.RELATED),
            ("quantum_ml", "qml_courses", KnowledgeNodeLink.LinkType.RELATED),
            ("doc_ai_overview", "ai_llm_particles", KnowledgeNodeLink.LinkType.RELATED),
            ("doc_quantum_concepts", "quantum_ml", KnowledgeNodeLink.LinkType.RELATED),
            ("hybrid_models_papers", "quantum_ml", KnowledgeNodeLink.LinkType.ENTANGLED),
            ("ml_github", "qml_github", KnowledgeNodeLink.LinkType.ENTANGLED),
            ("qml_papers", "hybrid_models_papers", KnowledgeNodeLink.LinkType.ENTANGLED),
            ("qml_courses", "quantum_ml", KnowledgeNodeLink.LinkType.RELATED),
            ("qml_courses", "ai_llm_particles", KnowledgeNodeLink.LinkType.ENTANGLED),
        ]

        for from_key, to_key, link_type in links:
            KnowledgeNodeLink.objects.create(
                from_node=nodes[from_key],
                to_node=nodes[to_key],
                link_type=link_type,
                is_live=True,
                weight=1.0,
            )

    def _sync_live_github_repos(self, nodes):
        now = timezone.now()
        targets = [
            ("qml_github", "quantum machine learning"),
            ("ml_github", "machine learning"),
        ]

        for node_key, query in targets:
            node = nodes[node_key]
            url = (
                "https://api.github.com/search/repositories"
                f"?q={quote_plus(query)}&sort=stars&order=desc&per_page=6"
            )
            try:
                response = requests.get(url, timeout=12)
                response.raise_for_status()
                payload = response.json()
            except requests.RequestException:
                continue

            for item in payload.get("items", []):
                repo_url = item.get("html_url")
                full_name = item.get("full_name")
                if not repo_url or not full_name:
                    continue

                KnowledgeNodeResource.objects.update_or_create(
                    node=node,
                    resource_type=KnowledgeNodeResource.ResourceType.REPO,
                    url=repo_url,
                    defaults={
                        "title": full_name,
                        "source": "github_api",
                        "summary": item.get("description") or "",
                        "external_id": str(item.get("id", "")),
                        "metadata": {
                            "stars": item.get("stargazers_count", 0),
                            "language": item.get("language", ""),
                        },
                        "last_checked_at": now,
                    },
                )

    def _sync_live_arxiv(self, nodes):
        now = timezone.now()
        targets = [
            ("qml_papers", "quantum machine learning"),
            ("hybrid_models_papers", "hybrid quantum classical machine learning"),
        ]

        namespace = {"atom": "http://www.w3.org/2005/Atom"}

        for node_key, query in targets:
            node = nodes[node_key]
            url = (
                "https://export.arxiv.org/api/query?"
                f"search_query=all:{quote_plus(query)}&start=0&max_results=6&sortBy=submittedDate&sortOrder=descending"
            )

            try:
                response = requests.get(url, timeout=12)
                response.raise_for_status()
            except requests.RequestException:
                continue

            try:
                root = ET.fromstring(response.text)
            except ET.ParseError:
                continue

            for entry in root.findall("atom:entry", namespace):
                title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
                summary = (entry.findtext("atom:summary", default="", namespaces=namespace) or "").strip()
                entry_id = (entry.findtext("atom:id", default="", namespaces=namespace) or "").strip()
                published_text = (entry.findtext("atom:published", default="", namespaces=namespace) or "").strip()

                if not title or not entry_id:
                    continue

                published_at = None
                if published_text:
                    try:
                        published_at = datetime.fromisoformat(published_text.replace("Z", "+00:00"))
                    except ValueError:
                        published_at = None

                KnowledgeNodeResource.objects.update_or_create(
                    node=node,
                    resource_type=KnowledgeNodeResource.ResourceType.PAPER,
                    url=entry_id,
                    defaults={
                        "title": title,
                        "source": "arxiv_api",
                        "summary": " ".join(summary.split())[:1200],
                        "published_at": published_at,
                        "last_checked_at": now,
                    },
                )
