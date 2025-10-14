# myapp/serializers.py
from django.contrib.auth.models import Group as DjangoGroup
import os
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from ..models import RecentAsset
from .asset import AssetSerializer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
User = get_user_model()

import os
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from ..models import Asset

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer utama untuk membaca data aset.
    """
    id = serializers.CharField(read_only=True)
    tags = serializers.JSONField(default=list, required=False)
    name = serializers.CharField(read_only=True)
    extension = serializers.CharField(read_only=True)
    url = serializers.SerializerMethodField()
    imageUrls = serializers.SerializerMethodField()
    size = serializers.IntegerField(read_only=True)
    mimeType = serializers.CharField(source='mime_type', read_only=True)
    categoryId = serializers.UUIDField(source='category.id', allow_null=True)
    folderId = serializers.UUIDField(source='folder.id', allow_null=True)
    uploadedAt = serializers.DateTimeField(source='uploaded_at', format='%Y-%m-%dT%H:%M:%SZ')
    lastModifiedAt = serializers.DateTimeField(source='last_modified_at', format='%Y-%m-%dT%H:%M:%SZ')
    lastUsedAt = serializers.DateTimeField(source='last_used_at', format='%Y-%m-%dT%H:%M:%SZ')
    uploadedBy = UserSerializer(read_only=True)
    metadata = serializers.JSONField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'tags', 'name', 'extension', 'url', 'imageUrls', 'size', 'mimeType',
            'categoryId', 'folderId', 'uploadedAt', 'lastModifiedAt', 'lastUsedAt',
            'uploadedBy', 'metadata'
        ]

    def get_url(self, obj):
        """Menghasilkan URL lengkap untuk file aset."""
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    def get_imageUrls(self, obj):
        """Mengambil URL thumbnail dari metadata."""
        return obj.metadata.get('imageUrls', {})

    def get_categoryId(self, obj):
        """Mengambil ID kategori."""
        if obj.category:
            return str(obj.category.id)
        return None

    def get_folderId(self, obj):
        """Mengambil ID folder."""
        if obj.field:
            return str(obj.field.id)
        return None

class RecentAssetUpdateSerializer(serializers.ListSerializer):
    child = serializers.CharField()

class RecentAssetSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)

    class Meta:
        model = RecentAsset
        fields = ['asset', 'accessed_at']
