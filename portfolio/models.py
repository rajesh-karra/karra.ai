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


class KnowledgeTopic(models.Model):
    class Domain(models.TextChoices):
        QUANTUM = "quantum", "Quantum"
        AI = "ai", "AI"

    domain = models.CharField(max_length=20, choices=Domain.choices, unique=True)
    topic_key = models.SlugField(max_length=80)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain"]

    def __str__(self) -> str:
        return f"{self.get_domain_display()} - {self.title}"


class KnowledgeBranch(models.Model):
    topic = models.ForeignKey(KnowledgeTopic, on_delete=models.CASCADE, related_name="branches")
    branch_key = models.SlugField(max_length=80)
    title = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["topic__domain", "sort_order", "title"]
        constraints = [
            models.UniqueConstraint(fields=["topic", "branch_key"], name="uq_knowledge_branch_topic_key"),
        ]

    def __str__(self) -> str:
        return f"{self.topic.get_domain_display()} - {self.title}"


class KnowledgeNode(models.Model):
    class Domain(models.TextChoices):
        QUANTUM = "quantum", "Quantum"
        AI = "ai", "AI"
        SHARED = "shared", "Shared"

    topic = models.ForeignKey(KnowledgeTopic, on_delete=models.CASCADE, related_name="nodes")
    branch = models.ForeignKey(KnowledgeBranch, on_delete=models.CASCADE, related_name="nodes")
    node_key = models.SlugField(max_length=120, unique=True)
    node_type = models.CharField(max_length=80)
    domain = models.CharField(max_length=20, choices=Domain.choices, default=Domain.SHARED)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)
    canonical_url = models.URLField(blank=True)
    is_live_entangled = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["topic__domain", "branch__sort_order", "sort_order", "title"]

    def __str__(self) -> str:
        return self.title


class KnowledgeNodeLink(models.Model):
    class LinkType(models.TextChoices):
        RELATED = "related", "Related"
        ENTANGLED = "entangled", "Entangled"
        DEPENDS_ON = "depends_on", "Depends On"

    from_node = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name="outgoing_links")
    to_node = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name="incoming_links")
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.RELATED)
    is_live = models.BooleanField(default=True)
    weight = models.FloatField(default=1.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_node", "to_node", "link_type"],
                name="uq_knowledge_node_link_pair_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.from_node.node_key} -> {self.to_node.node_key} ({self.link_type})"


class TechStackTool(models.Model):
    class Category(models.TextChoices):
        FRONTEND = "frontend", "Frontend"
        BACKEND = "backend", "Backend"
        ML = "ml", "ML"
        QUANTUM = "quantum", "Quantum"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    homepage_url = models.URLField(blank=True)
    docs_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class KnowledgeNodeTechStack(models.Model):
    node = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name="tech_links")
    tool = models.ForeignKey(TechStackTool, on_delete=models.CASCADE, related_name="node_links")
    note = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["node", "tool"], name="uq_knowledge_node_tool"),
        ]

    def __str__(self) -> str:
        return f"{self.node.node_key} - {self.tool.name}"


class KnowledgeNodeResource(models.Model):
    class ResourceType(models.TextChoices):
        DOC = "doc", "Documentation"
        PAPER = "paper", "Research Paper"
        REPO = "repo", "GitHub Repository"
        RESOURCE = "resource", "Resource"
        COURSE = "course", "Course"
        VIDEO = "video", "Video"
        BLOG = "blog", "Blog"
        COOKBOOK = "cookbook", "Cookbook"

    node = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    title = models.CharField(max_length=255)
    url = models.URLField()
    source = models.CharField(max_length=120, blank=True)
    summary = models.TextField(blank=True)
    external_id = models.CharField(max_length=120, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["resource_type", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["node", "resource_type", "url"],
                name="uq_knowledge_node_resource_url",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.node.node_key} - {self.title}"


class BlogPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    summary = models.TextField(blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    tags = models.JSONField(default=list, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self) -> str:
        return self.title
