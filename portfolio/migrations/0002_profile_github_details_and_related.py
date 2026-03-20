from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("portfolio", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="account_created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="account_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="blog_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="company",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="profile",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="profile",
            name="following",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="profile",
            name="hireable",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="public_gists",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="profile",
            name="twitter_username",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.CreateModel(
            name="GitHubOrganization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("login", models.CharField(max_length=150)),
                ("url", models.URLField(blank=True)),
                ("avatar_url", models.URLField(blank=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organizations",
                        to="portfolio.profile",
                    ),
                ),
            ],
            options={"ordering": ["login"]},
        ),
        migrations.CreateModel(
            name="GitHubRepository",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("repo_id", models.BigIntegerField(unique=True)),
                ("name", models.CharField(max_length=255)),
                ("full_name", models.CharField(max_length=255)),
                ("url", models.URLField(blank=True)),
                ("description", models.TextField(blank=True)),
                ("language", models.CharField(blank=True, max_length=100)),
                ("stargazers_count", models.PositiveIntegerField(default=0)),
                ("forks_count", models.PositiveIntegerField(default=0)),
                ("watchers_count", models.PositiveIntegerField(default=0)),
                ("open_issues_count", models.PositiveIntegerField(default=0)),
                ("is_fork", models.BooleanField(default=False)),
                ("archived", models.BooleanField(default=False)),
                ("pushed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="repositories",
                        to="portfolio.profile",
                    ),
                ),
            ],
            options={"ordering": ["-stargazers_count", "name"]},
        ),
    ]
