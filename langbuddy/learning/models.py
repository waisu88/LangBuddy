from django.db import models
from django.contrib.auth.models import User
from languages.models import Sentence, Category, Language
from django.db.models import JSONField

class UserCategoryPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_preferences')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  # Czy użytkownik aktywnie chce szkolić tę kategorię
    priority = models.IntegerField(default=3)  # Priorytet zainteresowania np. 1-5

    def __str__(self):
        return f"{self.user.username} - {self.category.name} (priority: {self.priority})"


class UserSentenceProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)

    correct_attempts = models.PositiveIntegerField(default=0)
    total_attempts = models.PositiveIntegerField(default=0)
    repeat_attempts = models.PositiveIntegerField(default=0)
    translate_attempts = models.PositiveIntegerField(default=0)

    last_similarity_score = models.FloatField(default=0.0)
    recent_scores = JSONField(default=list)  # <-- nowość
    is_mastered = models.BooleanField(default=False)
    last_attempt_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'sentence')

    def update_progress(self, similarity_score: float, attempt_type: str = "default"):
        self.total_attempts += 1
        self.last_similarity_score = similarity_score

        # Update repeat/translate attempts
        if attempt_type == "repeat":
            self.repeat_attempts += 1
        elif attempt_type == "translate":
            self.translate_attempts += 1

        # Update recent scores (keep only last 3)
        scores = self.recent_scores or []
        scores.append(similarity_score)
        self.recent_scores = scores[-3:]

        # Master if average of last 3 >= 0.8
        if len(self.recent_scores) == 3 and sum(self.recent_scores) / 3 >= 0.8:
            self.is_mastered = True

        # (Optional) treat similarity >= 0.8 as correct
        if similarity_score >= 0.8:
            self.correct_attempts += 1
        self.save()

    def accuracy(self):
        return (self.correct_attempts / self.total_attempts) * 100 if self.total_attempts > 0 else 0

    def __str__(self):
        status = "Mastered" if self.is_mastered else "In Progress"
        return f"{self.user.username} - {self.sentence.id} ({status}, {self.accuracy()}%)"

class UserCategoryProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    level = models.CharField(  # <-- POZIOM DLA KONKRETNEJ KATEGORII!
        max_length=2,
        choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')],
        default='B1'
    )
    mastered_sentences = models.PositiveIntegerField(default=0)
    total_sentences = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.category.name} ({self.level})"


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    global_level = models.CharField(
        max_length=2,
        choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')],
        default='B1'
    )
    # Plus accuracy, score itd.

	