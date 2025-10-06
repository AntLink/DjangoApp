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

class RecentAssetSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)

    class Meta:
        model = RecentAsset
        fields = ['asset', 'accessed_at']
