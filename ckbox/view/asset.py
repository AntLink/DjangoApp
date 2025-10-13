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
import shutil

# Impor library untuk pemrosesan gambar
from PIL import Image as PilImage, ImageOps
from blurhash import encode

from ..models import Asset, Workspace, Category, Folder, RecentAsset
from ..pagination import CustomPagination
from ..serializer.asset import (
    AssetSerializer, AssetCreateSerializer, AssetUpdateSerializer, NamesExistSerializer, EditImageSerializer,
    AssetMetadataUpdateSerializer, AssetBulkActionSerializer, RestoreValidateSerializer,
    CategoryTargetSerializer, FolderTargetSerializer, AssetNamesExistSerializer, AssetRestoreSerializer,
    AssetDeleteSerializer, TargetSerializer, AssetActionSerializer, SearchPayloadSerializer
)


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
        Upload an asset. File akan disimpan di dalam folder unik berdasarkan ID.
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

        original_filename = file_obj.name
        name, extension = os.path.splitext(original_filename)
        extension = extension.lstrip('.').lower()
        mime_type = file_obj.content_type or 'application/octet-stream'
        size = file_obj.size

        with transaction.atomic():
            # Django akan otomatis memanggil get_asset_upload_path untuk menentukan lokasi file
            asset = Asset.objects.create(
                name=name, extension=extension, size=size, mime_type=mime_type,
                file=file_obj, workspace=workspace, folder=folder, category=category,
                uploaded_by=request.user, metadata={'metadataProcessingStatus': 'pending'}
            )

        # Panggil helper untuk memproses metadata
        if asset.mime_type.startswith('image/'):
            # Panggil helper untuk memproses metadata hanya untuk gambar
            self._process_metadata_sync(asset, request)
        else:
            # Jika bukan gambar, cukup tandai status sebagai sukses tanpa pemrosesan
            asset.metadata.update({'metadataProcessingStatus': 'success'})
            asset.save(update_fields=['metadata'])

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
        Validates whether the specified assets in the trash bin can be restored.
        """
        # 1. Validasi workspaceId
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response({"detail": "workspaceId query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not Workspace.objects.filter(id=workspace_id, memberships__user=request.user).exists():
            return Response({"detail": "Workspace not found or you do not have access."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Validasi payload
        serializer = RestoreValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset_ids = serializer.validated_data['assetsIds']

        # 3. Ambil semua objek yang relevan
        trashed_assets_map = {str(asset.id): asset for asset in Asset.objects.filter(id__in=asset_ids, is_trashed=True, workspace_id=workspace_id)}
        categories_map = {str(cat.id): cat for cat in Category.objects.filter(id__in=[a.category_id for a in trashed_assets_map.values() if a.category_id], workspace_id=workspace_id)}
        folders_map = {str(fol.id): fol for fol in Folder.objects.filter(id__in=[a.folder_id for a in trashed_assets_map.values() if a.folder_id], workspace_id=workspace_id)}

        response_map = {}

        for asset_id in asset_ids:
            asset = trashed_assets_map.get(asset_id)

            # Default response jika aset tidak ditemukan
            if not asset:
                response_map[asset_id] = {
                    "sourceExists": False,
                    "hasNameConflict": False,
                    "isExtensionAllowed": False
                }
                continue

            # --- PERUBAHAN KRUSIAL: CEK LOKASI ASAL ---
            # Jika aset tidak memiliki category_id atau folder_id, validasi gagal
            if not asset.category_id and not asset.folder_id:
                response_map[asset_id] = {
                    "sourceExists": True,
                    "hasNameConflict": False,
                    "isExtensionAllowed": False,
                    "customError": "Asset has no original location (category or folder) to restore to."
                }
                continue
            # --- AKHIR PERUBAHAN ---

            # Sisanya adalah logika validasi yang sudah ada
            target_category = categories_map.get(str(asset.category_id)) if asset.category_id else None
            target_folder = folders_map.get(str(asset.folder_id)) if asset.folder_id else None

            if not target_category and not target_folder:
                response_map[asset_id] = {
                    "sourceExists": True,
                    "hasNameConflict": False,
                    "isExtensionAllowed": False,
                    "customError": "Original target location (category or folder) not found."
                }
                continue

            # Cek Konflik Nama
            conflict_query = Q(name=asset.name, extension=asset.extension, is_trashed=False)
            if target_category:
                conflict_query &= Q(category=target_category)
            elif target_folder:
                conflict_query &= Q(folder=target_folder)

            has_conflict = Asset.objects.filter(conflict_query).exclude(id=asset.id).exists()

            # Cek Izin Ekstensi
            is_allowed = True
            category_to_check = target_folder.category if target_folder else target_category
            if category_to_check and category_to_check.extensions:
                is_allowed = asset.extension in category_to_check.extensions

            response_map[asset_id] = {
                "sourceExists": True,
                "hasNameConflict": has_conflict,
                "isExtensionAllowed": is_allowed
            }

        # Tentukan status code HTTP
        has_issues = any(
            not status.get("sourceExists", False) or
            status.get("hasNameConflict", False) or
            not status.get("isExtensionAllowed", False) or
            status.get("customError")
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
        asset_ids = request.data
        if not isinstance(asset_ids, list):
            return Response(
                {"detail": "Invalid data. Expected a list of asset IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not asset_ids:
            return Response(
                {"detail": "No asset IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        assets_to_delete = Asset.objects.filter(
            id__in=asset_ids,
            is_trashed=True,
            workspace__memberships__user=request.user
        )

        response_data = {}

        for asset in assets_to_delete:
            try:
                asset_dir = os.path.join(settings.MEDIA_ROOT, 'assets', str(asset.id))
                image_dir = os.path.join(asset_dir, 'images')

                # 1️⃣ Hapus file utama
                if asset.file and asset.file.name:
                    try:
                        asset.file.delete(save=False)
                        print(f"✅ Deleted main file for asset {asset.id}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete main file for asset {asset.id}: {e}")

                # 2️⃣ Hapus folder thumbnail
                if os.path.exists(image_dir):
                    try:
                        os.chmod(image_dir, 0o755)
                        shutil.rmtree(image_dir)
                        print(f"✅ Deleted images directory for {asset.id}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete images directory for {asset.id}: {e}")
                else:
                    print(f"ℹ️ No images directory found for {asset.id}")

                # 3️⃣ Jika folder induk kosong, hapus juga
                if os.path.exists(asset_dir):
                    try:
                        # Hapus hanya jika kosong
                        if not os.listdir(asset_dir):
                            os.rmdir(asset_dir)
                            print(f"✅ Deleted empty folder: {asset_dir}")
                        else:
                            print(f"ℹ️ Folder not empty, skipping: {asset_dir}")
                    except Exception as e:
                        print(f"⚠️ Could not delete folder {asset_dir}: {e}")

                # 4️⃣ Hapus dari database
                asset.delete()
                response_data[str(asset.id)] = 204

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"❌ ERROR deleting asset {asset.id}: {e}")
                response_data[str(asset.id)] = 500

        # 5️⃣ Tentukan respon akhir
        if any(code != 204 for code in response_data.values()):
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        return Response(status=status.HTTP_204_NO_CONTENT)

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

        serializer = EditImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        new_asset_name = serializer.validated_data['assetName']
        transformations = serializer.validated_data['transformations']

        try:
            original_image = PilImage.open(asset.file.path)
            edited_image = self._apply_transformations(original_image, transformations)

            new_extension = asset.extension
            new_filename = f"{new_asset_name}.{new_extension}"
            buffer = BytesIO()

            format_mapping = {'JPG': 'JPEG', 'TIF': 'TIFF'}
            save_format = format_mapping.get(new_extension.upper(), new_extension.upper())

            if save_format == 'JPEG':
                if edited_image.mode in ('RGBA', 'LA', 'P'):
                    edited_image = edited_image.convert('RGB')

            edited_image.save(buffer, format=save_format)
            buffer.seek(0)
            new_file = ContentFile(buffer.getvalue(), name=new_filename)

            if action == 'create':
                with transaction.atomic():
                    # Django akan otomatis memanggil get_asset_upload_path untuk aset baru ini
                    new_asset = Asset.objects.create(
                        name=new_asset_name, extension=new_extension, size=new_file.size,
                        mime_type=asset.mime_type, file=new_file, workspace=asset.workspace,
                        folder=asset.folder, category=asset.category, uploaded_by=request.user,
                        metadata={'metadataProcessingStatus': 'pending'}
                    )
                    self._process_metadata_sync(new_asset, request)

                response_serializer = AssetSerializer(new_asset, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

            else:  # action == 'replace'
                if asset.file:
                    asset.file.delete(save=False)

                asset.file = new_file
                asset.name = new_asset_name
                asset.size = new_file.size
                asset.metadata = {'metadataProcessingStatus': 'pending'}
                asset.save()

                self._process_metadata_sync(asset, request)

                response_serializer = AssetSerializer(asset, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"detail": f"Error processing image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='move')
    def move(self, request):
        """
        Memindahkan satu atau lebih aset ke kategori atau folder target.
        """
        # 1. Validasi Workspace
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response({"detail": "Parameter 'workspaceId' diperlukan."}, status=status.HTTP_400_BAD_REQUEST)

        if not Workspace.objects.filter(id=workspace_id, memberships__user=request.user).exists():
            return Response({"detail": "Workspace tidak ditemukan atau Anda tidak memiliki akses."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Validasi Payload
        serializer = AssetBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_data = serializer.validated_data['target']
        asset_actions = serializer.validated_data['assetsActions']
        asset_ids = [action['assetId'] for action in asset_actions]

        # 3. Tentukan Target (Kategori atau Folder)
        target_category = None
        target_folder = None
        if 'categoryId' in target_data:
            try:
                target_category = Category.objects.get(id=target_data['categoryId'], workspace_id=workspace_id)
            except Category.DoesNotExist:
                return Response({"detail": "Kategori target tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
        else:  # 'folderId' in target_data
            try:
                target_folder = Folder.objects.get(id=target_data['folderId'], workspace_id=workspace_id)
            except Folder.DoesNotExist:
                return Response({"detail": "Folder target tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

        # 4. Pindahkan Aset
        assets_to_move = Asset.objects.filter(
            id__in=asset_ids,
            workspace_id=workspace_id,
            is_trashed=False
        )

        results = {}
        with transaction.atomic():
            for asset in assets_to_move:
                asset.category = target_category
                asset.folder = target_folder
                asset.save()
                results[str(asset.id)] = 204  # 204 No Content = Sukses

        # 5. Tangani Aset yang Tidak Ditemukan
        found_ids = {str(a.id) for a in assets_to_move}
        not_found_ids = [str(a_id) for a_id in asset_ids if str(a_id) not in found_ids]
        for asset_id in not_found_ids:
            results[asset_id] = 404  # 404 Not Found

        # 6. Kembalikan Respons
        if all(status == 204 for status in results.values()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(results, status=status.HTTP_207_MULTI_STATUS)

    @action(detail=False, methods=['post'], url_path='copy')
    def copy(self, request):
        """
        Menyalin satu atau lebih aset ke kategori atau folder target.
        """
        # 1. Validasi Workspace
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response({"detail": "Parameter 'workspaceId' diperlukan."}, status=status.HTTP_400_BAD_REQUEST)

        if not Workspace.objects.filter(id=workspace_id, memberships__user=request.user).exists():
            return Response({"detail": "Workspace tidak ditemukan atau Anda tidak memiliki akses."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Validasi Payload
        serializer = AssetBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_data = serializer.validated_data['target']
        asset_actions = serializer.validated_data['assetsActions']
        asset_ids = [action['assetId'] for action in asset_actions]

        # 3. Tentukan Target (Kategori atau Folder)
        target_category = None
        target_folder = None
        if 'categoryId' in target_data:
            try:
                target_category = Category.objects.get(id=target_data['categoryId'], workspace_id=workspace_id)
            except Category.DoesNotExist:
                return Response({"detail": "Kategori target tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
        else:  # 'folderId' in target_data
            try:
                target_folder = Folder.objects.get(id=target_data['folderId'], workspace_id=workspace_id)
            except Folder.DoesNotExist:
                return Response({"detail": "Folder target tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

        # 4. Salin Aset
        original_assets = Asset.objects.filter(
            id__in=asset_ids,
            workspace_id=workspace_id,
            is_trashed=False
        ).select_related('uploaded_by')

        new_assets = []
        with transaction.atomic():
            for original_asset in original_assets:
                # Buka file asli untuk dibaca isinya
                with original_asset.file.open('rb') as f:
                    file_content = f.read()

                # Buat instance ContentFile dari file yang dibaca
                new_file = ContentFile(file_content, name=original_asset.file.name)

                # Buat instance aset baru
                new_asset = Asset(
                    name=original_asset.name,
                    extension=original_asset.extension,
                    size=original_asset.size,
                    mime_type=original_asset.mime_type,
                    file=new_file,
                    workspace=original_asset.workspace,
                    category=target_category,
                    folder=target_folder,
                    uploaded_by=request.user,  # Penyalin menjadi pengunggah baru
                    tags=original_asset.tags,
                    metadata=original_asset.metadata,
                )
                new_assets.append(new_asset)

            # Gunakan bulk_create untuk efisiensi
            created_assets = Asset.objects.bulk_create(new_assets)

        # 5. Proses Metadata untuk Aset Baru (jika perlu)
        # Jika Anda perlu memproses metadata (seperti thumbnail) untuk aset yang disalin,
        # Anda harus melakukannya secara individual setelah bulk_create.
        for asset in created_assets:
            if asset.mime_type.startswith('image/'):
                self._process_metadata_sync(asset, request)

        # 6. Kembalikan Respons
        # Kembalikan data aset yang baru dibuat
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='search')
    def search(self, request):
        """
        Mencari aset berdasarkan frasa dan berbagai filter.
        Endpoint ini menggunakan POST untuk menerima payload filter yang kompleks.
        """
        # 1. Validasi Workspace
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            raise ValidationError("Parameter 'workspaceId' diperlukan.")

        if not Workspace.objects.filter(id=workspace_id, memberships__user=request.user).exists():
            raise ValidationError("Workspace tidak ditemukan atau Anda tidak memiliki akses.")

        # 2. Validasi Payload
        serializer = SearchPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        search_phrase = validated_data.get('searchPhrase')
        filters = validated_data.get('filters', {})
        pagination = validated_data['pagination']

        # 3. Bangun Queryset Dasar
        queryset = Asset.objects.filter(workspace_id=workspace_id, is_trashed=False)

        # 4. Terapkan Filter Pencarian (searchPhrase)
        if search_phrase:
            queryset = queryset.filter(name__icontains=search_phrase)

        # 5. Terapkan Filter Dinamis
        if filters:
            # Filter Kategori
            if 'categories' in filters and filters['categories'].get('in'):
                queryset = queryset.filter(category_id__in=filters['categories']['in'])

            # Filter Ekstensi
            if 'extensions' in filters and filters['extensions'].get('in'):
                queryset = queryset.filter(extension__in=[ext.lower() for ext in filters['extensions']['in']])

            # Filter Tags
            if 'tags' in filters and filters['tags'].get('in'):
                tags_to_find = filters['tags']['in']
                tag_query = Q()
                for tag in tags_to_find:
                    tag_query |= Q(tags__contains=[tag])
                queryset = queryset.filter(tag_query)

            # Filter Rentang Tanggal
            if 'uploadedAt' in filters:
                if filters['uploadedAt'].get('from'):
                    queryset = queryset.filter(uploaded_at__gte=filters['uploadedAt']['from'])
                if filters['uploadedAt'].get('to'):
                    queryset = queryset.filter(uploaded_at__lte=filters['uploadedAt']['to'])

            if 'lastModifiedAt' in filters:
                if filters['lastModifiedAt'].get('from'):
                    queryset = queryset.filter(last_modified_at__gte=filters['lastModifiedAt']['from'])
                if filters['lastModifiedAt'].get('to'):
                    queryset = queryset.filter(last_modified_at__lte=filters['lastModifiedAt']['to'])

        # 6. Terapkan Pengurutan (Sorting)
        sort_mapping = {
            'name': 'name',
            'size': 'size',
            'uploadedAt': 'uploaded_at',
            'lastModifiedAt': 'last_modified_at',
        }
        sort_by_field = sort_mapping.get(pagination['sortBy'], 'uploaded_at')
        ordering_prefix = '' if pagination['order'] == 'asc' else '-'
        queryset = queryset.order_by(f"{ordering_prefix}{sort_by_field}")

        # 7. Terapkan Pagination Manual
        limit = pagination['limit']
        offset = pagination['offset']

        total_count = queryset.count()
        results = queryset[offset: offset + limit]

        # 8. Serialisasi Hasil dengan AssetSerializer yang baru
        # Penting: meneruskan context={'request': request}
        asset_serializer = AssetSerializer(results, many=True, context={'request': request})

        # 9. Kembalikan Respons dengan Format Baru
        response_data = {
            "items": asset_serializer.data,
            "limit": limit,
            "offset": offset,
            "totalCount": total_count
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def _apply_transformations(self, image, transformations):
        """Menerapkan transformasi ke objek gambar Pillow."""
        if transformations.get('flip'):
            flip_data = transformations['flip']
            if flip_data.get('x', False):
                image = image.transpose(PilImage.Transpose.FLIP_LEFT_RIGHT)
            if flip_data.get('y', False):
                image = image.transpose(PilImage.Transpose.FLIP_TOP_BOTTOM)
        if transformations.get('rotate'):
            angle = transformations['rotate'].get('angle', 0)
            if angle != 0:
                image = image.rotate(angle, expand=True, fillcolor='white')
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
        Memproses metadata untuk aset secara sinkron.
        Folder 'images' hanya dibuat jika file adalah gambar.
        """
        try:
            file_path = asset.file.path

            # --- PERUBAHAN: PEMERIKSAAN MIME TYPE DI AWAL ---
            if not asset.mime_type.startswith('image/'):
                # Jika bukan gambar, tidak ada yang perlu diproses.
                print(f"Skipping metadata processing for non-image asset {asset.id}.")
                return
            # --- AKHIR PERUBAHAN ---

            # Kode di bawah ini hanya akan dijalankan untuk gambar
            asset_dir = os.path.dirname(file_path)
            image_dir = os.path.join(asset_dir, 'images')
            os.makedirs(image_dir, exist_ok=True)

            with PilImage.open(file_path) as img:
                # ... (semua kode di dalam blok `with` tetap sama) ...
                width, height = img.size
                metadata_to_update = {'width': width, 'height': height, 'metadataProcessingStatus': 'success'}

                # Generate BlurHash
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                try:
                    img_copy = img.copy()
                    img_copy.thumbnail((32, 32))
                    pixels = np.array(img_copy)
                    blurhash_str = encode(pixels, 4, 3)
                    metadata_to_update['blurHash'] = blurhash_str
                except Exception as e:
                    print(f"ERROR generating BlurHash for asset {asset.id}: {e}")

                # --- LOGIKA THUMBNAIL ---
                thumbnail_sizes = settings.GLOBAL_THUMBNAIL_SIZES
                image_urls = {}
                for size_name, format_ext in thumbnail_sizes.items():
                    if size_name == 'default':
                        image_urls[size_name] = request.build_absolute_uri(asset.file.url)
                        continue

                    thumb_filename = f"thumb_{size_name}.{format_ext}"
                    format_mapping = {'JPG': 'JPEG', 'TIF': 'TIFF'}
                    save_format = format_mapping.get(format_ext.upper(), format_ext.upper())
                    size_pixels = int(size_name)
                    thumb = img.copy()
                    thumb.thumbnail((size_pixels, size_pixels), PilImage.Resampling.LANCZOS)

                    thumb_path = os.path.join(image_dir, thumb_filename)
                    thumb.save(thumb_path, format=save_format)

                    relative_path = os.path.relpath(thumb_path, settings.MEDIA_ROOT)
                    image_urls[size_name] = f"{settings.MEDIA_URL}{relative_path.replace(os.sep, '/')}"

                metadata_to_update['imageUrls'] = image_urls

            asset.metadata.update(metadata_to_update)
            asset.save(update_fields=['metadata', 'last_modified_at'])
        except Exception as e:
            print(f"ERROR processing metadata for edited asset {asset.id}: {e}")
            import traceback
            traceback.print_exc()
            asset.metadata.update({'metadataProcessingStatus': 'failed', 'error': str(e)})
            asset.save(update_fields=['metadata', 'last_modified_at'])

    # @action(detail=True, methods=['patch'])
    # def metadata(self, request, pk=None):
    #     """
    #     Update the metadata of the asset.
    #     """
    #     asset = self.get_object()
    #     serializer = AssetMetadataUpdateSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     validated_data = serializer.validated_data
    #     asset.metadata.update({
    #         'description': validated_data.get('description', asset.metadata.get('description')),
    #         'customAttributes': validated_data.get('customAttributes', asset.metadata.get('customAttributes'))
    #     })
    #     asset.save(update_fields=['metadata', 'last_modified_at'])
    #
    #     return Response(asset.metadata)
