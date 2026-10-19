from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("document_uploads", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadeddocument",
            name="revision",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
