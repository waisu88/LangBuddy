from django.urls import path
from .views import get_sentence, repeat_view, translate_view
urlpatterns = [
    path('', get_sentence, name='get_record_view'),

    # path('repeat/', repeat, name='repeat'),
    path('repeat-view/', repeat_view, name='repeat-view'),
    path('translate-view/', translate_view, name='translate-view'),
]