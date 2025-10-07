import os
import uuid
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.conf import settings
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
import numpy as np
from io import BytesIO
from django.core.files.base import ContentFile

# Impor library untuk pemrosesan gambar
from PIL import Image as PilImage, ImageOps
from blurhash import encode

from ..models import Asset, Workspace, Category, Folder, RecentAsset
from ..serializer.asset import (
    AssetSerializer, AssetCreateSerializer, AssetUpdateSerializer, NamesExistSerializer, EditImageSerializer,
    AssetMetadataUpdateSerializer, AssetBulkActionSerializer, RestoreValidateSerializer,
    CategoryTargetSerializer, FolderTargetSerializer, AssetNamesExistSerializer, AssetRestoreSerializer,
    AssetDeleteSerializer
)


# --- Pagination Kustom ---
class CustomPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            'totalCount': self.page.paginator.count,
            'offset': (self.page.number - 1) * self.page_size,
            'limit': self.page_size,
            'items': data
        })


# --- ViewSet Utama ---
class AssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk mengelola aset, tanpa Celery (sinkron).
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = CustomPagination
    lookup_field = 'id'

    def get_queryset(self):
        """
        Filter aset berdasarkan query parameter.
        Memberikan queryset yang berbeda untuk aksi 'thumbs' agar bisa diakses publik.
        """
        # Jika aksinya adalah 'thumbs', kita tidak perlu memfilter berdasarkan user.
        # Cukup pastikan asetnya tidak ada di trash.
        # if self.action == 'thumbs':
        #     return Asset.objects.filter(is_trashed=False)

        if self.action == 'thumbs':
            return Asset.objects.all()

        # Untuk semua aksi lainnya, gunakan filter keamanan berdasarkan user.
        user = self.request.user
        queryset = Asset.objects.filter(workspace__memberships__user=user, is_trashed=False)

        # Filter berdasarkan workspaceId
        workspace_id = self.request.query_params.get('workspaceId')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)

        # Filter berdasarkan folderId
        folder_id = self.request.query_params.get('folderId')
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)

        # Filter berdasarkan kategori
        category_id = self.request.query_params.get('categoryId')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Sorting
        sort_by_param = self.request.query_params.get('sortBy', 'uploadedAt')
        order = self.request.query_params.get('order', 'desc')

        sort_mapping = {
            'name': 'name',
            'size': 'size',
            'uploadedAt': 'uploaded_at',
            'lastModifiedAt': 'last_modified_at',
        }

        sort_by_field = sort_mapping.get(sort_by_param, 'uploaded_at')
        ordering_prefix = '' if order == 'asc' else '-'
        queryset = queryset.order_by(f"{ordering_prefix}{sort_by_field}")

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return AssetCreateSerializer
        if self.action in ['list', 'retrieve', 'recent', 'trash']:
            return AssetSerializer
        if self.action == 'partial_update':
            return AssetUpdateSerializer
        return AssetSerializer

    def create(self, request, *args, **kwargs):
        """
        Upload an asset secara sinkron (tanpa Celery).
        PERINGATAN: Metode ini akan memblokir request sampai pemrosesan selesai.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        file_obj = validated_data['file']

        category_id = validated_data.get('categoryId')
        folder_id = validated_data.get('folderId')

        category = None
        folder = None
        workspace = None

        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                workspace = category.workspace
            except Category.DoesNotExist:
                return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        elif folder_id:
            try:
                folder = Folder.objects.get(id=folder_id)
                workspace = folder.workspace
            except Folder.DoesNotExist:
                return Response({"detail": "Folder not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"detail": "Either categoryId or folderId must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        if not workspace.memberships.filter(user=request.user).exists():
            return Response({"detail": "Workspace not found or you do not have access."}, status=status.HTTP_404_NOT_FOUND)

        # Ekstrak informasi file
        original_filename = file_obj.name
        name, extension = os.path.splitext(original_filename)
        extension = extension.lstrip('.').lower()
        mime_type = file_obj.content_type or 'application/octet-stream'
        size = file_obj.size

        with transaction.atomic():
            asset = Asset.objects.create(
                name=name,
                extension=extension,
                size=size,
                mime_type=mime_type,
                file=file_obj,
                workspace=workspace,
                folder=folder,
                category=category,
                uploaded_by=request.user,
                metadata={'metadataProcessingStatus': 'pending'}
            )

        # --- AWAL PROSES PEMROSESAN SINKRON ---
        # Semua kode di bawah ini akan memblokir respons hingga selesai
        try:
            file_path = asset.file.path
            asset_dir = os.path.dirname(file_path)
            image_dir = os.path.join(asset_dir, 'images')
            os.makedirs(image_dir, exist_ok=True)

            metadata_to_update = {'metadataProcessingStatus': 'success'}

            if asset.mime_type.startswith('image/'):
                with PilImage.open(file_path) as img:
                    width, height = img.size
                    metadata_to_update.update({'width': width, 'height': height})

                    # --- PERBAIKAN UNTUK BLURHASH ---
                    # 1. Pastikan gambar dalam mode RGB untuk mencegah error
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 2. Coba buat BlurHash
                    try:
                        img_copy = img.copy()
                        img_copy.thumbnail((32, 32))

                        if img_copy.mode != 'RGB':
                            img_copy = img_copy.convert('RGB')

                        # 3. KONVERSI IMAGE PILLOW MENJADI ARRAY NUMPY
                        pixels = np.array(img_copy)

                        # 4. ENCODE MENGGUNAKAN ARRAY NUMPY
                        # Gunakan argumen posisi untuk versi library lama
                        blurhash_str = encode(pixels, 4, 3)  # <-- PERUBAHAN KRUSIAL DI SINI
                        metadata_to_update['blurHash'] = blurhash_str

                        # Hapus error field jika berhasil
                        if 'blurHashError' in metadata_to_update:
                            del metadata_to_update['blurHashError']

                    except Exception as e:
                        print(f"ERROR generating BlurHash for asset {asset.id}: {e}")
                        import traceback
                        traceback.print_exc()
                        metadata_to_update['blurHashError'] = str(e)
                    # --- AKHIR PERBAIKAN ---

                    # Buat Thumbnail dan URL
                    image_urls = {}
                    thumbnail_sizes = {'80': 'webp', '160': 'webp', '240': 'webp', 'default': 'png'}

                    for size_name, format_ext in thumbnail_sizes.items():
                        # --- PERBAIKAN DIMULAI DI SINI ---
                        if size_name == 'default':
                            # Untuk 'default', gunakan URL file asli, tidak perlu membuat thumbnail baru
                            image_urls[size_name] = request.build_absolute_uri(asset.file.url)
                            continue  # Lewati ke iterasi berikutnya
                        # --- PERBAIKAN BERAKHIR DI SINI ---

                        # Kode di bawah ini hanya dijalankan untuk '80', '160', '240'
                        size_pixels = int(size_name)
                        thumb = img.copy()
                        thumb.thumbnail((size_pixels, size_pixels), PilImage.Resampling.LANCZOS)

                        thumb_filename = f"{size_name}.{format_ext}"
                        thumb_path = os.path.join(image_dir, thumb_filename)
                        thumb.save(thumb_path, format_ext.upper() if format_ext != 'webp' else 'WEBP')

                        relative_path = os.path.relpath(thumb_path, settings.MEDIA_ROOT)
                        image_urls[size_name] = f"{settings.MEDIA_URL}{relative_path.replace(os.sep, '/')}"

                    metadata_to_update['imageUrls'] = image_urls

            # Update metadata dengan hasil pemrosesan
            asset.metadata.update(metadata_to_update)
            asset.save(update_fields=['metadata', 'last_modified_at'])

        except Exception as e:
            # Jika ada error, tandai status sebagai gagal
            asset.metadata.update({'metadataProcessingStatus': 'failed', 'error': str(e)})
            asset.save(update_fields=['metadata', 'last_modified_at'])
        # --- AKHIR PROSES PEMROSESAN SINKRON ---

        # Karena proses sudah selesai, respons akan langsung berisi data lengkap
        read_serializer = AssetSerializer(asset, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        RecentAsset.objects.update_or_create(user=request.user, asset=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'])
    def trash(self, request):
        """
        Handles GET (list trashed assets) and POST (move assets to trash).
        """
        if request.method == 'GET':
            """
            Return the paginated list of trashed assets.
            """
            # Ambil workspaceId dari query parameter untuk filter
            workspace_id = request.query_params.get('workspaceId')
            if not workspace_id:
                return Response({"detail": "workspaceId query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

            trashed_assets = Asset.objects.filter(workspace_id=workspace_id, is_trashed=True)

            # Gunakan pagination yang sama
            page = self.paginate_queryset(trashed_assets)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(trashed_assets, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            """
            Move multiple assets to trash bin.
            """
            # Payload adalah list langsung, bukan dictionary
            asset_ids = request.data

            if not isinstance(asset_ids, list) or not asset_ids:
                return Response({"detail": "A list of asset IDs is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Filter aset yang ada dan dimiliki oleh user di workspace yang sama
            assets_to_trash = Asset.objects.filter(
                id__in=asset_ids,
                workspace__memberships__user=request.user,
                is_trashed=False
            )
            count = assets_to_trash.update(is_trashed=True)

            if count == len(asset_ids):
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                # Jika beberapa tidak ditemukan, kembalikan 207 Multi-Status
                found_ids = {str(a.id) for a in assets_to_trash}
                not_found_ids = [str(a_id) for a_id in asset_ids if str(a_id) not in found_ids]
                response_data = {asset_id: 404 for asset_id in not_found_ids}
                return Response(response_data, status=status.HTTP_207_MULTI_STATUS)

    @action(detail=False, methods=['post'], url_path='restore/validate')
    def restore_validate(self, request):
        """
        Validates whether the specified assets in the trash bin can be restored,
        providing detailed information for each asset.
        """
        # 1. Ambil dan validasi workspaceId
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response({"detail": "workspaceId query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not Workspace.objects.filter(id=workspace_id, memberships__user=request.user).exists():
            return Response({"detail": "Workspace not found or you do not have access."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Validasi payload
        serializer = RestoreValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset_ids = serializer.validated_data['assetsIds']

        # 3. Ambil semua aset yang ada di trash dan cocok dengan ID yang diminta
        trashed_assets_map = {
            str(asset.id): asset for asset in Asset.objects.filter(
                id__in=asset_ids,
                is_trashed=True,
                workspace_id=workspace_id
            ).select_related('category', 'folder')
        }

        response_map = {}

        for asset_id in asset_ids:
            asset = trashed_assets_map.get(asset_id)

            # Default status jika aset tidak ditemukan
            validation_status = {
                "sourceExists": False,
                "hasNameConflict": False,
                "isExtensionAllowed": False
            }

            if asset:
                # Aset ditemukan, lakukan validasi lebih lanjut
                validation_status["sourceExists"] = True

                # Tentukan lokasi tujuan (category atau folder)
                target_category = asset.category
                target_folder = asset.folder

                # 4. Cek Konflik Nama
                conflict_query = Q(name=asset.name, extension=asset.extension, is_trashed=False)
                if target_category:
                    conflict_query &= Q(category=target_category)
                elif target_folder:
                    conflict_query &= Q(folder=target_folder)

                has_conflict = Asset.objects.filter(conflict_query).exclude(id=asset.id).exists()
                validation_status["hasNameConflict"] = has_conflict

                # 5. Cek Izin Ekstensi
                # Ekstensi diizinkan jika kategori tidak memiliki pembatasan atau ekstensi ada dalam daftar
                is_allowed = True
                # Cek di kategori folder jika tujuannya adalah folder
                category_to_check = target_folder.category if target_folder else target_category

                if category_to_check and category_to_check.extensions:
                    is_allowed = asset.extension in category_to_check.extensions

                validation_status["isExtensionAllowed"] = is_allowed

            response_map[asset_id] = validation_status

        # 6. Tentukan status code respons
        # Jika ada masalah pada salah satu aset, gunakan 207 Multi-Status
        has_issues = any(
            not status.get("sourceExists", False) or
            status.get("hasNameConflict", False) or
            not status.get("isExtensionAllowed", False)
            for status in response_map.values()
        )

        status_code = status.HTTP_207_MULTI_STATUS if has_issues else status.HTTP_200_OK
        return Response({"assets": response_map}, status=status_code)

    @action(detail=False, methods=['post'], url_path='restore')
    def restore(self, request):
        """
        Restore multiple assets from trash bin. Can restore to original location
        or a new specified target.
        """
        # 1. Validasi workspaceId
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response({"detail": "workspaceId query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not Workspace.objects.filter(id=workspace_id, memberships__user=request.user).exists():
            return Response({"detail": "Workspace not found or you do not have access."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Validasi payload request
        serializer = AssetRestoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actions = serializer.validated_data['assetsActions']

        # 3. Kumpulkan semua ID yang dibutuhkan
        asset_ids = [action['assetId'] for action in actions]
        target_category_ids = {action['target']['categoryId'] for action in actions if action.get('target') and 'categoryId' in action['target']}
        target_folder_ids = {action['target']['folderId'] for action in actions if action.get('target') and 'folderId' in action['target']}

        # 4. Ambil semua objek yang relevan sekaligus
        trashed_assets_map = {str(asset.id): asset for asset in Asset.objects.filter(id__in=asset_ids, is_trashed=True, workspace_id=workspace_id)}
        categories_map = {str(cat.id): cat for cat in Category.objects.filter(id__in=target_category_ids, workspace_id=workspace_id)}
        folders_map = {str(fol.id): fol for fol in Folder.objects.filter(id__in=target_folder_ids, workspace_id=workspace_id)}

        results = {}

        # 5. Proses setiap aksi satu per satu
        with transaction.atomic():
            for action in actions:
                asset_id = action['assetId']
                target_data = action.get('target')  # Bisa None atau dictionary

                asset = trashed_assets_map.get(asset_id)
                if not asset:
                    results[asset_id] = 404  # Asset not found in trash
                    continue

                # --- LOGIKA UNTUK MENENTUKAN TARGET ---
                if target_data:
                    # Skenario 2: Restore ke target baru
                    new_category = None
                    new_folder = None
                    if 'categoryId' in target_data:
                        new_category = categories_map.get(str(target_data['categoryId']))
                        if not new_category:
                            results[asset_id] = 404  # Target category not found
                            continue
                    elif 'folderId' in target_data:
                        new_folder = folders_map.get(str(target_data['folderId']))
                        if not new_folder:
                            results[asset_id] = 404  # Target folder not found
                            continue
                else:
                    # Skenario 1: Restore ke lokasi asli
                    new_category = asset.category
                    new_folder = asset.folder

                # Lakukan pemulihan
                try:
                    asset.category = new_category
                    asset.folder = new_folder
                    asset.is_trashed = False
                    asset.trashed_at = None
                    asset.save()
                    results[asset_id] = 204  # Success
                except Exception as e:
                    print(f"Error restoring asset {asset_id}: {e}")
                    results[asset_id] = 500  # Internal Server Error

        # 6. Tentukan respons akhir
        if all(status == 204 for status in results.values()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            final_results = {k: (200 if v == 204 else v) for k, v in results.items()}
            return Response(final_results, status=status.HTTP_207_MULTI_STATUS)

    @action(detail=False, methods=['post'], url_path='delete')
    def delete(self, request):
        """
        Delete multiple assets permanently from trash and their files from storage.
        """
        # 1. Validasi payload secara manual (harus berupa list)
        asset_ids = request.data
        if not isinstance(asset_ids, list):
            return Response({"detail": "Invalid data. Expected a list of asset IDs."}, status=status.HTTP_400_BAD_REQUEST)

        if not asset_ids:
            return Response({"detail": "No asset IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Cari semua aset yang akan dihapus (harus ada di trash dan dimiliki user)
        assets_to_delete = Asset.objects.filter(
            id__in=asset_ids,
            is_trashed=True,
            workspace__memberships__user=request.user
        )

        # 3. Kumpulkan ID aset yang berhasil ditemukan
        found_ids = {str(asset.id) for asset in assets_to_delete}

        # 4. Hapus file dari storage (file utama dan thumbnail)
        for asset in assets_to_delete:
            try:
                # Hapus file utama
                if asset.file and asset.file.name:
                    asset.file.delete(save=False)

                # Hapus thumbnail
                image_urls = asset.metadata.get('imageUrls', {})
                if image_urls:
                    for url in image_urls.values():
                        try:
                            # Konversi URL menjadi path file sistem
                            file_path = url.replace(settings.MEDIA_URL, settings.MEDIA_ROOT)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception as e:
                            # Log error jika thumbnail gagal dihapus, tapi jangan gagalkan proses
                            print(f"Warning: Could not delete thumbnail {url}: {e}")
            except Exception as e:
                # Log error jika file utama gagal dihapus
                print(f"Warning: Could not delete file for asset {asset.id}: {e}")

        # 5. Hapus record dari database dalam satu transaksi
        with transaction.atomic():
            count, _ = assets_to_delete.delete()

        # 6. Buat respons
        response_data = {}
        for asset_id in asset_ids:
            if asset_id in found_ids:
                response_data[asset_id] = 204  # Success
            else:
                response_data[asset_id] = 404  # Not Found (not in trash or not owned)

        # 7. Tentukan status code HTTP
        if all(status == 204 for status in response_data.values()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)

    @action(detail=True, methods=['get'], url_path=r'thumbs/(?P<dimensions>[\dx]+)\.(?P<frm>[\w]+)', permission_classes=[permissions.AllowAny])
    def thumbs(self, request, id=None, dimensions=None, frm=None):  # <-- UBAH pk MENJADI id
        """
        Mengambil thumbnail gambar dengan ukuran tertentu.
        Endpoint ini dibuka publik agar bisa diakses oleh tag <img>.
        """
        # Kode di dalam metode tidak perlu diubah
        # self.get_object() akan secara otomatis menggunakan 'id' dari self.kwargs
        asset = self.get_object()

        if not asset.mime_type.startswith('image/'):
            return Response({"detail": "Asset is not an image."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if 'x' in dimensions:
                width, height = map(int, dimensions.split('x'))
            else:
                width = int(dimensions)
                height = None
        except ValueError:
            return Response({"detail": "Invalid dimensions format."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            img = PilImage.open(asset.file.path)
            img.thumbnail((width, height) if height else (width, img.height), PilImage.Resampling.LANCZOS)

            from io import BytesIO
            buffer = BytesIO()
            save_format = frm.upper()
            mime_type = f"image/{frm}"
            img.save(buffer, format=save_format)
            buffer.seek(0)

            return HttpResponse(buffer.getvalue(), content_type=mime_type)

        except Exception as e:
            return Response({"detail": f"Error processing image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='offset')
    def offset(self, request, id=None):
        """
        Return the asset's offset in the asset's location for given sorting options.
        """
        # 1. Dapatkan aset target
        target_asset = self.get_object()

        # 2. Ambil parameter pengurutan dari request, dengan nilai default
        sort_by_param = request.query_params.get('sortBy', 'uploadedAt')
        order = request.query_params.get('order', 'desc')

        # 3. Mapping field API ke field model
        sort_mapping = {
            'name': 'name',
            'size': 'size',
            'uploadedAt': 'uploaded_at',
            'lastModifiedAt': 'last_modified_at',
        }
        sort_field = sort_mapping.get(sort_by_param, 'uploaded_at')

        # 4. Gunakan queryset yang sama dengan list view untuk konsistensi
        queryset = self.get_queryset()

        # 5. Bangun kondisi query untuk menghitung aset sebelum target
        #    Ini juga menangani kasus jika ada nilai yang sama (tie) dengan menggunakan ID sebagai tie-breaker.
        if order == 'asc':
            # Hitung aset yang nilainya lebih kecil, atau nilainya sama tapi ID-nya lebih kecil
            condition = Q(**{f'{sort_field}__lt': getattr(target_asset, sort_field)}) | \
                        (Q(**{f'{sort_field}': getattr(target_asset, sort_field)}) & Q(id__lt=target_asset.id))
        else:  # 'desc'
            # Hitung aset yang nilainya lebih besar, atau nilainya sama tapi ID-nya lebih besar
            condition = Q(**{f'{sort_field}__gt': getattr(target_asset, sort_field)}) | \
                        (Q(**{f'{sort_field}': getattr(target_asset, sort_field)}) & Q(id__gt=target_asset.id))

        # 6. Hitung jumlah aset yang memenuhi kondisi. Ini adalah offset-nya.
        offset = queryset.filter(condition).count()

        return Response({'offset': offset})

    @action(detail=False, methods=['post'], url_path='namesExist')
    def names_exist(self, request):
        """
        Check if the asset's names exist in the target destination.
        """
        # 1. Ambil dan validasi workspaceId dari query parameter
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response({"detail": "workspaceId query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Pastikan user memiliki akses ke workspace ini
        if not Workspace.objects.filter(id=workspace_id, memberships__user=request.user).exists():
            return Response({"detail": "Workspace not found or you do not have access."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Validasi payload request
        serializer = NamesExistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_data = serializer.validated_data['target']
        names_to_check = serializer.validated_data['names']

        # 3. Bangun queryset dasar
        queryset = Asset.objects.filter(is_trashed=False, workspace_id=workspace_id)

        # 4. Terapkan filter target (folder atau kategori)
        if 'folderId' in target_data:
            queryset = queryset.filter(folder_id=target_data['folderId'])
        else:  # categoryId
            queryset = queryset.filter(category_id=target_data['categoryId'])

        # 5. Bangun query kompleks untuk mencocokkan nama dan ekstensi
        #    Kita menggunakan objek Q untuk menggabungkan kondisi OR
        q_objects = Q()
        for full_name in names_to_check:
            name, ext = os.path.splitext(full_name)
            # Gunakan iexact untuk pencocokan tidak case-sensitive
            q_objects |= (Q(name__iexact=name) & Q(extension__iexact=ext.lstrip('.')))

        # 6. Eksekusi query dan ambil nama-nama yang cocok
        existing_assets = queryset.filter(q_objects).values_list('name', 'extension')

        # 7. Format kembali nama menjadi 'nama.ekstensi'
        result = [f"{name}.{extension}" for name, extension in existing_assets]

        return Response(result)

    @action(detail=True, methods=['post'], url_path='editImage')
    def edit_image(self, request, id=None):
        """
        Edits an image using transformations and can create a new asset or replace the original.
        """
        asset = self.get_object()

        if not asset.mime_type.startswith('image/'):
            return Response({"detail": "Asset is not an image."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Validasi payload
        serializer = EditImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        new_asset_name = serializer.validated_data['assetName']
        transformations = serializer.validated_data['transformations']

        try:
            # 2. Buka gambar asli
            original_image = PilImage.open(asset.file.path)
            edited_image = self._apply_transformations(original_image, transformations)

            # 3. Siapkan file baru di memori
            new_extension = asset.extension
            new_filename = f"{new_asset_name}.{new_extension}"
            buffer = BytesIO()

            # --- PERBAIKAN FORMAT DAN TRANSPARANSI ---
            # Buat penerjemah dari ekstensi ke format Pillow yang benar
            format_mapping = {
                'JPG': 'JPEG',
                'TIF': 'TIFF',
            }
            # Gunakan format yang sudah diterjemahkan, atau gunakan aslinya jika tidak ada di peta
            save_format = format_mapping.get(new_extension.upper(), new_extension.upper())

            # Jika formatnya JPEG, konversi gambar ke RGB untuk menghapus transparansi
            if save_format == 'JPEG':
                if edited_image.mode in ('RGBA', 'LA', 'P'):
                    edited_image = edited_image.convert('RGB')

            # Simpan gambar yang sudah diedit ke buffer
            edited_image.save(buffer, format=save_format)
            buffer.seek(0)
            new_file = ContentFile(buffer.getvalue(), name=new_filename)

            # 4. Proses berdasarkan aksi ('create' atau 'replace')
            if action == 'create':
                with transaction.atomic():
                    new_asset = Asset.objects.create(
                        name=new_asset_name,
                        extension=new_extension,
                        size=new_file.size,
                        mime_type=asset.mime_type,  # Mime type tetap sama
                        file=new_file,
                        workspace=asset.workspace,
                        folder=asset.folder,
                        category=asset.category,
                        uploaded_by=request.user,
                        metadata={'metadataProcessingStatus': 'pending'}
                    )
                    # Proses metadata untuk aset baru (sinkron)
                    self._process_metadata_sync(new_asset,self.request)

                response_serializer = AssetSerializer(new_asset, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

            else:  # action == 'replace'
                # Hapus file lama
                if asset.file:
                    asset.file.delete(save=False)

                # Update aset yang ada
                asset.file = new_file
                asset.name = new_asset_name
                asset.size = new_file.size
                asset.metadata = {'metadataProcessingStatus': 'pending'}
                asset.save()

                # Proses metadata ulang
                self._process_metadata_sync(asset,self.request)

                response_serializer = AssetSerializer(asset, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # Cetak traceback lengkap untuk debugging yang lebih baik
            import traceback
            traceback.print_exc()
            return Response({"detail": f"Error processing image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- Helper Methods ---

    def _apply_transformations(self, image, transformations):
        """Menerapkan transformasi ke objek gambar Pillow."""
        # Urutan: flip -> rotate -> crop -> resize
        if transformations.get('flip'):
            flip_data = transformations['flip']
            if flip_data.get('x', False):
                image = image.transpose(PilImage.Transpose.FLIP_LEFT_RIGHT)
            if flip_data.get('y', False):
                image = image.transpose(PilImage.Transpose.FLIP_TOP_BOTTOM)

        if transformations.get('rotate'):
            angle = transformations['rotate'].get('angle', 0)
            if angle != 0:
                image = image.rotate(angle, expand=True, fillcolor='white')  # Tambahkan background putih

        if transformations.get('crop'):
            crop_data = transformations['crop']
            x, y, width, height = crop_data['x'], crop_data['y'], crop_data['width'], crop_data['height']
            image = image.crop((x, y, x + width, y + height))

        if transformations.get('resize'):
            resize_data = transformations['resize']
            width, height = resize_data['width'], resize_data['height']
            image = image.resize((width, height), PilImage.Resampling.LANCZOS)

        return image

    def _process_metadata_sync(self, asset, request):
        """
        Memproses metadata untuk aset secara sinkron (digunakan setelah edit).
        """
        try:
            file_path = asset.file.path
            with PilImage.open(file_path) as img:
                width, height = img.size
                metadata_to_update = {'width': width, 'height': height, 'metadataProcessingStatus': 'success'}

                # Generate BlurHash
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_copy = img.copy()
                img_copy.thumbnail((32, 32))
                pixels = np.array(img_copy)
                blurhash_str = encode(pixels, 4, 3)
                metadata_to_update['blurHash'] = blurhash_str

                # Buat ulang thumbnail
                asset_dir = os.path.dirname(file_path)
                image_dir = os.path.join(asset_dir, 'images')
                os.makedirs(image_dir, exist_ok=True)
                image_urls = {}
                thumbnail_sizes = {'80': 'webp', '160': 'webp', '240': 'webp', 'default': 'png'}

                for size_name, format_ext in thumbnail_sizes.items():
                    # --- PERBAIKAN DIMULAI DI SINI ---
                    if size_name == 'default':
                        # Untuk 'default', gunakan URL file asli
                        image_urls[size_name] = request.build_absolute_uri(asset.file.url)
                        continue  # Lewati ke iterasi berikutnya
                    # --- PERBAIKAN BERAKHIR DI SINI ---

                    # Kode di bawah ini hanya dijalankan untuk '80', '160', '240'
                    size_pixels = int(size_name)
                    thumb = img.copy()
                    thumb.thumbnail((size_pixels, size_pixels), PilImage.Resampling.LANCZOS)
                    thumb_filename = f"{size_name}.{format_ext}"
                    thumb_path = os.path.join(image_dir, thumb_filename)
                    thumb.save(thumb_path, format_ext.upper() if format_ext != 'webp' else 'WEBP')
                    relative_path = os.path.relpath(thumb_path, settings.MEDIA_ROOT)
                    image_urls[size_name] = f"{settings.MEDIA_URL}{relative_path.replace(os.sep, '/')}"

                metadata_to_update['imageUrls'] = image_urls

            asset.metadata.update(metadata_to_update)
            asset.save(update_fields=['metadata', 'last_modified_at'])
        except Exception as e:
            print(f"ERROR processing metadata for edited asset {asset.id}: {e}")
            asset.metadata.update({'metadataProcessingStatus': 'failed', 'error': str(e)})
            asset.save(update_fields=['metadata', 'last_modified_at'])


    @action(detail=True, methods=['patch'])
    def metadata(self, request, pk=None):
        """
        Update the metadata of the asset.
        """
        asset = self.get_object()
        serializer = AssetMetadataUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        asset.metadata.update({
            'description': validated_data.get('description', asset.metadata.get('description')),
            'customAttributes': validated_data.get('customAttributes', asset.metadata.get('customAttributes'))
        })
        asset.save(update_fields=['metadata', 'last_modified_at'])

        return Response(asset.metadata)
