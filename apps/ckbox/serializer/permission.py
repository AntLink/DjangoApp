from rest_framework import serializers
from ..models import Permission, WorkspaceGroup
from django.contrib.auth import get_user_model

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    # output fields
    categoriesIds = serializers.PrimaryKeyRelatedField(
        source='categories',
        many=True,
        read_only=True
    )
    permissionsList = serializers.JSONField(
        source='permissions_list',
        read_only=True
    )
    groupId = serializers.UUIDField(
        source='group.id',
        read_only=True
    )

    class Meta:
        model = Permission
        fields = [
            'id',
            'groupId',
            'categoriesIds',
            'permissionsList',
        ]

    def create(self, validated_data):
        """
        Create pakai payload:
        {
          "groupId": "...",
          "permissionsList": {...},
          "categoriesIds": [...]
        }
        """
        group_id = self.initial_data.get("groupId")
        permissions_list = self.initial_data.get("permissionsList", {})
        categories_ids = self.initial_data.get("categoriesIds", [])

        if not group_id:
            raise serializers.ValidationError({"groupId": "This field is required."})

        try:
            workspace_group = WorkspaceGroup.objects.get(id=group_id)
        except WorkspaceGroup.DoesNotExist:
            raise serializers.ValidationError(
                {"groupId": f"WorkspaceGroup with id '{group_id}' not found."}
            )

        permission = Permission.objects.create(
            group=workspace_group,
            permissions_list=permissions_list
        )

        if categories_ids:
            permission.categories.set(categories_ids)

        return permission

    def update(self, instance, validated_data):
        """
        Update pakai payload:
        {
          "permissionsList": {...},
          "categoriesIds": [...]
        }
        """
        permissions_list = self.initial_data.get("permissionsList")
        categories_ids = self.initial_data.get("categoriesIds")

        if permissions_list is not None:
            instance.permissions_list = permissions_list

        if categories_ids is not None:
            instance.categories.set(categories_ids)

        instance.save()
        return instance
