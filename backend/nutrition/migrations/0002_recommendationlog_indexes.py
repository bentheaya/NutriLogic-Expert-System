# Generated manually for RecommendationLog history index + ordering

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nutrition", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="recommendationlog",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="recommendationlog",
            index=models.Index(
                fields=["profile", "-created_at"],
                name="nutri_reclog_prof_created",
            ),
        ),
    ]
