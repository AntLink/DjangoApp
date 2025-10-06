from rest_framework import serializers
from ..models import (
    Category,
    Asset,
    EnvironmentConfig,
    ImageQualityConfig,
    WorkspaceGroup
)


class CategoryAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk endpoint /admin/categories GET.
    """
    extensionsInUse = serializers.SerializerMethodField()

    class Meta:
        model = Category
        # --- SESUAIKAN URUTAN FIELD ---
        fields = ['id', 'name', 'position', 'isPrivate', 'extensions', 'extensionsInUse']

    def get_extensionsInUse(self, obj):
        used_exts = Asset.objects.filter(category=obj, is_trashed=False).values_list('extension', flat=True).distinct()
        return list(used_exts)


class CategoryCreateAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk endpoint /admin/categories POST.
    """

    class Meta:
        model = Category
        fields = ['name', 'extensions']


class EnvironmentConfigAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentConfig
        fields = ['allowedExtensions', 'isAllowedExtensionsEnabled']
        # Ganti nama field untuk mencocokan API CKBox
        field_mappings = {
            'allowed_extensions': 'allowedExtensions',
            'is_allowed_extensions_enabled': 'isAllowedExtensionsEnabled'
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ganti nama key di output JSON
        data['allowedExtensions'] = data.pop('allowed_extensions')
        data['isAllowedExtensionsEnabled'] = data.pop('is_allowed_extensions_enabled')
        return data


class ImageQualityConfigSerializer(serializers.ModelSerializer):
    """
    Serializer untuk mengembalikan konfigurasi gambar tanpa kunci 'configs'.
    """

    class Meta:
        model = ImageQualityConfig
        fields = []  # Tidak perlu mendefinisikan fields karena kita menimpa representasi

    def to_representation(self, instance):
        """
        Menimpa metode untuk mengembalikan dictionary 'configs' secara langsung.
        """
        # instance.configs adalah field JSONField di model
        return instance.configs if instance.configs else {}


class WorkspaceGroupAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk endpoint /api/admin/groups
    - bisa untuk list, create, update
    - workspace diambil dari query param, jadi tidak dikirim di body
    """
    isDefault = serializers.BooleanField(source='is_default', required=False)

    class Meta:
        model = WorkspaceGroup
        fields = ['id', 'name', 'isDefault']


class GroupCreateAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk POST /admin/groups.
    """
    name = serializers.CharField(write_only=True)
    workspace_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = WorkspaceGroup
        fields = ['name', 'workspace_id']

    def create(self, validated_data):
        name = validated_data.pop('name')
        workspace_id = validated_data.pop('workspace_id')
        django_group = DjangoGroup.objects.create(name=name)
        workspace_group = WorkspaceGroup.objects.create(
            group=django_group,
            workspace_id=workspace_id
        )
        return workspace_group
