from django.urls import path
from .views import LearningView, TranslationView, EvaluateTranslationView, exercise_view

urlpatterns = [
    path('start/', LearningView.as_view(), name='start-learning'),
    path('translate/', TranslationView.as_view(), name='translate-sentence'),
    path('evaluate/', EvaluateTranslationView.as_view(), name='evaluate-translation'),
    path('exercise/', exercise_view),
]