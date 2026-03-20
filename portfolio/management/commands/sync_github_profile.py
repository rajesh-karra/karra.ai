import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from portfolio.models import GitHubOrganization, GitHubRepository, Profile


def _fetch_json(url: str):
    try:
        response = requests.get(
            url,
            timeout=25,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CommandError(f"Failed to fetch GitHub API {url}: {exc}") from exc
    return response.json()


def _fetch_paginated_repos(username: str):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?type=owner&per_page=100&page={page}"
        data = _fetch_json(url)
        if not data:
            break
        repos.extend(data)
        page += 1
        if page > 20:
            break
    return repos


class Command(BaseCommand):
    help = "Sync profile data from GitHub for a username."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="r-karra", help="GitHub username")

    def handle(self, *args, **options):
        username = options["username"]
        data = _fetch_json(f"https://api.github.com/users/{username}")
        orgs = _fetch_json(f"https://api.github.com/users/{username}/orgs")
        repos = _fetch_paginated_repos(username)

        profile, _ = Profile.objects.update_or_create(
            github_username=username,
            defaults={
                "name": data.get("name") or username,
                "bio": data.get("bio") or "",
                "company": data.get("company") or "",
                "location": data.get("location") or "",
                "blog_url": data.get("blog") or "",
                "twitter_username": data.get("twitter_username") or "",
                "email": data.get("email") or "",
                "hireable": data.get("hireable"),
                "avatar_url": data.get("avatar_url") or "",
                "github_url": data.get("html_url") or f"https://github.com/{username}",
                "followers": data.get("followers") or 0,
                "following": data.get("following") or 0,
                "public_repos": data.get("public_repos") or 0,
                "public_gists": data.get("public_gists") or 0,
                "account_created_at": parse_datetime(data.get("created_at")) if data.get("created_at") else None,
                "account_updated_at": parse_datetime(data.get("updated_at")) if data.get("updated_at") else None,
            },
        )

        GitHubOrganization.objects.filter(profile=profile).delete()
        GitHubOrganization.objects.bulk_create(
            [
                GitHubOrganization(
                    profile=profile,
                    login=org.get("login") or "",
                    url=org.get("html_url") or "",
                    avatar_url=org.get("avatar_url") or "",
                )
                for org in orgs
            ]
        )

        GitHubRepository.objects.filter(profile=profile).delete()
        GitHubRepository.objects.bulk_create(
            [
                GitHubRepository(
                    profile=profile,
                    repo_id=repo.get("id"),
                    name=repo.get("name") or "",
                    full_name=repo.get("full_name") or "",
                    url=repo.get("html_url") or "",
                    description=repo.get("description") or "",
                    language=repo.get("language") or "",
                    stargazers_count=repo.get("stargazers_count") or 0,
                    forks_count=repo.get("forks_count") or 0,
                    watchers_count=repo.get("watchers_count") or 0,
                    open_issues_count=repo.get("open_issues_count") or 0,
                    is_fork=repo.get("fork") or False,
                    archived=repo.get("archived") or False,
                    pushed_at=parse_datetime(repo.get("pushed_at")) if repo.get("pushed_at") else None,
                )
                for repo in repos
                if repo.get("id")
            ]
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced profile for {profile.github_username} ({len(orgs)} orgs, {len(repos)} repos)."
            )
        )
