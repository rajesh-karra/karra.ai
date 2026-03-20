import re
from html import escape

from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from .models import LearningPathContent, Profile, ResourceItem, TopicScenario


class HomeView(TemplateView):
    template_name = "home.html"

    @staticmethod
    def _highlight_keywords(text: str) -> str:
        keywords = ["LLM", "LLMs", "Quantum AI", "QML", "JAX", "DeepMind", "Google Research"]
        for keyword in keywords:
            pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            text = pattern.sub(lambda m: f"<span class=\"hl\">{m.group(0)}</span>", text)
        return text

    @staticmethod
    def _linkify(text: str) -> str:
        # Markdown links first: [label](url)
        text = re.sub(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
            lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noreferrer">{m.group(1)}</a>',
            text,
        )

        # Bare URLs
        text = re.sub(
            r"(?<![\"'=])(https?://[^\s<]+)",
            lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noreferrer">{m.group(1)}</a>',
            text,
        )
        return text

    @classmethod
    def _format_learning_path_html(cls, raw_text: str | None):
        if not raw_text:
            return (
                mark_safe('<p class="lp-empty">Use the seed/import command to load your learning pathway content.</p>'),
                [],
            )

        lines = raw_text.splitlines()
        chunks = []
        toc = []
        toc_titles_seen = set()
        anchor_counts = {}
        in_list = False

        def close_list_if_open():
            nonlocal in_list
            if in_list:
                chunks.append("</ul>")
                in_list = False

        for original in lines:
            line = original.strip()
            if not line:
                close_list_if_open()
                continue

            safe_line = escape(line)
            safe_line = cls._linkify(safe_line)
            safe_line = cls._highlight_keywords(safe_line)

            if re.match(r"^phase\s+\d+", line, flags=re.IGNORECASE):
                close_list_if_open()
                base_anchor = re.sub(r"[^a-z0-9]+", "-", line.lower()).strip("-")[:80]
                count = anchor_counts.get(base_anchor, 0)
                anchor = base_anchor if count == 0 else f"{base_anchor}-{count + 1}"
                anchor_counts[base_anchor] = count + 1

                if line not in toc_titles_seen:
                    toc.append({"title": line, "anchor": anchor})
                    toc_titles_seen.add(line)

                chunks.append(f"<h3 id=\"{anchor}\">{safe_line}</h3>")
                continue

            if line.endswith(":") and len(line) <= 80:
                close_list_if_open()
                chunks.append(f"<h4>{safe_line}</h4>")
                continue

            if line.startswith(("- ", "* ")):
                if not in_list:
                    chunks.append("<ul>")
                    in_list = True
                bullet_text = safe_line[2:].strip()
                chunks.append(f"<li>{bullet_text}</li>")
                continue

            close_list_if_open()
            chunks.append(f"<p>{safe_line}</p>")

        close_list_if_open()
        return mark_safe("\n".join(chunks)), toc

    @staticmethod
    def _build_scenario_context() -> dict:
        scenario = {}
        for topic in TopicScenario.objects.all():
            scenario[topic.domain] = {
                "topic": topic.topic_title,
                "url": topic.topic_url,
                "description": topic.description,
                "branches": topic.branches or {},
                "entangled_partner_label": topic.entangled_partner_label,
                "entangled_panel_title": topic.entangled_panel_title,
                "entangled_panel_body": topic.entangled_panel_body,
                "entangled_points": topic.entangled_points or [],
            }
        return scenario

    @staticmethod
    def _build_domain_payload(domain: str):
        other_domain = (
            ResourceItem.Domain.AI
            if domain == ResourceItem.Domain.QUANTUM
            else ResourceItem.Domain.QUANTUM
        )
        own_items = ResourceItem.objects.filter(domain=domain)
        entangled_from_other = ResourceItem.objects.filter(
            domain=other_domain,
            entangled_with_other_domain=True,
        )

        payload = {}
        for category in [
            ResourceItem.Category.SOURCE,
            ResourceItem.Category.RESOURCES,
            ResourceItem.Category.VIDEO,
            ResourceItem.Category.BLOG,
        ]:
            payload[category] = {
                "own": own_items.filter(category=category),
                "entangled": entangled_from_other.filter(category=category),
            }
        return payload

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = Profile.objects.first()
        learning_path = LearningPathContent.objects.first()

        context["profile"] = profile
        context["learning_path"] = learning_path
        learning_path_html, learning_path_toc = self._format_learning_path_html(
            learning_path.body if learning_path else None
        )
        context["learning_path_html"] = learning_path_html
        context["learning_path_toc"] = learning_path_toc
        context["github_organizations"] = profile.organizations.all() if profile else []
        context["github_repositories"] = profile.repositories.all() if profile else []
        context["scenario"] = self._build_scenario_context()

        domain_data = {
            ResourceItem.Domain.QUANTUM: self._build_domain_payload(ResourceItem.Domain.QUANTUM),
            ResourceItem.Domain.AI: self._build_domain_payload(ResourceItem.Domain.AI),
        }

        context["domain_data"] = domain_data
        return context
