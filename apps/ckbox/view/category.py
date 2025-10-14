from rest_framework import viewsets, status, permissions
from ..models import Category
from ..serializer.category import CategorySerializer
from ..permissions import IsSuperAdmin, IsWorkspaceMember, IsWorkspaceOwner
from ..pagination import CustomPagination


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