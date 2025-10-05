# myapp/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import *
# Buat router dan daftarkan viewsets kita
router = DefaultRouter(trailing_slash=False)
# router = DefaultRouter()
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'recent', RecentAssetViewSet, basename='recent-asset')
router.register(r'auth', AuthViewSet, basename='auth')

# --- DAFTARKAN VIEWSET BARU INI ---
# router.register(r'admin/groups', WorkspaceGroupViewSet, basename='workspace-group')
router.register(r'admin/permissions', PermissionViewSet, basename='permission')


# --- DAFTARKAN VIEWSET ADMIN BARU INI ---
router.register(r'admin/categories', AdminCategoryViewSet, basename='admin-category')
router.register(r'admin/images', AdminImageViewSet, basename='admin-image')
router.register(r'admin/groups', AdminGroupViewSet, basename='admin-group')

# URL API ditentukan secara otomatis oleh router
urlpatterns = [
    path('api/', include(router.urls)),

    # Endpoint Autentikasi
    path('api/token', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoint Superadmin
    path('api/superadmin/environmentConfig', SuperadminEnvironmentConfigView.as_view(), name='superadmin-env-config'),
    path('api/superadmin/workspacesTemplate', SuperadminWorkspaceTemplateView.as_view(), name='superadmin-workspace-template'),

# --- TAMBAHKAN RUTE UNTUK VIEW YANG BUKAN VIEWSET ---
    path('api/permissions', UserPermissionsView.as_view(), name='user-permissions'),
    path('api/admin/environmentConfig', AdminEnvironmentConfigView.as_view(), name='admin-env-config'),
]