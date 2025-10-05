# myapp/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.core.files.base import ContentFile
import io
from PIL import Image

from .models import *
from .serializers import *
from .permissions import IsSuperAdmin, IsWorkspaceMember, IsWorkspaceOwner
from .pagination import CustomPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Prefetch

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet untuk autentikasi dan otorisasi CKBox
    """
    permission_classes = [AllowAny]  # ubah agar bisa login tanpa token

    @action(detail=False, methods=['get'])
    def limits(self, request):
        data = {
            "maxImageInMegapixelsLimit": 50,
            "maxFileSizeInBytesLimit": 50000000,
            "pricingPlanName": "ckbox.pro",
            "isMaxBandwidthExceeded": False,
            "isMaxStorageSizeExceeded": False
        }
        return Response(data)

    @action(detail=False, methods=['post'])
    def ckbox_login(self, request):
        """
        Endpoint login CKBox: menghasilkan access dan refresh token
        """
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Gunakan custom serializer untuk CKBox
        refresh = CKBoxTokenObtainPairSerializer.get_token(user)
        access_token = refresh.access_token

        access_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
        refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

        return Response({
            'refresh': str(refresh),
            'access': str(access_token),
            'access_token_lifetime': int(access_lifetime.total_seconds()),
            'refresh_token_lifetime': int(refresh_lifetime.total_seconds()),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })

    @action(detail=False, methods=['post'])
    def ckbox_token_refresh(self, request):
        """
        Refresh token CKBox — hasilkan access baru dengan claim CKBox
        """
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            user = User.objects.get(id=user_id)

            # Gunakan serializer yang sama untuk regenerate token dengan CKBox claim
            new_refresh = CKBoxTokenObtainPairSerializer.get_token(user)
            new_access = new_refresh.access_token

            access_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
            refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

            return Response({
                'refresh': str(new_refresh),
                'access': str(new_access),
                'access_token_lifetime': int(access_lifetime.total_seconds()),
                'refresh_token_lifetime': int(refresh_lifetime.total_seconds()),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View kustom yang menggunakan serializer kita.
    """
    serializer_class = CustomTokenObtainPairSerializer

class WorkspaceGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk mengelola grup dalam sebuah workspace.
    Hanya owner workspace yang bisa mengakses.
    """
    serializer_class = WorkspaceGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner]

    def get_queryset(self):
        workspace_id = self.request.query_params.get('workspaceId')
        if workspace_id:
            return WorkspaceGroup.objects.filter(workspace_id=workspace_id)
        return WorkspaceGroup.objects.none()

    def perform_create(self, serializer):
        workspace_id = self.request.query_params.get('workspaceId')
        if workspace_id:
            serializer.save(workspace_id=workspace_id)
        else:
            raise serializers.ValidationError("workspaceId is required.")

class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk mengelola aturan permission.
    Hanya owner workspace yang bisa mengakses.
    """
    serializer_class = PermissionSerializer # Pastikan menggunakan serializer yang baru
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner]
    pagination_class = None # Nonaktifkan pagination untuk mencocokan respons yang Anda inginkan

    def get_queryset(self):
        workspace_id = self.request.query_params.get('workspaceId')
        if workspace_id:
            return Permission.objects.filter(group__workspace_id=workspace_id).prefetch_related('categories')
        return Permission.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"items": serializer.data}) # Membungkus dengan 'items'

