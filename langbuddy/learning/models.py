from django.db import models
from django.contrib.auth.models import User
from languages.models import Sentence, Category, Language

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
    is_mastered = models.BooleanField(default=False)
    last_attempt_at = models.DateTimeField(auto_now=True)  # aktualizuje się automatycznie

    class Meta:
        unique_together = ('user', 'sentence')  # Jeden rekord dla danego użytkownika i zdania

    def update_progress(self, is_correct, similarity_score):
        self.total_attempts += 1
        if is_correct:
            self.correct_attempts += 1
        self.last_similarity_score = similarity_score

        # np. jeśli 3 razy dobrze z rzędu → oznacz jako opanowane
        if self.correct_attempts >= 3 and (self.correct_attempts / self.total_attempts) >= 0.8:
            self.is_mastered = True
        
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

    def check_completion(self):
        if self.total_sentences > 0 and (self.mastered_sentences / self.total_sentences) >= 0.8:
            self.is_completed = True
            self.upgrade_level()

    def upgrade_level(self):
        if self.is_completed and self.level != 'C2':
            levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
            current_index = levels.index(self.level)
            next_level = levels[current_index + 1] if current_index + 1 < len(levels) else 'C2'
            self.level = next_level
            self.is_completed = False  # Reset completion for next level
            self.mastered_sentences = 0
            self.total_sentences = 0
            self.save()

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

	