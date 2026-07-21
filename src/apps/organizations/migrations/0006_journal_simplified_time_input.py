from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0005_journal_typography_preferences"),
    ]

    operations = [
        migrations.AddField(
            model_name="interfacepreference",
            name="journal_simplified_time_input",
            field=models.BooleanField(
                default=False,
                verbose_name="Упрощённый ввод времени",
            ),
        ),
    ]
