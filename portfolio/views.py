import re
import json
from html import escape
from pathlib import Path

from django.http import JsonResponse
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django.urls import reverse

from config.settings import BASE_DIR

from .forms import BlogPostCreateForm
from .models import (
    KnowledgeNode,
    KnowledgeNodeLink,
    KnowledgeNodeResource,
    KnowledgeNodeTechStack,
    BlogPost,
    LearningPathContent,
    Profile,
    ResourceItem,
    TopicScenario,
)

# Pre-compile regex patterns for performance
_KEYWORD_PATTERN_CACHE = {}
_URL_MARKDOWN_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_URL_BARE_PATTERN = re.compile(r"(?<![\"'=])(https?://[^\s<]+)")


class HomeView(TemplateView):
    template_name = "home.html"

    @staticmethod
    def _build_knowledge_graph_from_db() -> dict:
        # Cache the entire knowledge graph for 5 minutes (300 seconds)
        # This dramatically reduces DB queries on high-traffic pages
        cache_key = "knowledge_graph_home_view"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        if not KnowledgeNode.objects.exists():
            result = {"branches": [], "nodes": [], "domain_overrides": {}}
            cache.set(cache_key, result, 300)
            return result

        node_queryset = KnowledgeNode.objects.select_related("branch", "topic")

        branch_titles = list(
            dict.fromkeys(
                node_queryset.order_by("branch__sort_order", "branch__title").values_list("branch__title", flat=True)
            )
        )

        links_by_node = {}
        for link in KnowledgeNodeLink.objects.filter(is_live=True).select_related("from_node", "to_node"):
            links_by_node.setdefault(link.from_node.node_key, []).append(link.to_node.node_key)

        resources_by_node = {}
        for resource in KnowledgeNodeResource.objects.all().order_by("resource_type", "title"):
            resources_by_node.setdefault(resource.node.node_key, []).append(
                {
                    "type": resource.resource_type,
                    "title": resource.title,
                    "url": resource.url,
                    "source": resource.source,
                    "summary": resource.summary,
                    "last_checked_at": resource.last_checked_at.isoformat() if resource.last_checked_at else None,
                }
            )

        tech_by_node = {}
        tech_links = KnowledgeNodeTechStack.objects.select_related("node", "tool").all().order_by(
            "-is_primary", "tool__name"
        )
        for tech_link in tech_links:
            tech_by_node.setdefault(tech_link.node.node_key, []).append(
                {
                    "name": tech_link.tool.name,
                    "category": tech_link.tool.category,
                    "homepage_url": tech_link.tool.homepage_url,
                    "docs_url": tech_link.tool.docs_url,
                    "is_primary": tech_link.is_primary,
                    "note": tech_link.note,
                }
            )

        nodes = []
        for node in node_queryset:
            resources = resources_by_node.get(node.node_key, [])
            cookbooks = [item for item in resources if item["type"] == KnowledgeNodeResource.ResourceType.COOKBOOK]

            nodes.append(
                {
                    "node_id": node.node_key,
                    "branch": node.branch.title,
                    "type": node.node_type,
                    "domain": node.domain,
                    "title": node.title,
                    "content": node.content or node.summary,
                    "links": links_by_node.get(node.node_key, []),
                    "url": node.canonical_url,
                    "is_live_entangled": node.is_live_entangled,
                    "resources": resources,
                    "tech_stack": tech_by_node.get(node.node_key, []),
                    "cookbooks": cookbooks,
                }
            )

        result = {
            "branches": branch_titles,
            "nodes": nodes,
            "domain_overrides": {},
        }
        cache.set(cache_key, result, 300)  # Cache for 5 minutes
        return result


    @staticmethod
    def _load_quantum_ai_graph() -> dict:
        db_payload = HomeView._build_knowledge_graph_from_db()
        if db_payload.get("nodes"):
            return db_payload

        graph_path = Path(BASE_DIR) / "data" / "quantum_ai_graph.json"
        if not graph_path.exists():
            return {"branches": [], "nodes": [], "domain_overrides": {}}

        with graph_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    @staticmethod
    def _highlight_keywords(text: str) -> str:
        # Use pre-compiled patterns and cache keyword results for performance
        keywords = ["LLM", "LLMs", "Quantum AI", "QML", "JAX", "DeepMind", "Google Research"]
        for keyword in keywords:
            if keyword not in _KEYWORD_PATTERN_CACHE:
                _KEYWORD_PATTERN_CACHE[keyword] = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            pattern = _KEYWORD_PATTERN_CACHE[keyword]
            text = pattern.sub(lambda m: f"<span class=\"hl\">{m.group(0)}</span>", text)
        return text

    @staticmethod
    def _linkify(text: str) -> str:
        # Use pre-compiled regex patterns for URLs (compiled at module load time)
        # Markdown links first: [label](url)
        text = _URL_MARKDOWN_PATTERN.sub(
            lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noreferrer">{m.group(1)}</a>',
            text,
        )

        # Bare URLs
        text = _URL_BARE_PATTERN.sub(
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
        context["quantum_ai_graph"] = self._load_quantum_ai_graph()

        domain_data = {
            ResourceItem.Domain.QUANTUM: self._build_domain_payload(ResourceItem.Domain.QUANTUM),
            ResourceItem.Domain.AI: self._build_domain_payload(ResourceItem.Domain.AI),
        }

        context["domain_data"] = domain_data
        return context


class KnowledgeGraphAPIView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(HomeView._load_quantum_ai_graph())


class BlogListView(ListView):
    template_name = "blog_list.html"
    model = BlogPost
    context_object_name = "posts"
    paginate_by = 12

    def get_queryset(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)


class BlogDetailView(DetailView):
    template_name = "blog_detail.html"
    model = BlogPost
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)


class BlogCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = "blog_write.html"
    model = BlogPost
    form_class = BlogPostCreateForm
    login_url = "/admin/login/"

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Staff access required to write posts.")
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse("blog-detail", kwargs={"slug": self.object.slug})
