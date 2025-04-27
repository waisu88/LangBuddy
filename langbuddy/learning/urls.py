from django.urls import path
from .views import (UserProgressAPIView, 
                    UserCategoryPreferenceAPIView, UserCategoryProgressAPIView, 
                    UserSentenceProgressAPIView,
                    repeat, translate, check_answer)
    # ,
    # RepeatAPIView, TranslateAPIView, CheckAnswerAPIView

urlpatterns = [
    # path('start/', LearningView.as_view(), name='start-learning'),
    # path('translate/', TranslationView.as_view(), name='translate-sentence'),
    # path('evaluate/', EvaluateTranslationView.as_view(), name='evaluate-translation'),
    path('check_answer/', check_answer, name='check_answer'),
    path('repeat/', repeat),
    path('translate/', translate),
    # path('check_answer/', CheckAnswerAPIView.as_view()),
    # path('repeat/', RepeatAPIView.as_view()),
    # path('translate/', TranslateAPIView.as_view()),
    path('progress/category/', UserCategoryProgressAPIView.as_view()),
    # path('progress/category/<id>/', UserCategoryProgressAPIView.as_view()),
    path('preferences/', UserCategoryPreferenceAPIView.as_view()),
    path('progress/sentence/', UserSentenceProgressAPIView.as_view()),
    path('progress/', UserProgressAPIView.as_view()),
]