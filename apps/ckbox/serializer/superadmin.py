from rest_framework import serializers
from ..models import WorkspaceTemplate, EnvironmentConfig,Workspace

class EnvironmentConfigSerializer(serializers.ModelSerializer):
    """
    Serializer untuk EnvironmentConfig dengan output camelCase.
    """

    class Meta:
        model = EnvironmentConfig
        fields = ['allowed_extensions', 'is_allowed_extensions_enabled', 'ckbox_project_id']

    def to_representation(self, instance):
        """
        Ubah snake_case → camelCase untuk output API.
        """
        data = super().to_representation(instance)

        allowed_extensions = data.pop('allowed_extensions', [])
        is_allowed_extensions_enabled = data.pop('is_allowed_extensions_enabled', False)
        ckbox_project_id = data.pop('ckbox_project_id', None)

        return {
            'allowedExtensions': allowed_extensions,
            'isAllowedExtensionsEnabled': is_allowed_extensions_enabled,
            'ckboxProjectId': ckbox_project_id,
        }