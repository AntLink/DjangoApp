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
