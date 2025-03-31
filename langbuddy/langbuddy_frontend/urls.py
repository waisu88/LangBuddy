from django.urls import path
from .views import upload_audio, get_sentence, repeat_view, repeat

urlpatterns = [
    path('', get_sentence, name='get_record_view'),
    path('upload_audio/', upload_audio, name='upload_audio'),
    path('repeat/', repeat, name='repeat'),
    path('repeat-view/', repeat_view, name='repeat-view'),
]