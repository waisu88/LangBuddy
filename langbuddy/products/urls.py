from django.urls import path

from .views import ProductDetailAPIView, ProductListCreateAPIView

urlpatterns = [
    path('<int:pk>', ProductDetailAPIView.as_view()),
    path('', ProductListCreateAPIView.as_view()),
]