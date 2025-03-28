from rest_framework.routers import DefaultRouter
from .views import LanguageViewSet, SentenceViewSet, TranslationViewSet

router = DefaultRouter()
router.register(r'languages', LanguageViewSet)
router.register(r'sentences', SentenceViewSet)
router.register(r'translations', TranslationViewSet)

urlpatterns = router.urls
