from django.urls import path
from .views import main_view, repeat_view, translate_view, choose_categories_view, progress_view, register_view, conversation_ai_view
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', main_view, name='main-view'),
    path('progress-view/', progress_view, name='progress-view'),
    path('repeat-view/', repeat_view, name='repeat-view'),
    path('translate-view/', translate_view, name='translate-view'),
    path('choose-categories-view/', choose_categories_view, name='choose-categories-view'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    path('login/', LoginView.as_view(template_name="langbuddy_login.html"), name='login'),
    path('register/', register_view, name='register'),

    path("conversation/", conversation_ai_view, name='conversation-view'),
]