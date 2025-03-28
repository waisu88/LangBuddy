from django.db import models


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Np. English, Polish
    code = models.CharField(max_length=10, unique=True)  # Np. en, pl, hr

    def __str__(self):
        return f"{self.name} ({self.code})"


class Sentence(models.Model):
    content = models.TextField()  # Treść zdania
    language = models.ForeignKey(Language, on_delete=models.CASCADE)  # Język źródłowy
    level = models.CharField(
        max_length=2,
        choices=[
            ('A1', 'A1'), ('A2', 'A2'),
            ('B1', 'B1'), ('B2', 'B2'),
            ('C1', 'C1'), ('C2', 'C2')
        ],
        default='B1'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content[:50]}... ({self.language.code}, {self.level})"
    

class Translation(models.Model):
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE, related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)  # Język docelowy
    content = models.TextField()  # Przetłumaczone zdanie
    is_verified = models.BooleanField(default=False)  # Czy tłumaczenie zostało zweryfikowane

    def __str__(self):
        return f"{self.content[:50]}... ({self.language.code})"
