# myapp/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.core.files.base import ContentFile
import io
from PIL import Image

from ..models import RecentAsset
from ..serializer.recentasset import RecentAssetSerializer
from ..permissions import IsSuperAdmin, IsWorkspaceMember, IsWorkspaceOwner
from ..pagination import CustomPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Prefetch

User = get_user_model()


class RecentAssetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecentAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RecentAsset.objects.filter(user=self.request.user).select_related('asset')