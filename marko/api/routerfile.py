from rest_framework.routers import DefaultRouter

from .views import IdentifierViewSet, TypeIdViewSet

router = DefaultRouter()
router.register(r'typeids', TypeIdViewSet, basename='typeid')
router.register(r'identifiers', IdentifierViewSet, basename='identifier')

urlpatterns = router.urls
