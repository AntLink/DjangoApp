# apps/media/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TagsViewSet, CategoryViewSet, FolderViewSet, 
    MediaViewSet, MediahastagsViewSet, AuthViewSet, AdminViewSet
)

router = DefaultRouter(trailing_slash=False)
router.register(r'admin', AdminViewSet,basename='admin')
router.register(r'tags', TagsViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'folders', FolderViewSet)
router.register(r'media', MediaViewSet)
router.register(r'mediahastags', MediahastagsViewSet)
router.register(r'auth', AuthViewSet, basename='auth')  # Tambahkan ini

urlpatterns = [
    path('', include(router.urls)),
]