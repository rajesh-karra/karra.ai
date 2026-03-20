from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LearningPathContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("github_username", models.CharField(max_length=50, unique=True)),
                ("name", models.CharField(blank=True, max_length=200)),
                ("bio", models.TextField(blank=True)),
                ("location", models.CharField(blank=True, max_length=200)),
                ("avatar_url", models.URLField(blank=True)),
                ("github_url", models.URLField(blank=True)),
                ("followers", models.PositiveIntegerField(default=0)),
                ("public_repos", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ResourceItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "domain",
                    models.CharField(
                        choices=[("quantum", "Quantum"), ("ai", "AI")],
                        max_length=20,
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("source", "Source"),
                            ("resources", "Resources"),
                            ("video", "Video Lectures"),
                            ("blog", "Blog"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("url", models.URLField(blank=True)),
                ("entangled_with_other_domain", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["domain", "category", "sort_order", "title"]},
        ),
    ]
