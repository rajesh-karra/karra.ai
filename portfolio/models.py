from django.db import models


class Profile(models.Model):
    github_username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=200, blank=True)
    blog_url = models.URLField(blank=True)
    twitter_username = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    hireable = models.BooleanField(null=True, blank=True)
    avatar_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    followers = models.PositiveIntegerField(default=0)
    following = models.PositiveIntegerField(default=0)
    public_repos = models.PositiveIntegerField(default=0)
    public_gists = models.PositiveIntegerField(default=0)
    account_created_at = models.DateTimeField(null=True, blank=True)
    account_updated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name or self.github_username


class LearningPathContent(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class ResourceItem(models.Model):
    class Domain(models.TextChoices):
        QUANTUM = "quantum", "Quantum"
        AI = "ai", "AI"

    class Category(models.TextChoices):
        SOURCE = "source", "Source"
        RESOURCES = "resources", "Resources"
        VIDEO = "video", "Video Lectures"
        BLOG = "blog", "Blog"

    domain = models.CharField(max_length=20, choices=Domain.choices)
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    entangled_with_other_domain = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["domain", "category", "sort_order", "title"]

    def __str__(self) -> str:
        return f"{self.get_domain_display()} - {self.title}"


class GitHubOrganization(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="organizations")
    login = models.CharField(max_length=150)
    url = models.URLField(blank=True)
    avatar_url = models.URLField(blank=True)

    class Meta:
        ordering = ["login"]

    def __str__(self) -> str:
        return self.login


class GitHubRepository(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="repositories")
    repo_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=100, blank=True)
    stargazers_count = models.PositiveIntegerField(default=0)
    forks_count = models.PositiveIntegerField(default=0)
    watchers_count = models.PositiveIntegerField(default=0)
    open_issues_count = models.PositiveIntegerField(default=0)
    is_fork = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    pushed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-stargazers_count", "name"]

    def __str__(self) -> str:
        return self.full_name


class TopicScenario(models.Model):
    class Domain(models.TextChoices):
        QUANTUM = "quantum", "Quantum"
        AI = "ai", "AI"

    domain = models.CharField(max_length=20, choices=Domain.choices, unique=True)
    topic_key = models.SlugField(max_length=80)
    topic_title = models.CharField(max_length=255)
    topic_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    branches = models.JSONField(default=dict)
    entangled_partner_label = models.CharField(max_length=255, blank=True)
    entangled_panel_title = models.CharField(max_length=255, blank=True)
    entangled_panel_body = models.TextField(blank=True)
    entangled_points = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain"]

    def __str__(self) -> str:
        return f"{self.get_domain_display()} - {self.topic_title}"
