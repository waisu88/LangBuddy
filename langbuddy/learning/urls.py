from django.urls import path
from .views import (UserProgressAPIView, 
                    user_category_preferences,
                    UserSentenceProgressAPIView,
                    repeat, translate, check_answer,
                    conversation_respond, conversation_start)
# UserCategoryProgressAPIView, 
    # ,
    # RepeatAPIView, TranslateAPIView, CheckAnswerAPIView

urlpatterns = [
    path('check_answer/', check_answer, name='check_answer'),
    path('repeat/', repeat),
    path('translate/', translate),
    path('preferences/', user_category_preferences),
    path('progress/sentence/', UserSentenceProgressAPIView.as_view()),
    path('progress/', UserProgressAPIView.as_view()),
    path('conversation/start/', conversation_start),
    path('conversation/respond/', conversation_respond),
]