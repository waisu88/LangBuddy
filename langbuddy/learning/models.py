from django.db import models
from django.contrib.auth.models import User
from languages.models import Sentence, Category, Language
from django.db.models import JSONField, Sum

class UserCategoryPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_preferences')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  # Czy użytkownik aktywnie chce szkolić tę kategorię
    priority = models.IntegerField(default=3)  # Priorytet zainteresowania np. 1-5

    def __str__(self):
        return f"{self.user.username} - {self.category.name} (priority: {self.priority})"

from django.utils import timezone
 
class UserSentenceProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)

    total_attempts = models.PositiveIntegerField(default=0)
        
    repeat_attempts = models.PositiveIntegerField(default=0)
    correct_attempts_repeat = models.PositiveIntegerField(default=0)

    translate_attempts = models.PositiveIntegerField(default=0)
    correct_attempts_translate = models.PositiveIntegerField(default=0)

    last_similarity_score_repeat = models.FloatField(default=0.0)
    recent_scores_repeat = JSONField(default=list, blank=True)  # <-- nowość

    last_similarity_score_translate = models.FloatField(default=0.0)
    recent_scores_translate = JSONField(default=list, blank=True)  # <-- nowość

    is_mastered_repeat = models.BooleanField(default=False)
    is_mastered_translate = models.BooleanField(default=False)
    last_attempt_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'sentence')

    def update_progress(self, similarity_score: float, attempt_type: str = "repeat"):
        self.total_attempts += 1
        self.last_attempt_at = timezone.now()

        if attempt_type == "repeat":
            self.repeat_attempts += 1
            self.last_similarity_score_repeat = similarity_score
            scores = self.recent_scores_repeat or []
            scores.append(similarity_score)
            self.recent_scores_repeat = scores[-3:]
            if similarity_score >= 80:
                self.correct_attempts_repeat += 1
            if len(self.recent_scores_repeat) == 3 and sum(self.recent_scores_repeat) / 3 >= 80:
                self.is_mastered_repeat = True
                """evaluate demotion jest źle przemyślana. 
                Jak wpadniesz poniżej 33% poprawnych powtórzeń 
                to za każdym razem CIę wyrzuci na niższy poziom, na razie wyłaczam"""
            # try:
            #     category_progress = UserCategoryProgress.objects.get(user=self.user, category=self.sentence.category)
            #     category_progress.evaluate_demotion() 
            # except UserCategoryProgress.DoesNotExist:
            #     pass

        elif attempt_type == "translate":
            self.translate_attempts += 1
            self.last_similarity_score_translate = similarity_score
            scores = self.recent_scores_translate or []
            scores.append(similarity_score)
            self.recent_scores_translate = scores[-3:]
            if similarity_score >= 80:
                self.correct_attempts_translate += 1
            if (len(self.recent_scores_translate) == 3 and sum(self.recent_scores_translate) / 3 >= 80) or \
                (sum(self.recent_scores_translate[-2:]) >= 90):
                self.is_mastered_translate = True
            try:
                category_progress = UserCategoryProgress.objects.get(user=self.user, category=self.sentence.category)
                category_progress.evaluate_promotion()
            except UserCategoryProgress.DoesNotExist:
                pass

        self.save()

    def accuracy(self):
        return (self.correct_attempts_translate / self.total_attempts) * 100 if self.total_attempts > 0 else 0

    def __str__(self):
        status = "Mastered" if self.is_mastered_translate else "In Progress"
        return f"{self.user.username} - {self.sentence.id} ({status}, {self.accuracy()}%)"

class UserCategoryProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    level = models.CharField(
        max_length=2,
        choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')],
        default='B1'
    )

    class Meta:
        unique_together = ('user', 'category')

    def __str__(self):
        return f"{self.user.username} - {self.category.name} ({self.level})"

    def evaluate_promotion(self):
        level = self.level
        progress_qs = UserSentenceProgress.objects.filter(
            user=self.user,
            sentence__category=self.category,
            sentence__level=level
        )
        
        all_category_sentences = Sentence.objects.filter(category=self.category, level=level)

        total = all_category_sentences.count()

        attempted = progress_qs.exclude(translate_attempts=0).count()
        mastered = progress_qs.filter(is_mastered_translate=True).count()
 
        if total == 0:
            return

        if attempted / total >= 0.7 and mastered / attempted >= 0.75:
            levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
            current_idx = levels.index(self.level)
            if current_idx < len(levels) - 1:
                self.level = levels[current_idx + 1]
                self.save()

    def evaluate_demotion(self):
        levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        current_idx = levels.index(self.level)

        if current_idx == 0:
            return  # Nie można spaść poniżej A1

        progress_qs = UserSentenceProgress.objects.filter(
            user=self.user,
            sentence__category=self.category,
            sentence__level=self.level
        ).filter(repeat_attempts__gte=3)  # tylko zdania, które miały szansę na naukę

        total_repeat_attempts = progress_qs.aggregate(total=Sum('repeat_attempts'))['total'] or 0
        total_correct_repeat = progress_qs.aggregate(correct=Sum('correct_attempts_repeat'))['correct'] or 0

        if total_repeat_attempts == 0:
            return

        accuracy = total_correct_repeat / total_repeat_attempts

        if accuracy <= 0.33:
            new_level = levels[current_idx - 1]
            self.level = new_level
            self.save()

            # Wyczyść dane z wyższego poziomu (z którego spadamy)
            UserSentenceProgress.objects.filter(
                user=self.user,
                sentence__category=self.category,
                sentence__level=levels[current_idx]
            ).update(
                is_mastered_repeat=False,
                is_mastered_translate=False,
                recent_scores_repeat=[],
                recent_scores_translate=[],
            )

            # Zresetuj częściowo dane z poziomu, na który spadamy
            lower_level_qs = UserSentenceProgress.objects.filter(
                user=self.user,
                sentence__category=self.category,
                sentence__level=new_level
            )

            for progress in lower_level_qs:
                progress.recent_scores_repeat = progress.recent_scores_repeat[1:] if len(progress.recent_scores_repeat) > 0 else []
                progress.recent_scores_translate = progress.recent_scores_translate[1:] if len(progress.recent_scores_translate) > 0 else []
                progress.is_mastered_repeat = False
                progress.is_mastered_translate = False
                progress.save()





class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    global_level = models.CharField(
        max_length=2,
        choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')],
        default='B1'
    )
    # Plus accuracy, score itd.

	