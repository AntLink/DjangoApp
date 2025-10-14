from rest_framework import serializers
from ..models import Category

class CategorySerializer(serializers.ModelSerializer):
    assets_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'extensions', 'position', 'assets_count']

    def get_assets_count(self, obj):
        return obj.assets.filter(is_trashed=False).count()

    def get_extensions(self, obj):
        # Jika sudah berupa list, kembalikan langsung
        if isinstance(obj.extensions, list):
            return obj.extensions

        # Jika string, coba parse
        if obj.extensions:
            try:
                return json.loads(obj.extensions)
            except (json.JSONDecodeError, TypeError):
                return [obj.extensions] if obj.extensions else []
        return []