class AssetViewSet(viewsets.ModelViewSet):
    serializer_class = AssetSerializer
    parser_classes = [MultiPartParser, FormParser]

    pagination_class = CustomPagination

    # def get_serializer_class(self):
    #     if self.action in ['list', 'recent', 'trash', 'retrieve']:
    #         return AssetListSerializer
    #     return AssetSerializer

    def get_queryset(self):
        """
        Filter aset berdasarkan query parameter.
        """
        user = self.request.user
        queryset = Asset.objects.filter(workspace__memberships__user=user, is_trashed=False)

        # --- Filter berdasarkan folderId ---
        folder_id = self.request.query_params.get('folderId')
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)

        # Filter berdasarkan kategori (opsional)
        category_id = self.request.query_params.get('categoryId')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Update last_used_at
        RecentAsset.objects.update_or_create(user=request.user, asset=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def trash(self, request, *args, **kwargs):
        asset_ids = request.data.get('asset_ids', [])
        if not asset_ids:
            return Response({"detail": "asset_ids field is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update last_used_at
        RecentAsset.objects.filter(asset_id__in=asset_ids, user=request.user).delete()

        count = Asset.objects.filter(id__in=asset_ids, workspace__memberships__user=request.user).update(is_trashed=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='trash')
    def get_trashed_assets(self, request, *args, **kwargs):
        """
        Mengembalikan daftar aset yang ada di trash bin (GET).
        Endpoint: GET /api/assets/trash/
        """
        # 1. Filter aset yang di-trash dan milik user
        queryset = Asset.objects.filter(
            is_trashed=True,
            workspace__memberships__user=request.user
        )

        # 2. (Opsional) Terapkan filter tambahan seperti workspaceId
        workspace_id = request.query_params.get('workspaceId')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)

        # 3. Terapkan pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # 4. Jika pagination tidak diatur, kembalikan semua data
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def restore(self, request, *args, **kwargs):
        asset_ids = request.data.get('asset_ids', [])
        if not asset_ids:
            return Response({"detail": "asset_ids field is required."}, status=status.HTTP_400_BAD_REQUEST)

        count = Asset.objects.filter(id__in=asset_ids, workspace__memberships__user=request.user, is_trashed=True).update(is_trashed=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def delete(self, request, *args, **kwargs):
        """Permanent delete for trashed items."""
        asset_ids = request.data.get('asset_ids', [])
        if not asset_ids:
            return Response({"detail": "asset_ids field is required."}, status=status.HTTP_400_BAD_REQUEST)

        assets_to_delete = Asset.objects.filter(id__in=asset_ids, workspace__memberships__user=request.user, is_trashed=True)

        # Delete files from storage
        for asset in assets_to_delete:
            asset.file.delete(save=False)

        count, _ = assets_to_delete.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path=r'thumbs/(?P<dimensions>[\dx]+)')
    def thumbs(self, request, pk=None, dimensions=None):
        """
        Mengambil thumbnail gambar dengan ukuran tertentu.
        Format ditentukan via query parameter 'format'.
        Contoh URL: /api/assets/{asset-id}/thumbs/200x200?format=webp
        """
        asset = self.get_object()
        if not asset.mime_type.startswith('image/'):
            return Response({"detail": "Asset is not an image."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Parsing dimensi dari URL
        try:
            if 'x' in dimensions:
                width, height = map(int, dimensions.split('x'))
            else:
                width = int(dimensions)
                height = None
        except ValueError:
            return Response({"detail": "Invalid dimensions format. Use 'width' or 'widthxheight'."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Ambil format dari query parameter, default ke 'webp'
        image_format = request.query_params.get('format', 'webp').lower()

        try:
            img = Image.open(asset.file)

            # Resize gambar
            if height:
                img.thumbnail((width, height))
            else:
                img.thumbnail((width, img.height))

            buffer = io.BytesIO()

            # 3. Handling format
            if image_format in ('jpg', 'jpeg'):
                img_save_format, mime = 'JPEG', 'image/jpeg'
            elif image_format == 'png':
                img_save_format, mime = 'PNG', 'image/png'
            elif image_format == 'webp':
                img_save_format, mime = 'WEBP', 'image/webp'
            else:
                return Response({"detail": f"Unsupported format: {image_format}. Supported formats are jpg, jpeg, png, webp."}, status=status.HTTP_400_BAD_REQUEST)

            img.save(buffer, format=img_save_format)
            buffer.seek(0)

            # 4. Kembalikan file gambar sebagai HttpResponse
            return HttpResponse(buffer.getvalue(), content_type=mime)

        except Exception as e:
            return Response({"detail": f"Error processing image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # --- PERBAIKAN: METODE INI SEKARANG SEJAJAR DENGAN YANG LAIN ---
    # @action(detail=True, methods=['get'], url_path=r'thumbs/(?P<dimensions>[\dx]+)\.(?P<frm>[a-zA-Z0-9]+)')
    # def thumbs(self, request, pk=None, dimensions=None, format=None):
    #     """
    #     Mengambil thumbnail gambar dengan ukuran dan format tertentu.
    #     Contoh URL: /api/assets/{asset-id}/thumbs/200x200.webp
    #     """
    #     asset = self.get_object()
    #     if not asset.mime_type.startswith('image/'):
    #         return Response({"detail": "Asset is not an image."}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     # parsing dimensi
    #     try:
    #         if 'x' in dimensions:
    #             width, height = map(int, dimensions.split('x'))
    #         else:
    #             width = int(dimensions)
    #             height = None
    #     except ValueError:
    #         return Response({"detail": "Invalid dimensions format. Use 'width' or 'widthxheight'."}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     try:
    #         img = Image.open(asset.file)
    #
    #         # resize
    #         if height:
    #             img.thumbnail((width, height))
    #         else:
    #             img.thumbnail((width, img.height))
    #
    #         buffer = io.BytesIO()
    #
    #         # format handling
    #         fmt = format.lower()
    #         if fmt in ('jpg', 'jpeg'):
    #             img_format, mime = 'JPEG', 'image/jpeg'
    #         elif fmt == 'png':
    #             img_format, mime = 'PNG', 'image/png'
    #         elif fmt == 'webp':
    #             img_format, mime = 'WEBP', 'image/webp'
    #         else:
    #             return Response({"detail": f"Unsupported format: {format}"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #         img.save(buffer, format=img_format)
    #         buffer.seek(0)
    #
    #         return HttpResponse(buffer.getvalue(), content_type=mime)
    #
    #     except Exception as e:
    #         return Response({"detail": f"Error processing image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = CustomPagination
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        workspace_id = self.request.query_params.get('workspaceId')
        if workspace_id:
            return Category.objects.filter(workspace_id=workspace_id, workspace__memberships__user=user)
        return Category.objects.none()


class FolderViewSet(viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    def get_queryset(self):
        user = self.request.user
        workspace_id = self.request.query_params.get('workspaceId')
        if workspace_id:
            return Folder.objects.filter(
                workspace_id=workspace_id,
                parent__isnull=True,
                is_trashed=False
            ).select_related('workspace', 'category', 'parent').prefetch_related(
                'children__children__children',
                'children__category',
                'children__workspace',
            )
        return Folder.objects.none()

    def retrieve(self, request, *args, **kwargs):
        """
        Method ini dipanggil untuk GET /folders/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'create':
            return FolderCreateSerializer
        return FolderSerializer



    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"items": serializer.data})

    def perform_create(self, serializer):
        serializer.save()

    def get_object(self):
        # Menggunakan get_object_or_404 untuk pesan error yang lebih baik
        obj = get_object_or_404(Folder, pk=self.kwargs['pk'])
        return obj



    @action(detail=True, methods=['get'], url_path='branch')
    def branch(self, request, pk=None, depth=1):
        """
        Mengembalikan jalur folder dari root ke folder ini, plus anak-anaknya.
        Query Parameters:
        - depth: (int) Kedalaman anak-anak folder yang akan ditampilkan. Default 1.
        """
        # 1. Ambil folder target
        folder = self.get_object()

        # 2. Bangun jalur dari root ke folder target
        path_to_root = folder.get_path()

        # 3. Ambil anak-anak folder hingga kedalaman tertentu
        children_at_depth = self._get_children_at_depth(folder, depth)

        # 4. Gabungkan jalur dan anak-anak
        # Penting: anak-anak dari folder target tidak boleh duplikasi dengan folder itu sendiri
        final_list = path_to_root + [f for f in children_at_depth if f != folder]

        # 5. Serialisasi dan kembalikan response
        serializer = FolderSerializer(final_list, many=True, context={'request': request})
        return Response({"items": serializer.data})

    def _get_children_at_depth(self, folder, depth):
        """
        Method helper untuk mengambil anak-anak folder secara rekursif hingga kedalaman tertentu.
        """
        if depth <= 0:
            return []

        children = folder.children.filter(is_trashed=False)
        result = list(children)

        if depth > 1:
            for child in children:
                result.extend(self._get_children_at_depth(child, depth - 1))

        return result

class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return self.request.user.workspaces.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "items": serializer.data
        })

class RecentAssetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecentAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RecentAsset.objects.filter(user=self.request.user).select_related('asset')

class UserPermissionsView(APIView):
    """
    Mengembalikan peta perizinan untuk setiap kategori di sebuah workspace.
    Endpoint: GET /api/permissions?workspaceId=...
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response({"detail": "workspaceId query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workspace = Workspace.objects.get(id=workspace_id, memberships__user=request.user)
        except Workspace.DoesNotExist:
            return Response({"detail": "Workspace not found or you are not a member."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Ambil semua kategori di workspace ini
        categories = workspace.categories.all()

        # 2. Ambil semua WorkspaceGroup di workspace ini
        workspace_groups = WorkspaceGroup.objects.filter(workspace=workspace)

        # 3. Ambil semua permission rules yang terkait dengan WorkspaceGroup tersebut
        permission_rules = Permission.objects.filter(
            group__in=workspace_groups
        ).prefetch_related('categories')

        # 4. Buat peta perizinan berdasarkan workspace
        workspace_permissions_map = {}

        # Inisialisasi semua kategori dengan permission kosong
        for category in categories:
            workspace_permissions_map[str(category.id)] = {}

        # Isi peta perizinan dari semua permission rules
        for rule in permission_rules:
            for category in rule.categories.all():
                if str(category.id) in workspace_permissions_map:
                    # Gabungkan perizinan (union). Jika salah satu rule memberi izin, maka izin tersebut aktif.
                    for perm, value in rule.permissions_list.items():
                        if value:  # Hanya tambahkan jika izinnya True
                            workspace_permissions_map[str(category.id)][perm] = True

        return Response(workspace_permissions_map)

# --- Superadmin Views ---
class SuperadminEnvironmentConfigView(APIView):
    permission_classes = [IsAdminUser,IsAuthenticated]

    def get(self, request, format=None):
        config, _ = EnvironmentConfig.objects.get_or_create(pk=1)
        serializer = EnvironmentConfigSerializer(config)
        return Response(serializer.data)

    def put(self, request, format=None):
        """
        Update konfigurasi lingkungan global.
        Terima payload camelCase dan konversi ke snake_case.
        """
        config, _ = EnvironmentConfig.objects.get_or_create(pk=1)

        validated_data = {}
        if 'allowedExtensions' in request.data:
            validated_data['allowed_extensions'] = request.data['allowedExtensions']
        if 'isAllowedExtensionsEnabled' in request.data:
            validated_data['is_allowed_extensions_enabled'] = request.data['isAllowedExtensionsEnabled']
        if 'ckboxProjectId' in request.data:
            validated_data['ckbox_project_id'] = request.data['ckboxProjectId']

        serializer = EnvironmentConfigSerializer(config, data=validated_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SuperadminWorkspaceTemplateView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request, format=None):
        """
        Mengembalikan daftar kategori dari semua template yang digabung menjadi satu.
        """
        # Ambil semua template
        templates = WorkspaceTemplate.objects.all()

        # Gabungkan semua daftar kategori dari setiap template
        all_categories = []
        for template in templates:
            # Pastikan categories_templates adalah list sebelum menambahkannya
            if isinstance(template.categories_templates, list):
                all_categories.extend(template.categories_templates)

        return Response({"categoriesTemplates": all_categories})

    def put(self, request, format=None):
        """
        Memperbarui daftar kategori master.
        API akan menyimpan semua kategori ini ke dalam satu template default.
        """
        categories_data = request.data.get('categoriesTemplates', [])

        if not isinstance(categories_data, list):
            return Response({"detail": "Invalid payload. Expected a list of categories."}, status=status.HTTP_400_BAD_REQUEST)

        # Gunakan get_or_create untuk membuat atau memperbarui template default
        template, created = WorkspaceTemplate.objects.get_or_create(
            name="Default Template",  # Nama tetap untuk template master kita
            defaults={'categories_templates': categories_data}
        )

        # Jika template sudah ada, perbarui datanya
        if not created:
            template.categories_templates = categories_data
            template.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


# admin view
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