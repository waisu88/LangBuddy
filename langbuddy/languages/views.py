from rest_framework import viewsets
from .models import Language, Sentence, Translation
from .serializers import LanguageSerializer, SentenceSerializer, TranslationSerializer

# Widok dla języków
class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

# Widok dla zdań
class SentenceViewSet(viewsets.ModelViewSet):
    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer

# Widok dla tłumaczeń
class TranslationViewSet(viewsets.ModelViewSet):
    queryset = Translation.objects.all()
    serializer_class = TranslationSerializer
