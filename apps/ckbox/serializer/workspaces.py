from rest_framework import serializers
from ..models import Workspace
from ..serializers import UserSerializer

class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'owner', 'members', 'created_at']

