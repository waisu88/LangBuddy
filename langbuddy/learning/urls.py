from django.urls import path
from .views import LearningView, TranslationView, EvaluateTranslationView, repeat, translate, upload_audio

urlpatterns = [
    path('start/', LearningView.as_view(), name='start-learning'),
    # path('translate/', TranslationView.as_view(), name='translate-sentence'),
    path('evaluate/', EvaluateTranslationView.as_view(), name='evaluate-translation'),
    path('upload_audio/', upload_audio, name='upload_audio'),
    path('repeat/', repeat),
    path('translate/', translate),
]