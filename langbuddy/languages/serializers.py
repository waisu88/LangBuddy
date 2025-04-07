from rest_framework import serializers
from .models import Language, Sentence, Translation

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['name', 'code']

class SentenceSerializer(serializers.ModelSerializer):
    language = serializers.SlugRelatedField(slug_field='code', queryset=Language.objects.all())

    class Meta:
        model = Sentence
        fields = ['content', 'language', 'category', 'level', 'created_at']

class TranslationSerializer(serializers.ModelSerializer):
    sentence = serializers.PrimaryKeyRelatedField(queryset=Sentence.objects.all())
    language = serializers.SlugRelatedField(slug_field='code', queryset=Language.objects.all())

    class Meta:
        model = Translation
        fields = ['sentence', 'language', 'content', 'is_verified']
