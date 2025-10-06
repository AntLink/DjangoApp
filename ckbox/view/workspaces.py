from rest_framework import viewsets, status, permissions
from ..models import Workspace
from ..serializer.workspaces import WorkspaceSerializer
from ..permissions import IsSuperAdmin, IsWorkspaceMember, IsWorkspaceOwner
from ..pagination import CustomPagination
from rest_framework.response import Response

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
