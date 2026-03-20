from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portfolio", "0002_profile_github_details_and_related"),
    ]

    operations = [
        migrations.CreateModel(
            name="TopicScenario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(choices=[("quantum", "Quantum"), ("ai", "AI")], max_length=20, unique=True)),
                ("topic_key", models.SlugField(max_length=80)),
                ("topic_title", models.CharField(max_length=255)),
                ("topic_url", models.URLField(blank=True)),
                ("description", models.TextField(blank=True)),
                ("branches", models.JSONField(default=dict)),
                ("entangled_partner_label", models.CharField(blank=True, max_length=255)),
                ("entangled_panel_title", models.CharField(blank=True, max_length=255)),
                ("entangled_panel_body", models.TextField(blank=True)),
                ("entangled_points", models.JSONField(default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["domain"]},
        ),
    ]
