from rest_framework import permissions, viewsets, status
from rest_framework.views import APIView
from ..models import *
from ..serializer.admin import *
from ..permissions import IsWorkspaceMember, IsWorkspaceOwner
from ..pagination import CustomPagination

from rest_framework.decorators import action
from rest_framework.response import Response
class AdminCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk mengelola kategori bagi admin workspace.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner]
    pagination_class = CustomPagination
    def get_queryset(self):
        workspace_id = self.request.query_params.get('workspaceId')
        if workspace_id:
            return Category.objects.filter(workspace_id=workspace_id).order_by('position')
        return Category.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return CategoryCreateAdminSerializer
        return CategoryAdminSerializer

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Dipanggil saat category baru dibuat.
        1. Menyimpan kategori ke workspace yang benar.
        2. Membuat permission default untuk grup default di workspace.
        """
        # 1. Dapatkan workspace dari query parameter
        workspace_id = self.request.query_params.get('workspaceId')
        if not workspace_id:
            raise serializers.ValidationError("workspaceId query parameter is required.")

        try:
            from .models import Workspace
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            raise serializers.ValidationError(f"Workspace with id '{workspace_id}' not found.")

        # 2. Simpan kategori dengan workspace
        category = serializer.save(workspace=workspace)

        # 3. Cari grup default di workspace yang sama
        default_group = WorkspaceGroup.objects.filter(
            workspace=category.workspace,
            is_default=True
        ).first()

        # 4. Jika grup default ditemukan, buat permission baru
        if default_group:
            default_permissions = {
                'category:access': True,
                'asset:create': True,
                'asset:read': True,
                'asset:delete': False,
                'asset:metadata:modify': False,
                'asset:overwrite': False,
                'folder:create': False,
                'folder:delete': False,
                'folder:metadata:modify': False,
            }

            Permission.objects.create(
                group=default_group,
                permissions_list=default_permissions
            ).categories.add(category)

    @action(detail=False, methods=['put'], url_path='order')
    def set_order(self, request, *args, **kwargs):
        """Endpoint untuk /admin/categories/order"""
        category_ids = request.data
        if not isinstance(category_ids, list):
            return Response({"detail": "Invalid payload. Expected a list of IDs."}, status=status.HTTP_400_BAD_REQUEST)

        for index, cat_id in enumerate(category_ids):
            Category.objects.filter(pk=cat_id, workspace__memberships__user=request.user).update(position=index)

        return Response(status=status.HTTP_204_NO_CONTENT)

class AdminEnvironmentConfigView(APIView):
    """
    Endpoint GET untuk /admin/environmentConfig.
    Ini membaca konfigurasi global yang sama dengan superadmin.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner,IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        config, _ = EnvironmentConfig.objects.get_or_create(pk=1)
        serializer = EnvironmentConfigAdminSerializer(config)
        return Response(serializer.data)

class AdminImageViewSet(viewsets.GenericViewSet):
    """
    ViewSet untuk mengelola konfigurasi gambar.
    Endpoint: GET /admin/images, PUT /admin/images/{format}
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner]
    serializer_class = ImageQualityConfigSerializer
    pagination_class = None

    def get_object(self):
        obj, _ = ImageQualityConfig.objects.get_or_create(pk=1)
        return obj

    def list(self, request, *args, **kwargs):
        """
        Endpoint GET untuk /admin/images
        """
        config = self.get_object()
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    # --- KEMBALIKAN MENGGUNAKAN @action ---
    @action(detail=False, methods=['put'], url_path='(?P<frm>[a-z]+)')
    def update_quality(self, request, frm, *args, **kwargs):  # <-- UBAH 'format' MENJADI 'frm'
        """
        Endpoint PUT untuk /admin/images/{format}
        """
        config = self.get_object()

        # Validasi input
        quality = request.data.get('defaultQuality')
        if quality is None:
            return Response(
                {"detail": "'defaultQuality' must be provided in the payload."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quality = int(quality)
            if not 1 <= quality <= 100:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"detail": "'defaultQuality' must be an integer between 1 and 100."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update konfigurasi
        configs = config.configs
        # Gunakan variabel 'frm' di sini
        configs[frm] = {'defaultQuality': quality}
        config.configs = configs
        config.save()

        # Kembalikan seluruh konfigurasi yang sudah diperbarui
        serializer = self.get_serializer(config)
        return Response(serializer.data)

class AdminGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk mengelola grup bagi admin workspace.
    Contoh:
      - GET  /api/admin/groups?workspaceId=<uuid>
      - POST /api/admin/groups?workspaceId=<uuid>
      - PATCH /api/admin/groups/<group_id>/?workspaceId=<uuid>
    """
    serializer_class = WorkspaceGroupAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner]
    pagination_class = CustomPagination

    def get_queryset(self):
        workspace_id = self.request.query_params.get('workspaceId')
        if not workspace_id:
            return WorkspaceGroup.objects.none()
        return WorkspaceGroup.objects.filter(workspace_id=workspace_id)

    def perform_create(self, serializer):
        workspace_id = self.request.query_params.get('workspaceId')
        if not workspace_id:
            raise serializers.ValidationError({"workspaceId": "Query parameter workspaceId is required."})
        serializer.save(workspace_id=workspace_id)

    def perform_update(self, serializer):
        """
        Pastikan update hanya bisa dilakukan dalam konteks workspaceId yang benar.
        """
        workspace_id = self.request.query_params.get('workspaceId')
        if not workspace_id:
            raise serializers.ValidationError({"workspaceId": "Query parameter workspaceId is required."})

        # instance = self.get_object()
        # if str(instance.workspace_id) != workspace_id:
        #     raise serializers.ValidationError({"detail": "This group does not belong to the specified workspace."})

        serializer.save()