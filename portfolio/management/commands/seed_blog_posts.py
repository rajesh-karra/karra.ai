from django.core.management.base import BaseCommand
from django.utils import timezone

from portfolio.models import BlogPost


class Command(BaseCommand):
    help = "Seed published blog posts into Neon-backed BlogPost table."

    def handle(self, *args, **options):
        now = timezone.now()

        posts = [
            {
                "title": "AI-LLM and QML Entanglement for Particle Sequences",
                "slug": "ai-llm-qml-entanglement-particle-sequences",
                "summary": "How sequence-modeling LLM workflows can entangle with QML nodes for hybrid scientific research.",
                "body": (
                    "This note explores a practical bridge between AI-LLM sequence pipelines and Quantum ML.\n\n"
                    "When we model particle-like sequences, classical transformers provide strong baselines. "
                    "QML layers can then be introduced in constrained feature maps to test representation gains.\n\n"
                    "A reliable workflow is: baseline with PyTorch or JAX, add quantum feature embeddings, "
                    "and compare cost/accuracy with strict experiment tracking."
                ),
                "tags": ["ai", "llm", "qml", "physics", "sequence-modeling"],
            },
            {
                "title": "Production Notes: Normalizing a Knowledge Graph on Neon",
                "slug": "production-notes-normalizing-knowledge-graph-on-neon",
                "summary": "A practical schema strategy for topics, branches, nodes, links, resources, and stack metadata in Postgres.",
                "body": (
                    "A normalized schema keeps Quantum and AI content manageable over time.\n\n"
                    "Use separate tables for nodes, cross-node links, resources, and tech stack references. "
                    "This keeps ingestion clean and query patterns predictable.\n\n"
                    "Neon works well for this pattern because branch-based workflows and managed Postgres "
                    "fit staged data updates and background sync tasks."
                ),
                "tags": ["postgres", "neon", "knowledge-graph", "django"],
            },
            {
                "title": "Research Feed Design: Combining arXiv and GitHub Signals",
                "slug": "research-feed-design-arxiv-github-signals",
                "summary": "A lightweight pattern for attaching live papers and repositories to each knowledge node.",
                "body": (
                    "Live data ingestion should combine stable curated links with fetched feeds.\n\n"
                    "For papers, use arXiv API and keep metadata plus last_checked timestamps. "
                    "For repos, use GitHub search by domain queries and keep stars/language in metadata.\n\n"
                    "The UI should prioritize readability: concise cards, source badges, and direct actions."
                ),
                "tags": ["arxiv", "github", "data-ingestion", "research-ops"],
            },
            {
                "title": "Designing a Clear Quantum-AI Interface",
                "slug": "designing-clear-quantum-ai-interface",
                "summary": "Why card-based sections and explicit entanglement markers outperform dense tables for research UIs.",
                "body": (
                    "A research dashboard should be glanceable before it is exhaustive.\n\n"
                    "Replacing dense tables with compact cards improves scan speed and mobile fit. "
                    "For cross-domain relations, explicit entanglement banners prevent context loss.\n\n"
                    "The result is a faster navigation loop between AI and Quantum nodes."
                ),
                "tags": ["ui", "ux", "quantum-ai", "information-architecture"],
            },
            {
                "title": "Operational Playbook for Scheduled Knowledge Sync",
                "slug": "operational-playbook-scheduled-knowledge-sync",
                "summary": "A reliable timer-based workflow to keep resources fresh without manual intervention.",
                "body": (
                    "Scheduled sync should run as a timer service, not as an ad hoc cron command in user shells.\n\n"
                    "The pipeline should execute data sync, then collect static artifacts if needed, and log outcomes. "
                    "Keep failure logs queryable via journalctl and monitor drift in feed freshness.\n\n"
                    "This turns the content graph into a maintained system instead of a static snapshot."
                ),
                "tags": ["systemd", "operations", "automation", "django"],
            },
        ]

        created = 0
        updated = 0

        for post in posts:
            obj, was_created = BlogPost.objects.update_or_create(
                slug=post["slug"],
                defaults={
                    "title": post["title"],
                    "summary": post["summary"],
                    "body": post["body"],
                    "status": BlogPost.Status.PUBLISHED,
                    "tags": post["tags"],
                    "published_at": now,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: created={created}, updated={updated}, total={BlogPost.objects.count()}"
            )
        )
