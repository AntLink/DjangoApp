from rest_framework import viewsets, status, permissions
from ..models import Permission
from ..serializer.permission import PermissionSerializer
from ..permissions import IsSuperAdmin, IsWorkspaceMember, IsWorkspaceOwner
from rest_framework.response import Response


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
