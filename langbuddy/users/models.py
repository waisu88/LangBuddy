from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    # Zdefiniowanie poziomów biegłości CEFR
    A1 = 'A1'
    A2 = 'A2'
    B1 = 'B1'
    B2 = 'B2'
    C1 = 'C1'
    C2 = 'C2'

    CEFR_CHOICES = [
        (A1, 'A1 - Beginner'),
        (A2, 'A2 - Elementary'),
        (B1, 'B1 - Intermediate'),
        (B2, 'B2 - Upper Intermediate'),
        (C1, 'C1 - Advanced'),
        (C2, 'C2 - Proficient'),
    ]

    language = models.CharField(max_length=50, default="pl")
    target_language = models.CharField(max_length=50, default="hr")
    target_language_level = models.CharField(
        max_length=2,
        choices=CEFR_CHOICES,
        default=B1,
    )

    # Dodajemy `related_name` do pól `groups` i `user_permissions`, aby uniknąć konfliktu z modelem `auth.User`
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # Unikalna nazwa odwrotnej relacji
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Unikalna nazwa odwrotnej relacji
        blank=True,
    )

    def __str__(self):
        return self.username