from django.contrib.auth.models import User
from django.db import models

CEFR_LEVELS = [
    ('A1', 'Beginner (A1)'),
    ('A2', 'Elementary (A2)'),
    ('B1', 'Intermediate (B1)'),
    ('B2', 'Upper-Intermediate (B2)'),
    ('C1', 'Advanced (C1)'),
    ('C2', 'Proficient (C2)'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    native_language = models.CharField(max_length=4, default='pl')
    target_language = models.CharField(max_length=4, default='hr')
    target_language_level = models.CharField(max_length=2, choices=CEFR_LEVELS, default='B1')

    def __str__(self):
        return f"{self.user.username}'s Profile"