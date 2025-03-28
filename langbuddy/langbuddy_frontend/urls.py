from django.urls import path
from .views import upload_audio, get_sentence

urlpatterns = [
    path('', get_sentence, name='get_record_view'),
    path('upload_audio/', upload_audio, name='upload_audio'),
]