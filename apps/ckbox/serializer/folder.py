from rest_framework import serializers
from ..models import Folder, Workspace, Category
from ..serializers import UserSerializer
from django.shortcuts import get_object_or_404


class FolderSerializer(serializers.ModelSerializer):
    folders = serializers.SerializerMethodField()
    assets_count = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'created_at', 'updated_at',
            'category_id', 'parent_id', 'folders',
            'assets_count', 'created_by','parent', 'children'
        ]

    def get_children(self, obj):
        children = obj.children.all()
        return FolderSerializer(children, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'name': data['name'],
            'createdAt': data['created_at'],
            'updatedAt': data['updated_at'],
            'categoryId': data['category_id'],
            'parentId': data['parent_id'],
            'folders': data['folders'],
            'assetsCount': data['assets_count'],
            'createdBy': data['created_by']
        }

    def get_folders(self, obj):
        # Karena `children` sudah di-prefetch, ini akan sangat cepat
        children = obj.children.all()
        return FolderSerializer(children, many=True, context=self.context).data

    def get_assets_count(self, obj):
        return obj.assets.filter(is_trashed=False).count()

class FolderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer fleksibel untuk membuat folder baru:
    - Jika `categoryId` diberikan → folder root.
    - Jika `parentId` diberikan → subfolder.
    """
    parentId = serializers.UUIDField(write_only=True, required=False)
    categoryId = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Folder
        fields = ['name', 'parentId', 'categoryId']

    def validate(self, attrs):
        """
        Validasi input dasar — salah satu dari categoryId atau parentId harus ada.
        """
        parent_id = attrs.get('parentId')
        category_id = attrs.get('categoryId')

        if not parent_id and not category_id:
            raise serializers.ValidationError({
                "detail": "Either 'categoryId' or 'parentId' must be provided."
            })

        return attrs

    def create(self, validated_data):
        """
        Logika utama untuk membuat folder baru.
        """
        request = self.context['request']
        user = request.user
        workspace_id = request.query_params.get('workspaceId')

        if not workspace_id:
            raise serializers.ValidationError({
                "detail": "workspaceId query parameter is required."
            })

        # --- Cek workspace ---
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            raise serializers.ValidationError({
                "detail": f"Workspace with id '{workspace_id}' not found."
            })

        parent_id = validated_data.get('parentId')
        category_id = validated_data.get('categoryId')
        name = validated_data['name']

        # --- CASE 1: Membuat subfolder ---
        if parent_id:
            parent_folder = get_object_or_404(Folder, id=parent_id, workspace=workspace)

            # Warisi kategori dari parent
            category = parent_folder.category

            # Validasi permission
            if parent_folder.workspace.owner != user:
                raise PermissionDenied("You do not have permission to create a subfolder here.")

            folder = Folder.objects.create(
                name=name,
                workspace=workspace,
                parent=parent_folder,
                category=category,
                created_by=user
            )

        # --- CASE 2: Membuat folder di bawah kategori ---
        elif category_id:
            category = get_object_or_404(Category, id=category_id, workspace=workspace)

            folder = Folder.objects.create(
                name=name,
                workspace=workspace,
                category=category,
                created_by=user
            )

        return folder
