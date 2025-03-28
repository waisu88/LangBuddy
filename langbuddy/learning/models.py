from django.db import models
from django.contrib.auth.models import User
from languages.models import Language

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    level = models.CharField(
        max_length=2,
        choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')],
        default='B1'
    )
    score = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    difficulty_score = models.FloatField(default=0.5)  # 0.0 - łatwe, 1.0 - trudne

    def accuracy(self):
        return (self.score / self.attempts) * 100 if self.attempts > 0 else 0

    def adjust_difficulty(self):
        if self.attempts > 0:
            error_rate = 1 - (self.score / self.attempts)
            self.difficulty_score = min(1.0, max(0.1, error_rate))

        # Automatyczne podnoszenie poziomu trudności
        if self.accuracy() >= 80 and self.level != 'C2':
            levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
            current_index = levels.index(self.level)
            self.level = levels[current_index + 1] if current_index + 1 < len(levels) else 'C2'
            self.score = 0
            self.attempts = 0

        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.language.name} ({self.level})"


from languages.models import Sentence, Translation

class LearningSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    user_translation = models.TextField(blank=True, null=True)
    correct_translation = models.ForeignKey(Translation, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    similarity_score = models.FloatField(default=0.0)
    attempts = models.PositiveIntegerField(default=1)  # Liczba prób na to zdanie
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Correct" if self.is_correct else "Incorrect"
        return f"{self.user.username} - {status} ({self.similarity_score}%)"
