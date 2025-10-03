# myapp/permissions.py

from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsWorkspaceMember(permissions.BasePermission):
    """
    Memeriksa apakah user adalah anggota workspace yang disebutkan di query parameter.
    """

    def has_permission(self, request, view):
        workspace_id = request.query_params.get('workspaceId')
        if not workspace_id:
            return False  # WorkspaceId harus ada di request

        is_member = request.user.workspaces.filter(id=workspace_id).exists()
        return is_member


# class IsWorkspaceOwner(permissions.BasePermission):
#     """
#     Memeriksa apakah user yang login adalah owner dari workspace yang terkait.
#     Asumsikan workspaceId ada di query parameter atau di URL.
#     """
#
#     def has_permission(self, request, view):
#         # Coba dapatkan workspace_id dari URL (untuk detail view)
#         workspace_id = view.kwargs.get('workspace_pk')  # atau nama parameter lain di URL
#
#         # Jika tidak ada di URL, coba di query parameter (untuk list view)
#         if not workspace_id:
#             workspace_id = request.query_params.get('workspaceId')
#
#         if not workspace_id:
#             return False  # Tidak bisa menentukan workspace
#
#         try:
#             from .models import Workspace
#             workspace = Workspace.objects.get(id=workspace_id)
#             return workspace.owner == request.user
#         except Workspace.DoesNotExist:
#             return False

class IsWorkspaceOwner(permissions.BasePermission):
    """
    Memeriksa apakah user yang login adalah owner dari workspace yang terkait.
    """

    def has_permission(self, request, view):
        # --- AWAL KODE DEBUGGING ---
        print("=" * 50)
        print("DEBUGGING IsWorkspaceOwner.has_permission()")
        print(f"User: {request.user} (ID: {request.user.id})")
        # --- AKHIR KODE DEBUGGING ---

        workspace_id = view.kwargs.get('workspace_pk')
        if not workspace_id:
            workspace_id = request.query_params.get('workspaceId')

        # --- AWAL KODE DEBUGGING ---
        print(f"Workspace ID dari request: {workspace_id}")
        # --- AKHIR KODE DEBUGGING ---

        if not workspace_id:
            print("ERROR: Workspace ID tidak ditemukan di request.")
            print("=" * 50)
            return False

        try:
            from .models import Workspace
            workspace = Workspace.objects.get(id=workspace_id)

            # --- AWAL KODE DEBUGGING ---
            print(f"Workspace ditemukan: {workspace.name}")
            print(f"Owner workspace: {workspace.owner} (ID: {workspace.owner.id})")
            print(f"Apakah user adalah owner? {workspace.owner == request.user}")
            # --- AKHIR KODE DEBUGGING ---

            is_owner = workspace.owner == request.user
            print("=" * 50)
            return is_owner

        except (Workspace.DoesNotExist, ValueError) as e:
            # --- AWAL KODE DEBUGGING ---
            print(f"ERROR: Workspace tidak ditemukan atau ID tidak valid. Exception: {e}")
            # --- AKHIR KODE DEBUGGING ---
            print("=" * 50)
            return False