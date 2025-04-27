from rest_framework.routers import DefaultRouter
from .views import LanguageViewSet, SentenceViewSet, TranslationViewSet, category_list
from django.urls import path

router = DefaultRouter()
router.register(r'languages', LanguageViewSet)
router.register(r'sentences', SentenceViewSet)
router.register(r'translations', TranslationViewSet)

urlpatterns = router.urls

urlpatterns += [
    path('categories/', category_list, name='category_list'),
]