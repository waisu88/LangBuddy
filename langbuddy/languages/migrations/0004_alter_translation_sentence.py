# Generated by Django 5.1.7 on 2025-05-27 21:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('languages', '0003_alter_sentence_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='translation',
            name='sentence',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='languages.sentence'),
        ),
    ]
