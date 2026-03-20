import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from portfolio.models import TopicScenario

REQUIRED_BRANCH_KEYS = ["resources", "projects", "papers", "open_source", "git_repos"]


class Command(BaseCommand):
    help = "Import/update TopicScenario records from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="data/topic_scenarios.json",
            help="Path to the JSON file containing scenarios.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing TopicScenario records before import.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        replace = options["replace"]

        if not file_path.exists():
            raise CommandError(f"JSON file not found: {file_path}")

        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {file_path}: {exc}") from exc

        scenarios = payload.get("scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            raise CommandError("JSON must contain a non-empty 'scenarios' list.")

        domains_seen = set()
        for idx, item in enumerate(scenarios, start=1):
            domain = item.get("domain")
            if domain in domains_seen:
                raise CommandError(
                    f"Scenario #{idx} duplicates domain '{domain}'. "
                    "Provide at most one scenario per domain."
                )
            domains_seen.add(domain)

        if replace:
            TopicScenario.objects.all().delete()

        upserted = 0
        for idx, item in enumerate(scenarios, start=1):
            self._validate_item(item, idx)

            TopicScenario.objects.update_or_create(
                domain=item["domain"],
                defaults={
                    "topic_key": item["topic_key"],
                    "topic_title": item["topic_title"],
                    "topic_url": item.get("topic_url", ""),
                    "description": item.get("description", ""),
                    "branches": item.get("branches", {}),
                    "entangled_partner_label": item.get("entangled_partner_label", ""),
                    "entangled_panel_title": item.get("entangled_panel_title", ""),
                    "entangled_panel_body": item.get("entangled_panel_body", ""),
                    "entangled_points": item.get("entangled_points", []),
                },
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {upserted} TopicScenario records from {file_path}."))

    def _validate_item(self, item: dict, idx: int):
        required = ["domain", "topic_key", "topic_title", "branches", "entangled_points"]
        for key in required:
            if key not in item:
                raise CommandError(f"Scenario #{idx} is missing required key: {key}")

        if item["domain"] not in {TopicScenario.Domain.AI, TopicScenario.Domain.QUANTUM}:
            raise CommandError(
                f"Scenario #{idx} has invalid domain '{item['domain']}'. Use 'ai' or 'quantum'."
            )

        if not isinstance(item["branches"], dict):
            raise CommandError(f"Scenario #{idx} key 'branches' must be an object.")

        if not isinstance(item["topic_key"], str) or not item["topic_key"].strip():
            raise CommandError(f"Scenario #{idx} key 'topic_key' must be a non-empty string.")

        if not isinstance(item["topic_title"], str) or not item["topic_title"].strip():
            raise CommandError(f"Scenario #{idx} key 'topic_title' must be a non-empty string.")

        missing_branches = [key for key in REQUIRED_BRANCH_KEYS if key not in item["branches"]]
        if missing_branches:
            raise CommandError(
                f"Scenario #{idx} branches missing required keys: {', '.join(missing_branches)}"
            )

        for branch_key in REQUIRED_BRANCH_KEYS:
            branch_items = item["branches"][branch_key]
            if not isinstance(branch_items, list):
                raise CommandError(
                    f"Scenario #{idx} branch '{branch_key}' must be a list."
                )

            for item_idx, branch_item in enumerate(branch_items, start=1):
                self._validate_branch_item(idx, branch_key, item_idx, branch_item)

        if not isinstance(item["entangled_points"], list):
            raise CommandError(f"Scenario #{idx} key 'entangled_points' must be a list.")

        for point_idx, point in enumerate(item["entangled_points"], start=1):
            if not isinstance(point, str) or not point.strip():
                raise CommandError(
                    f"Scenario #{idx} entangled_points[{point_idx}] must be a non-empty string."
                )

    def _validate_branch_item(self, scenario_idx: int, branch_key: str, item_idx: int, branch_item: dict):
        if not isinstance(branch_item, dict):
            raise CommandError(
                f"Scenario #{scenario_idx} branch '{branch_key}' item #{item_idx} must be an object."
            )

        title = branch_item.get("title")
        if not isinstance(title, str) or not title.strip():
            raise CommandError(
                f"Scenario #{scenario_idx} branch '{branch_key}' item #{item_idx} requires non-empty 'title'."
            )

        if branch_key == "projects":
            summary = branch_item.get("summary")
            tech_stack = branch_item.get("tech_stack")
            if not isinstance(summary, str) or not summary.strip():
                raise CommandError(
                    f"Scenario #{scenario_idx} projects item #{item_idx} requires non-empty 'summary'."
                )
            if not isinstance(tech_stack, list) or not tech_stack:
                raise CommandError(
                    f"Scenario #{scenario_idx} projects item #{item_idx} requires non-empty 'tech_stack' list."
                )
            for stack_idx, stack_item in enumerate(tech_stack, start=1):
                if not isinstance(stack_item, str) or not stack_item.strip():
                    raise CommandError(
                        f"Scenario #{scenario_idx} projects item #{item_idx} tech_stack[{stack_idx}] "
                        "must be a non-empty string."
                    )
        else:
            url = branch_item.get("url")
            if not isinstance(url, str) or not url.strip():
                raise CommandError(
                    f"Scenario #{scenario_idx} branch '{branch_key}' item #{item_idx} requires non-empty 'url'."
                )
