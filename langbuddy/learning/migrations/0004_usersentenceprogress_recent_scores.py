# Generated by Django 5.1.7 on 2025-04-29 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0003_usersentenceprogress_repeat_attempts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersentenceprogress',
            name='recent_scores',
            field=models.JSONField(default=list),
        ),
    ]
