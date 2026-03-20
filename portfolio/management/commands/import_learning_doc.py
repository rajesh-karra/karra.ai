import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from django.core.management.base import BaseCommand, CommandError

from portfolio.models import LearningPathContent, ResourceItem

DEFAULT_DOC_EXPORT_URL = (
    "https://docs.google.com/document/d/"
    "1RSezpbxa5_VNKxc4tARunh34F83lU8si50qgosN0fbk/export?format=txt"
)

QUANTUM_KEYS = {
    "quantum",
    "qiskit",
    "cirq",
    "pennylane",
    "qubit",
    "qml",
    "vqe",
    "ibm quantum",
    "entanglement",
}
AI_KEYS = {
    "llm",
    "language model",
    "jax",
    "flax",
    "optax",
    "deepmind",
    "tensorflow",
    "pytorch",
    "google ai",
    "machine learning",
    "generative ai",
    "agents",
}
VIDEO_KEYS = {"youtube", "lecture", "talk", "course", "workshop", "video"}
BLOG_KEYS = {"blog", "medium", "newsletter"}
SOURCE_KEYS = {"research", "program", "community", "accelerator", "google", "ibm"}


@dataclass
class Candidate:
    title: str
    url: str
    context: str


class Command(BaseCommand):
    help = "Import learning resources from a Google Doc and map them to Quantum/AI with entanglement."

    def add_arguments(self, parser):
        parser.add_argument("--doc-url", default=DEFAULT_DOC_EXPORT_URL, help="Google doc export URL")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace existing ResourceItem records before import.",
        )

    def handle(self, *args, **options):
        doc_url = options["doc_url"]
        replace = options["replace"]

        text = self._download_doc(doc_url)

        LearningPathContent.objects.update_or_create(
            title="Learning Pathway: LLMs and Quantum AI",
            defaults={"body": text[:120000]},
        )

        candidates = self._extract_candidates(text)
        if not candidates:
            raise CommandError("No resource candidates were extracted from the document.")

        if replace:
            ResourceItem.objects.all().delete()

        created = 0
        for index, candidate in enumerate(candidates, start=1):
            domain, entangled = self._infer_domain_and_entanglement(candidate)
            category = self._infer_category(candidate)

            ResourceItem.objects.update_or_create(
                domain=domain,
                category=category,
                title=candidate.title[:255],
                defaults={
                    "description": candidate.context[:1000],
                    "url": candidate.url[:500],
                    "entangled_with_other_domain": entangled,
                    "sort_order": index,
                },
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported learning data: {created} resources, mapped into Quantum/AI with entanglement."
            )
        )

    def _download_doc(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CommandError(f"Failed to download learning doc: {exc}") from exc
        text = response.text.strip()
        if not text:
            raise CommandError("Downloaded learning doc is empty.")
        return text

    def _extract_candidates(self, text: str) -> list[Candidate]:
        markdown_links = re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", text)
        plain_urls = set(re.findall(r"https?://[^\s)\]]+", text))

        candidates: list[Candidate] = []
        seen = set()

        for label, url in markdown_links:
            key = url.strip().rstrip(".,;")
            if key in seen:
                continue
            seen.add(key)
            context = self._collect_context(text, label, key)
            candidates.append(Candidate(title=self._clean_title(label), url=key, context=context))

        for url in sorted(plain_urls):
            key = url.strip().rstrip(".,;")
            if key in seen:
                continue
            seen.add(key)
            title = self._title_from_url(key)
            context = self._collect_context(text, title, key)
            candidates.append(Candidate(title=title, url=key, context=context))

        return candidates

    def _collect_context(self, text: str, label: str, url: str) -> str:
        idx = text.lower().find(label.lower())
        if idx == -1:
            idx = text.find(url)
        if idx == -1:
            return "Imported from learning document."
        start = max(0, idx - 140)
        end = min(len(text), idx + 220)
        return " ".join(text[start:end].split())

    def _clean_title(self, title: str) -> str:
        return " ".join(title.replace("\n", " ").split())

    def _title_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.replace("www.", "")
        path = parsed.path.strip("/")
        if path:
            last = path.split("/")[-1]
            pretty = re.sub(r"[-_]+", " ", last).strip()
            pretty = pretty if pretty else host
            return f"{host} - {pretty[:80]}"
        return host

    def _infer_domain_and_entanglement(self, candidate: Candidate) -> tuple[str, bool]:
        blob = f"{candidate.title} {candidate.context} {candidate.url}".lower()
        q_score = sum(1 for key in QUANTUM_KEYS if key in blob)
        ai_score = sum(1 for key in AI_KEYS if key in blob)

        if q_score > 0 and ai_score > 0:
            domain = ResourceItem.Domain.QUANTUM if q_score >= ai_score else ResourceItem.Domain.AI
            return domain, True

        if q_score > 0:
            return ResourceItem.Domain.QUANTUM, False

        return ResourceItem.Domain.AI, False

    def _infer_category(self, candidate: Candidate) -> str:
        blob = f"{candidate.title} {candidate.context} {candidate.url}".lower()

        if any(key in blob for key in VIDEO_KEYS):
            return ResourceItem.Category.VIDEO
        if any(key in blob for key in BLOG_KEYS):
            return ResourceItem.Category.BLOG
        if any(key in blob for key in SOURCE_KEYS):
            return ResourceItem.Category.SOURCE
        return ResourceItem.Category.RESOURCES
