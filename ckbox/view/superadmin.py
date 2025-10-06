# myapp/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from ..serializer.superadmin import EnvironmentConfigSerializer
from ..models import WorkspaceTemplate, EnvironmentConfig
from ..permissions import IsSuperAdmin, IsWorkspaceMember, IsWorkspaceOwner
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from rest_framework.response import Response


class SuperadminEnvironmentConfigView(APIView):
    permission_classes = [IsAdminUser, IsAuthenticated]

    def get(self, request, format=None):
        config, _ = EnvironmentConfig.objects.get_or_create(pk=1)
        serializer = EnvironmentConfigSerializer(config)
        return Response(serializer.data)

    def put(self, request, format=None):
        """
        Update konfigurasi lingkungan global.
        Terima payload camelCase dan konversi ke snake_case.
        """
        config, _ = EnvironmentConfig.objects.get_or_create(pk=1)

        validated_data = {}
        if 'allowedExtensions' in request.data:
            validated_data['allowed_extensions'] = request.data['allowedExtensions']
        if 'isAllowedExtensionsEnabled' in request.data:
            validated_data['is_allowed_extensions_enabled'] = request.data['isAllowedExtensionsEnabled']
        if 'ckboxProjectId' in request.data:
            validated_data['ckbox_project_id'] = request.data['ckboxProjectId']

        serializer = EnvironmentConfigSerializer(config, data=validated_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SuperadminWorkspaceTemplateView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request, format=None):
        """
        Mengembalikan daftar kategori dari semua template yang digabung menjadi satu.
        """
        # Ambil semua template
        templates = WorkspaceTemplate.objects.all()

        # Gabungkan semua daftar kategori dari setiap template
        all_categories = []
        for template in templates:
            # Pastikan categories_templates adalah list sebelum menambahkannya
            if isinstance(template.categories_templates, list):
                all_categories.extend(template.categories_templates)

        return Response({"categoriesTemplates": all_categories})

    def put(self, request, format=None):
        """
        Memperbarui daftar kategori master.
        API akan menyimpan semua kategori ini ke dalam satu template default.
        """
        categories_data = request.data.get('categoriesTemplates', [])

        if not isinstance(categories_data, list):
            return Response({"detail": "Invalid payload. Expected a list of categories."}, status=status.HTTP_400_BAD_REQUEST)

        # Gunakan get_or_create untuk membuat atau memperbarui template default
        template, created = WorkspaceTemplate.objects.get_or_create(
            name="Default Template",  # Nama tetap untuk template master kita
            defaults={'categories_templates': categories_data}
        )

        # Jika template sudah ada, perbarui datanya
        if not created:
            template.categories_templates = categories_data
            template.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
