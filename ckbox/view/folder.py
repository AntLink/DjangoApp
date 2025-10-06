from rest_framework import permissions

from ..serializer.folder import *
from ..permissions import IsWorkspaceMember
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class FolderViewSet(viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    def get_queryset(self):
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
