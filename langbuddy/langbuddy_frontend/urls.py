from django.urls import path
from .views import main_view, repeat_view, translate_view, choose_categories_view, progress_view


urlpatterns = [
    path('', main_view, name='main-view'),
    path('progress-view/', progress_view, name='progress-view'),
    path('repeat-view/', repeat_view, name='repeat-view'),
    path('translate-view/', translate_view, name='translate-view'),
    path('choose-categories-view/', choose_categories_view, name='choose-categories-view'),
]