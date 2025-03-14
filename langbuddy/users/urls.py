from django.urls import path
from .views import RegisterUser, UserAPIView

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register_user'),
    path('', UserAPIView.as_view(), name='user_api_view'),
]