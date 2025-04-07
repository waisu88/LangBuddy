# Generated by Django 5.1.7 on 2025-04-02 18:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('languages', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LearningSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_translation', models.TextField(blank=True, null=True)),
                ('is_correct', models.BooleanField(default=False)),
                ('similarity_score', models.FloatField(default=0.0)),
                ('attempts', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('correct_translation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='languages.translation')),
                ('sentence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='languages.sentence')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')], default='B1', max_length=2)),
                ('score', models.PositiveIntegerField(default=0)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('difficulty_score', models.FloatField(default=0.5)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='languages.language')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
