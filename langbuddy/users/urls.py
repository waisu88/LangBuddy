from django.urls import path
from .views import RegisterUser, UserAPIView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register_user'),
    path('', UserAPIView.as_view(), name='user_api_view'),
    path('login/', obtain_auth_token, name='login'),
]