# myapp/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse

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

    @action(detail=False, methods=['post'], url_path='login')
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

    @action(detail=False, methods=['post'], url_path='token-refresh')
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

    @action(detail=False, methods=['post'], url_path='authorize-private-access')
    def authorizeprivateaccess(self, request):
        """
        Membuat dan mengatur cookie autentikasi CKBox.
        Payload token diambil dari database menggunakan serializer.
        """
        # 1. Buat instance serializer dengan request
        auth_serializer = CKBoxAuthSerializer(request)

        # 2. Dapatkan payload dari serializer
        payload = auth_serializer.get_payload()

        # 3. Encode payload menjadi JWT
        token = jwt.encode(payload, settings.CKBOX_SECRET, algorithm="HS256")

        # 4. Buat response dan atur cookie
        response = HttpResponse(status=status.HTTP_204_NO_CONTENT)
        response.set_cookie(
            key="CKBox-Auth",
            value=token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Strict",
        )
        return response

    @action(detail=False, methods=['get'], url_path='permissions')
    def permissions(self, request):
        """
        Get permissions for the current user across all accessible workspaces and categories.
        """
        user = request.user

        # 1. Dapatkan workspace yang dimiliki user (role: owner)
        owned_workspaces = Workspace.objects.filter(owner=user)

        # 2. Dapatkan workspace di mana user adalah anggota (role: member)
        #    Ini akan termasuk workspace yang dimilikinya juga, jadi kita perlu filter nanti
        member_workspaces = user.workspaces.all()

        # 3. Buat peta peran user di setiap workspace
        user_roles = {}

        # Tandai semua workspace yang dimiliki sebagai 'owner'
        for ws in owned_workspaces:
            user_roles[str(ws.id)] = 'owner'

        # Tandai workspace lain di mana user adalah anggota sebagai 'member'
        for ws in member_workspaces:
            ws_id = str(ws.id)
            # Hanya tambahkan jika workspace ini belum ditandai sebagai 'owner'
            if ws_id not in user_roles:
                user_roles[ws_id] = 'member'

        # Jika user tidak ada di workspace manapun, kembalikan respons kosong
        if not user_roles:
            return Response({})

        # 4. Dapatkan semua kategori dari workspace-workspace tersebut
        categories = Category.objects.filter(workspace_id__in=user_roles.keys())

        # 5. Definisikan set izin
        OWNER_PERMISSIONS = {
            "category:access": True,
            "asset:create": True,
            "asset:delete": True,
            "asset:metadata:modify": True,
            "asset:overwrite": True,
            "folder:create": True,
            "folder:delete": True,
            "folder:metadata:modify": True
        }

        MEMBER_PERMISSIONS = {
            "category:access": True,
            "asset:create": True,
            "asset:delete": True,
            "asset:metadata:modify": True,
            "asset:overwrite": True,
            "folder:create": True,
            "folder:delete": True,
            "folder:metadata:modify": True
        }

        permissions_data = {}

        # 6. Bangun data izin untuk setiap kategori
        for category in categories:
            workspace_id = str(category.workspace_id)
            category_id = str(category.id)

            role = user_roles.get(workspace_id)

            if role == 'owner':
                permissions_data[category_id] = OWNER_PERMISSIONS
            else:  # role == 'member'
                permissions_data[category_id] = MEMBER_PERMISSIONS

        return Response(permissions_data)

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

# class CustomTokenObtainPairView(TokenObtainPairView):
#     """
#     View kustom yang menggunakan serializer kita.
#     """
#     serializer_class = CustomTokenObtainPairSerializer


# class WorkspaceGroupViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet untuk mengelola grup dalam sebuah workspace.
#     Hanya owner workspace yang bisa mengakses.
#     """
#     serializer_class = WorkspaceGroupSerializer
#     permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner]
#
#     def get_queryset(self):
#         workspace_id = self.request.query_params.get('workspaceId')
#         if workspace_id:
#             return WorkspaceGroup.objects.filter(workspace_id=workspace_id)
#         return WorkspaceGroup.objects.none()
#
#     def perform_create(self, serializer):
#         workspace_id = self.request.query_params.get('workspaceId')
#         if workspace_id:
#             serializer.save(workspace_id=workspace_id)
#         else:
#             raise serializers.ValidationError("workspaceId is required.")
