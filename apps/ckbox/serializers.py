from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model
User = get_user_model()

# app/serializers.py

import jwt
from django.conf import settings
import datetime

class CKBoxAuthSerializer:
    """
    Serializer untuk membuat payload JWT CKBox.
    Tidak menerima data, tapi menghasilkan payload berdasarkan request.
    """

    def __init__(self, request):
        self.request = request
        self.user = request.user

    def get_payload(self):
        """Membuat payload untuk token CKBox."""
        # Tentukan role berdasarkan user
        role = "superadmin" if self.user.is_superuser and self.user.is_staff else "admin"

        # Ambil workspace yang dimiliki user
        workspaces = [
            str(w) for w in Workspace.objects.filter(owner=self.user).values_list('id', flat=True)
        ]

        # 🔹 Ambil CKBox AUD dari database
        env_config = EnvironmentConfig.objects.first()
        aud = env_config.ckbox_project_id if env_config and env_config.ckbox_project_id else "ckbox"

        payload = {
            "aud": aud,
            "sub": str(self.user.id),
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            "auth": {
                "ckbox": {
                    "role": role,
                    "workspaces": workspaces
                }
            }
        }
        return payload

class CKBoxTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        role = "superadmin" if user.is_superuser and user.is_staff else "admin"
        ws = [str(w) for w in Workspace.objects.filter(owner=user).values_list('id', flat=True)]


        # 🔹 Ambil CKBox AUD dari database
        env = EnvironmentConfig.objects.first()
        aud = env.ckbox_project_id if env and env.ckbox_project_id else "default-audience"

        token["aud"] = aud
        token["sub"] = str(user.id)
        token["auth"] = {
            "ckbox": {
                "role": role,
                "workspaces": ws
            }
        }
        return token

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer kustom untuk menambahkan klaim (data) tambahan ke dalam JWT payload.
    """

    def validate(self, attrs):
        # Data default dari validasi user
        data = super().validate(attrs)

        # Tambahkan klaim kustom
        refresh = self.get_token(self.user)

        # Menambahkan role ke payload
        if self.user.is_superuser:
            role = 'superadmin'
        # Anda bisa menambahkan logika lain di sini, misal untuk 'admin' workspace
        else:
            role = 'admin'

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Tambahkan data ke payload access token
        data['access'] = str(refresh.access_token)
        # refresh.access_token.payload adalah dictionary yang bisa dimodifikasi
        refresh.access_token['role'] = role

        # Tambahkan audience (environment ID)
        # Ini bisa diambil dari settings atau model EnvironmentConfig
        from django.conf import settings
        refresh.access_token['aud'] = getattr(settings, 'CKBOX_ENVIRONMENT_ID', 'default-env')

        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

# class WorkspaceTemplateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WorkspaceTemplate
#         fields = '__all__'
#
# class WorkspaceGroupSerializer(serializers.ModelSerializer):
#     """
#     Serializer untuk WorkspaceGroup yang juga menangani pembuatan Group Django.
#     """
#     name = serializers.CharField(source='name', write_only=True)
#     workspace_id = serializers.UUIDField(write_only=True)
#
#     class Meta:
#         model = WorkspaceGroup
#         fields = ['id', 'name', 'workspace_id']
#
#     def create(self, validated_data):
#         name = validated_data.pop('name')
#         workspace_id = validated_data.pop('workspace_id')
#
#         django_group = DjangoGroup.objects.create(name=name)
#         workspace_group = WorkspaceGroup.objects.create(
#             group=django_group,
#             workspace_id=workspace_id
#         )
#         return workspace_group
