from django.contrib import admin

from .models import (
    BlogPost,
    GitHubOrganization,
    GitHubRepository,
    KnowledgeBranch,
    KnowledgeNode,
    KnowledgeNodeLink,
    KnowledgeNodeResource,
    KnowledgeNodeTechStack,
    KnowledgeTopic,
    LearningPathContent,
    Profile,
    ResourceItem,
    TechStackTool,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("github_username", "name", "followers", "public_repos", "updated_at")
    search_fields = ("github_username", "name")


@admin.register(LearningPathContent)
class LearningPathContentAdmin(admin.ModelAdmin):
    list_display = ("title", "updated_at")
    search_fields = ("title",)


@admin.register(ResourceItem)
class ResourceItemAdmin(admin.ModelAdmin):
    list_display = ("title", "domain", "category", "entangled_with_other_domain", "sort_order")
    list_filter = ("domain", "category", "entangled_with_other_domain")
    search_fields = ("title", "description")


@admin.register(GitHubOrganization)
class GitHubOrganizationAdmin(admin.ModelAdmin):
    list_display = ("login", "profile")
    search_fields = ("login", "profile__github_username")


@admin.register(GitHubRepository)
class GitHubRepositoryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "language",
        "stargazers_count",
        "forks_count",
        "watchers_count",
        "is_fork",
        "archived",
    )
    list_filter = ("language", "is_fork", "archived")
    search_fields = ("name", "full_name", "description", "profile__github_username")


@admin.register(KnowledgeTopic)
class KnowledgeTopicAdmin(admin.ModelAdmin):
    list_display = ("domain", "title", "topic_key", "updated_at")
    search_fields = ("title", "topic_key")


@admin.register(KnowledgeBranch)
class KnowledgeBranchAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "branch_key", "sort_order")
    list_filter = ("topic__domain",)
    search_fields = ("title", "branch_key")


@admin.register(KnowledgeNode)
class KnowledgeNodeAdmin(admin.ModelAdmin):
    list_display = (
        "node_key",
        "title",
        "domain",
        "node_type",
        "branch",
        "is_live_entangled",
        "sort_order",
    )
    list_filter = ("domain", "node_type", "is_live_entangled", "branch__topic__domain")
    search_fields = ("node_key", "title", "summary", "content")


@admin.register(KnowledgeNodeLink)
class KnowledgeNodeLinkAdmin(admin.ModelAdmin):
    list_display = ("from_node", "to_node", "link_type", "is_live", "weight")
    list_filter = ("link_type", "is_live")
    search_fields = ("from_node__node_key", "to_node__node_key", "from_node__title", "to_node__title")


@admin.register(TechStackTool)
class TechStackToolAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "homepage_url", "docs_url")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(KnowledgeNodeTechStack)
class KnowledgeNodeTechStackAdmin(admin.ModelAdmin):
    list_display = ("node", "tool", "is_primary", "note")
    list_filter = ("is_primary", "tool__category")
    search_fields = ("node__node_key", "node__title", "tool__name", "note")


@admin.register(KnowledgeNodeResource)
class KnowledgeNodeResourceAdmin(admin.ModelAdmin):
    list_display = ("node", "resource_type", "title", "source", "last_checked_at")
    list_filter = ("resource_type", "node__domain")
    search_fields = ("node__node_key", "node__title", "title", "source", "url")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_at", "updated_at")
    list_filter = ("status",)
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "summary", "body")
