# assets/views.py
from uuid import UUID
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from ..models import Asset, RecentAsset
from ..serializer.recentasset import AssetSerializer, RecentAssetUpdateSerializer
from ..pagination import CustomPagination


class RecentAssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk melihat dan memperbarui daftar aset yang baru diakses.
    """
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Ambil workspaceId dari query parameter
        workspace_id = self.request.query_params.get('workspaceId')

        # Ambil semua recent asset milik user
        recent_asset_records = RecentAsset.objects.filter(
            user=self.request.user
        ).select_related('asset')

        # Ambil daftar ID asset
        asset_ids = [record.asset_id for record in recent_asset_records]

        # Filter aset sesuai workspace_id (jika diberikan)
        asset_filter = {
            "id__in": asset_ids,
            "is_trashed": False,
        }
        if workspace_id:
            asset_filter["workspace_id"] = workspace_id

        queryset = Asset.objects.filter(**asset_filter)

        # Buat dictionary agar lookup cepat
        asset_dict = {asset.id: asset for asset in queryset}

        # Ambil hanya asset yang masih valid
        valid_assets = [
            asset_dict[record.asset_id]
            for record in recent_asset_records
            if record.asset_id in asset_dict
        ]

        # Urutkan berdasarkan waktu akses
        sorted_assets = sorted(
            valid_assets,
            key=lambda asset: next(
                (r.accessed_at for r in recent_asset_records if r.asset_id == asset.id),
                None
            ),
            reverse=True
        )

        return sorted_assets

    @action(detail=False, methods=['put'], url_path='update')
    def update_list(self, request):
        """
        Memperbarui daftar aset yang baru diakses.
        Endpoint: PUT /api/recent/update
        Payload: ["uuid1", "uuid2", ...]
        """
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return Response(
                {"detail": "workspaceId query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Pastikan payload adalah list
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of UUIDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validasi format UUID
        try:
            asset_ids = [str(UUID(str(asset_id))) for asset_id in request.data]
        except ValueError:
            return Response(
                {"detail": "One or more IDs are not valid UUIDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not asset_ids:
            return Response(
                {"detail": "No asset IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_assets = Asset.objects.filter(
            id__in=asset_ids,
            is_trashed=False,
            workspace_id=workspace_id,
            uploaded_by=request.user
        )

        found_ids = {str(asset.id) for asset in valid_assets}
        response_data = {}

        for asset_id in asset_ids:
            if asset_id in found_ids:
                try:
                    recent_asset, created = RecentAsset.objects.update_or_create(
                        user=request.user,
                        asset_id=asset_id
                    )
                    response_data[asset_id] = 201 if created else 200
                except Exception as e:
                    print(f"Error updating recent asset {asset_id}: {e}")
                    response_data[asset_id] = 500
            else:
                response_data[asset_id] = 404

        if all(code in [200, 201] for code in response_data.values()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)

    @action(detail=True, methods=['get'], url_path='asset_detail')
    def asset_detail(self, request, pk=None):
        """Endpoint untuk mendapatkan detail satu aset berdasarkan ID."""
        try:
            asset = Asset.objects.get(
                pk=pk,
                is_trashed=False,
                workspace__memberships__user=request.user
            )
            serializer = self.get_serializer(asset)
            return Response(serializer.data)
        except Asset.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)