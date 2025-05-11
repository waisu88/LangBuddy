from rest_framework import serializers
from .models import UserProgress, UserCategoryProgress, UserCategoryPreference, UserSentenceProgress

class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['user', 'language', 'global_level']


class UserCategoryProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCategoryProgress
        fields = "__all__"

class UserCategoryPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCategoryPreference
        fields = "__all__"

class UserSentenceProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSentenceProgress
        fields = "__all__"


