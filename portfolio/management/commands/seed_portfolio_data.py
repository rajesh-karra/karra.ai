from django.core.management.base import BaseCommand

from portfolio.models import LearningPathContent, ResourceItem

LEARNING_PATH_TEXT = """Learning Pathway: Large Language Models (LLMs) and Quantum AI

This roadmap is phased to help you move from foundations to advanced specialization and research contribution in LLMs and Quantum AI, aligned with your interests in Google Research, DeepMind, JAX, IBM Quantum, Cirq, and PennyLane.

Phase 1: Foundation Building (Zero to Intermediate)
- Core Mathematics: Linear Algebra, Multivariate Calculus, Probability.
- Programming Essentials: Python, NumPy, Pandas, Scientific Computing.
- ML Fundamentals: Supervised/Unsupervised learning, training and evaluation.
- Deliverables: Build core ML models from scratch and complete practical tutorials.

Phase 2: Skill Development and Application (Intermediate to Advanced)
LLM Track:
- Deep Learning Fundamentals: CNNs, RNNs, Transformers.
- Transformer Architecture: Attention and encoder-decoder understanding.
- LLM Application: Prompt engineering, fine-tuning, and deployment.

Quantum AI Track:
- Quantum Mechanics Basics: Qubits, superposition, entanglement, measurement.
- Quantum Programming: Gates, Bell states, Deutsch-Jozsa.
- Quantum ML: VQE, QCNNs, TFQ experiments.

Phase 3: Research, Specialization, and Contribution
- Advanced LLM/JAX: Efficient training and open-source contributions.
- Quantum Error Correction: Capstone quantum algorithm projects.
- AI for Global Good: Prototype real-world applications.

Community and Program Engagement
- Google developer and accelerator programs.
- Academic progression toward Master's and PhD goals.
- Publish notebooks, datasets, models, and documentation across open platforms.
"""

RESOURCE_SEED = [
    {
        "domain": "quantum",
        "category": "source",
        "title": "IBM Quantum Learning",
        "description": "Core quantum learning portal and labs.",
        "url": "https://learning.quantum.ibm.com/",
        "entangled_with_other_domain": False,
        "sort_order": 1,
    },
    {
        "domain": "quantum",
        "category": "resources",
        "title": "PennyLane Codebook",
        "description": "Hands-on quantum machine learning and circuit tutorials.",
        "url": "https://pennylane.ai/codebook/",
        "entangled_with_other_domain": True,
        "sort_order": 2,
    },
    {
        "domain": "quantum",
        "category": "video",
        "title": "Qiskit YouTube",
        "description": "Quantum programming lectures and demonstrations.",
        "url": "https://www.youtube.com/@qiskit",
        "entangled_with_other_domain": False,
        "sort_order": 3,
    },
    {
        "domain": "quantum",
        "category": "blog",
        "title": "IBM Quantum Blog",
        "description": "Research and ecosystem updates.",
        "url": "https://www.ibm.com/quantum/blog",
        "entangled_with_other_domain": True,
        "sort_order": 4,
    },
    {
        "domain": "ai",
        "category": "source",
        "title": "Google DeepMind Educational",
        "description": "Educational material for RL and modern AI.",
        "url": "https://github.com/google-deepmind/educational",
        "entangled_with_other_domain": True,
        "sort_order": 1,
    },
    {
        "domain": "ai",
        "category": "resources",
        "title": "Google ML Crash Course",
        "description": "Foundational ML learning content.",
        "url": "https://developers.google.com/machine-learning/crash-course",
        "entangled_with_other_domain": False,
        "sort_order": 2,
    },
    {
        "domain": "ai",
        "category": "video",
        "title": "Andrej Karpathy Lectures",
        "description": "Practical model-building and deep learning intuition.",
        "url": "https://www.youtube.com/@AndrejKarpathy",
        "entangled_with_other_domain": True,
        "sort_order": 3,
    },
    {
        "domain": "ai",
        "category": "blog",
        "title": "Google Research Blog",
        "description": "Latest AI and scientific research updates.",
        "url": "https://research.google/blog/",
        "entangled_with_other_domain": True,
        "sort_order": 4,
    },
]


class Command(BaseCommand):
    help = "Seed portfolio content and resource links."

    def handle(self, *args, **options):
        LearningPathContent.objects.update_or_create(
            title="Learning Pathway: LLMs and Quantum AI",
            defaults={"body": LEARNING_PATH_TEXT},
        )

        for item in RESOURCE_SEED:
            ResourceItem.objects.update_or_create(
                domain=item["domain"],
                category=item["category"],
                title=item["title"],
                defaults=item,
            )

        self.stdout.write(self.style.SUCCESS("Portfolio content seeded."))
