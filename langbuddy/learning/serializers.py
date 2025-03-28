from rest_framework import serializers
from .models import UserProgress, LearningSession

class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['user', 'language', 'level', 'score', 'attempts']

class LearningSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningSession
        fields = ['user', 'sentence', 'user_translation', 'correct_translation', 'is_correct', 'similarity_score', 'created_at']