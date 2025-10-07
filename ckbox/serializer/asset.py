# assets/serializers.py

import os
from rest_framework import serializers
from ..models import Asset, Workspace, Category, Folder

class AssetDeleteSerializer(serializers.Serializer):
    """Serializer untuk menerima daftar ID aset yang akan dihapus permanen."""
    ids = serializers.ListField(child=serializers.CharField())

class ImageTransformationsSerializer(serializers.Serializer):
    """Serializer untuk berbagai jenis transformasi gambar."""
    crop = serializers.DictField(child=serializers.IntegerField(), required=False)
    resize = serializers.DictField(child=serializers.IntegerField(), required=False)
    rotate = serializers.DictField(child=serializers.IntegerField(), required=False)
    flip = serializers.DictField(child=serializers.BooleanField(), required=False)

class EditImageSerializer(serializers.Serializer):
    """Serializer untuk payload endpoint editImage."""
    action = serializers.ChoiceField(choices=['create', 'replace'])
    assetName = serializers.CharField(max_length=255)
    transformations = ImageTransformationsSerializer()

class NamesExistTargetSerializer(serializers.Serializer):
    """Serializer untuk objek 'target' dalam payload namesExist."""
    folderId = serializers.UUIDField(required=False)
    categoryId = serializers.UUIDField(required=False)

    def validate(self, data):
        # Pastikan hanya salah satu (folderId atau categoryId) yang ada
        if not data.get('folderId') and not data.get('categoryId'):
            raise serializers.ValidationError("Either folderId or categoryId must be provided.")
        if data.get('folderId') and data.get('categoryId'):
            raise serializers.ValidationError("Provide either folderId or categoryId, not both.")
        return data

class NamesExistSerializer(serializers.Serializer):
    """Serializer utama untuk payload endpoint namesExist."""
    target = NamesExistTargetSerializer()
    names = serializers.ListField(child=serializers.CharField())

class RestoreValidateSerializer(serializers.Serializer):
    assetsIds = serializers.ListField(child=serializers.CharField())

class TargetSerializer(serializers.Serializer):
    """Serializer untuk objek 'target'."""
    folderId = serializers.UUIDField(required=False)
    categoryId = serializers.UUIDField(required=False)

    def validate(self, data):
        if not data.get('folderId') and not data.get('categoryId'):
            raise serializers.ValidationError("Either folderId or categoryId must be provided.")
        if data.get('folderId') and data.get('categoryId'):
            raise serializers.ValidationError("Provide either folderId or categoryId, not both.")
        return data

class RestoreAssetActionSerializer(serializers.Serializer):
    """Serializer untuk satu objek aksi pemulihan. Target bersifat opsional."""
    assetId = serializers.CharField()
    # --- PERUBAHAN DI SINI ---
    # Jadikan target opsional dengan required=False
    target = TargetSerializer(required=False, allow_null=True)

class AssetRestoreSerializer(serializers.Serializer):
    """Serializer untuk payload utama endpoint restore."""
    assetsActions = RestoreAssetActionSerializer(many=True)

# --- Serializer untuk Membuat Aset (POST /assets) ---
class AssetCreateSerializer(serializers.ModelSerializer):
    """Hanya untuk menangani pembuatan aset baru."""
    class Meta:
        model = Asset
        fields = ['file', 'categoryId', 'folderId'] # Field yang diterima dari form-data

    categoryId = serializers.UUIDField(write_only=True, required=False)
    folderId = serializers.UUIDField(write_only=True, required=False)

    def validate(self, data):
        # Pastikan hanya salah satu (categoryId atau folderId) yang ada
        if data.get('categoryId') and data.get('folderId'):
            raise serializers.ValidationError("Provide either categoryId or folderId, not both.")
        return data

# --- Serializer untuk Membaca Aset (GET /assets, /assets/{id}) ---
class AssetSerializer(serializers.ModelSerializer):
    """Serializer utama untuk output data aset yang sesuai dengan format CKBox."""
    id = serializers.CharField()
    url = serializers.SerializerMethodField()
    imageUrls = serializers.SerializerMethodField()
    mimeType = serializers.CharField(source='mime_type')
    categoryId = serializers.UUIDField(source='category.id', allow_null=True)
    folderId = serializers.UUIDField(source='folder.id', allow_null=True)
    uploadedAt = serializers.DateTimeField(source='uploaded_at', format='%Y-%m-%dT%H:%M:%SZ')
    lastModifiedAt = serializers.DateTimeField(source='last_modified_at', format='%Y-%m-%dT%H:%M:%SZ')

    class Meta:
        model = Asset
        fields = [
            'id', 'tags', 'name', 'extension', 'url', 'imageUrls',
            'size', 'mimeType', 'categoryId', 'folderId', 'uploadedAt',
            'lastModifiedAt', 'metadata'
        ]

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    def get_imageUrls(self, obj):
        # **Poin Penting**: Ambil dari metadata yang telah diproses oleh Celery
        return obj.metadata.get('imageUrls', {})

# --- Serializer untuk Memperbarui Aset (PATCH /assets/{id}) ---

class AssetUpdateSerializer(serializers.ModelSerializer):
    """Untuk memperbarui data aset (nama, ekstensi, metadata, tags)."""

    class Meta:
        model = Asset
        fields = ['name', 'extension', 'metadata', 'tags']

    def update(self, instance, validated_data):
        """
        Override metode update untuk menggabungkan metadata
        alih-alih menimpanya.
        """
        # 1. Ambil data metadata baru dari request, lalu hapus dari validated_data
        new_metadata = validated_data.pop('metadata', None)

        # 2. Jika ada metadata baru dalam request
        if new_metadata:
            # Buat salinan metadata lama dari instance untuk diubah
            merged_metadata = instance.metadata.copy()

            # 3. Gabungkan (merge) metadata baru ke dalam metadata lama
            #    - Key baru akan ditambahkan.
            #    - Key yang sudah ada akan nilainya diperbarui.
            merged_metadata.update(new_metadata)

            # 4. Masukkan kembali metadata yang sudah digabung ke validated_data
            validated_data['metadata'] = merged_metadata

        # 5. Lanjutkan proses update seperti biasa dengan data yang sudah digabung
        return super().update(instance, validated_data)

# --- Serializer untuk Memperbarui Metadata (PATCH /assets/{id}/metadata) ---
class AssetMetadataUpdateSerializer(serializers.Serializer):
    """Khusus untuk endpoint metadata."""
    description = serializers.CharField(required=False, allow_blank=True)
    customAttributes = serializers.JSONField(required=False, default=dict)

# --- Serializer untuk Aksi Massal ---
class AssetBulkActionSerializer(serializers.Serializer):
    """Serializer untuk menerima array ID aset."""
    ids = serializers.ListField(child=serializers.UUIDField())

class CategoryTargetSerializer(serializers.Serializer):
    categoryId = serializers.UUIDField()

class FolderTargetSerializer(serializers.Serializer):
    folderId = serializers.UUIDField()

class AssetNamesExistSerializer(serializers.Serializer):
    target = serializers.DictField(child=serializers.UUIDField())
    names = serializers.ListField(child=serializers.CharField())