from django.contrib import admin

from .models import GitHubOrganization, GitHubRepository, LearningPathContent, Profile, ResourceItem


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
