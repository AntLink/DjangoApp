from rest_framework import permissions

from ..serializer.folder import FolderSerializer, FolderCreateSerializer
from ..permissions import IsWorkspaceMember
from ..models import Asset, Folder
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status

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


    def perform_destroy(self, instance):
        """
        Override perform_destroy untuk memindahkan semua aset di dalam folder
        dan subfoldernya ke trash, serta mengubah category_id-nya ke kategori
        dari folder yang dihapus.
        """
        # 1. Dapatkan ID kategori dari folder yang akan dihapus
        #    Gunakan .category_id untuk menghindari error jika kategori tidak ada (None)
        # target_category_id = instance.category_id

        # 2. Dapatkan semua ID folder yang akan terpengaruh
        folder_ids_to_trash = self._get_all_folder_ids(instance)

        if folder_ids_to_trash:
            # 3. Persiapkan data untuk update
            update_data = {
                'is_trashed': True,
            }

            # Hanya update category_id jika folder induk memiliki kategori
            # if target_category_id:
            #     update_data['category_id'] = target_category_id

            # 4. Pindahkan semua aset di dalam folder-folder tersebut ke trash
            #    dan ubah kategorinya dalam satu operasi database yang efisien
            updated_count = Asset.objects.filter(
                folder_id__in=folder_ids_to_trash
            ).update(**update_data)

            print(f"Moved {updated_count} assets to trash and updated their category from folder {instance.name} and its subfolders.")

        # 5. Lanjutkan proses penghapusan folder itu sendiri
        super().perform_destroy(instance)

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        folder = serializer.save()  # Ini akan mengembalakan instance Folder

        # Di sini kamu bisa sesuaikan responsnya:
        # - Jika CKBox mengharapkan field "id" dengan format tertentu, ubah di sini.
        #   Misalnya kalau ingin respons hanya seperti {"id": "<uuid>"}:
        return Response({"id": str(folder.id)}, status=status.HTTP_201_CREATED)

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

    def _get_all_folder_ids(self, folder):
        """
        Metode helper untuk mendapatkan ID folder dan semua subfoldernya secara rekursif.
        """
        ids = [str(folder.id)]
        # Gunakan prefetch_related untuk efisiensi jika sudah di-get_queryset
        for child in folder.children.all():
            ids.extend(self._get_all_folder_ids(child))
        return ids

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
