# apps/media/serializers.py
from django.core.cache import cache
from rest_framework import serializers
from ..models import Tags, Category, Folder, Media, Mediahastags
import json
import os
from django.conf import settings
import blurhash
from PIL import Image

class TagsSerializer(serializers.ModelSerializer):
    # Manual implementation for MPTT structure
    children = serializers.SerializerMethodField()

    class Meta:
        model = Tags
        fields = ['id', 'name', 'parent', 'slug', 'status', 'type', 'description', 'created_at', 'updated_at', 'children']

    def get_children(self, obj):
        # Get all children of this node
        children = obj.get_children()
        return TagsSerializer(children, many=True).data


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class TagsTreeSerializer(serializers.ModelSerializer):
    children = RecursiveSerializer(many=True, source='get_children')

    class Meta:
        model = Tags
        fields = ['id', 'name', 'parent', 'slug', 'status', 'type', 'description', 'created_at', 'updated_at', 'children']


class CategorySerializer(serializers.ModelSerializer):
    # Ubah nama field ke camelCase
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    position = serializers.IntegerField(read_only=True)
    assetsCount = serializers.IntegerField(source='assets_count', read_only=True)
    totalAssetsCount = serializers.IntegerField(source='total_assets_count', read_only=True)
    isPrivate = serializers.BooleanField(source='is_private', read_only=True)

    # Custom field untuk extensions sebagai array
    extensions = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'position', 'assetsCount', 'totalAssetsCount', 'extensions', 'isPrivate']

    def get_extensions(self, obj):
        # Konversi string JSON ke array
        if obj.extensions:
            try:
                return json.loads(obj.extensions)
            except (json.JSONDecodeError, TypeError):
                # Jika bukan JSON valid, kembalikan sebagai array dengan 1 elemen
                return [obj.extensions] if obj.extensions else []
        return []


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name', 'category', 'parent', 'created_at', 'updated_at', 'assets_count']


class MediaSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True, source='media_tags')
    category = CategorySerializer(read_only=True)
    folder = FolderSerializer(read_only=True)

    class Meta:
        model = Media
        fields = [
            'id', 'user', 'tags', 'category', 'folder',
            'name', 'unique_name', 'size', 'path', 'file',
            'type', 'file_type', 'favored', 'description',
            'created_at', 'updated_at'
        ]


class MediahastagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mediahastags
        fields = ['media', 'tags']


class MediaListSerializer(serializers.ModelSerializer):
    """Serializer khusus untuk aksi list dengan format respons yang diinginkan"""
    id = serializers.CharField(source='pk')
    extension = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    imageUrls = serializers.SerializerMethodField()
    mimeType = serializers.CharField(source='file_type')
    categoryId = serializers.SerializerMethodField()  # Diubah menjadi SerializerMethodField
    folderId = serializers.SerializerMethodField()  # Diubah menjadi SerializerMethodField
    size = serializers.SerializerMethodField()
    uploadedAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%dT%H:%M:%S.%fZ')
    lastModifiedAt = serializers.DateTimeField(source='updated_at', format='%Y-%m-%dT%H:%M:%S.%fZ')
    lastUsedAt = serializers.DateTimeField(source='updated_at', format='%Y-%m-%dT%H:%M:%S.%fZ')
    tags = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = [
            'id', 'name', 'extension', 'url', 'imageUrls', 'mimeType',
            'categoryId', 'folderId', 'size', 'uploadedAt',
            'lastModifiedAt', 'lastUsedAt', 'tags', 'metadata'
        ]

    def get_extension(self, obj):
        """Ekstrak ekstensi file dari path file"""
        if obj.file and obj.file.name:
            return os.path.splitext(obj.file.name)[1][1:].lower()
        return ''

    def get_url(self, obj):
        """Buat URL lengkap untuk file asli"""
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None

    def get_imageUrls(self, obj):
        """Generate image URLs for different sizes with new folder structure"""
        if obj.file_type not in ['jpg', 'png', 'jpeg', 'gif', 'webp','bmp','webp','tiff']:
            return {}

        image_urls = {}
        # sizes = [160, 320, 384, 280, 373, 507, 538,533, 498, 480, 640, 800, 960, 1120, 1280, 1440, 1600,1920]
        sizes = []

        if obj.file and obj.file.name:
            # Extract directory and filename
            dirname = os.path.dirname(obj.file.name)
            filename = os.path.basename(obj.file.name)
            base, ext = os.path.splitext(filename)
            thumb_path = settings.MEDIA_ROOT + os.path.join(dirname, 'thumbnail')
            if(os.path.exists(thumb_path)):
                sizes = os.listdir(thumb_path)

            # Generate URLs for each size with new folder structure
            for size in sizes:
                # Create thumbnail path: /media/images/2025923/thumbnail/160/filename.png
                thumbnail_path = os.path.join(dirname, 'thumbnail', str(size), filename)
                full_url = self.context['request'].build_absolute_uri(
                    f"{settings.MEDIA_URL}{thumbnail_path}"
                )
                image_urls[str(size)] = full_url

            # Add default URL (original image)
            image_urls['default'] = self.get_url(obj)

        return image_urls

    def get_size(self, obj):
        """Konversi ukuran string ke integer"""
        try:
            return int(obj.size)
        except (ValueError, TypeError):
            return 0

    def get_categoryId(self, obj):
        """Dapatkan ID kategori sebagai string jika ada, jika tidak ada maka None"""
        if obj.category:
            return str(obj.category.id)
        return None

    def get_folderId(self, obj):
        """Dapatkan ID folder sebagai string jika ada, jika tidak ada maka None"""
        if obj.folder:
            return str(obj.folder.id)
        return None

    def get_tags(self, obj):
        """Dapatkan daftar nama tag"""
        return [tag.name for tag in obj.tags.all()]

    def generate_manual_blurhash(self, image):
        """Generate a manual blurhash based on image colors"""
        try:
            # Resize image to small size for performance
            image_copy = image.copy()
            image_copy.thumbnail((32, 32))

            # Convert to RGB if necessary
            if image_copy.mode != 'RGB':
                image_copy = image_copy.convert('RGB')

            # Get average color
            pixels = np.array(image_copy)
            avg_color = np.mean(pixels, axis=(0, 1))
            r, g, b = avg_color.astype(int)

            # Get color variance for more interesting blurhash
            color_variance = np.std(pixels, axis=(0, 1))
            vr, vg, vb = color_variance.astype(int)

            # Create a blurhash-like string
            # Format: LRRGGBBVV + fixed pattern
            blurhash = f"L{r:02x}{g:02x}{b:02x}{vr:01x}{vg:01x}{vb:01x}PZfSi_.AyE_3t7t7R**0o#DgR4"

            image_copy.close()
            return blurhash

        except Exception as e:
            print(f"Error generating manual blurhash: {str(e)}")
            # Fallback to a default blurhash
            return "L6PZfSi_.AyE_3t7t7R**0o#DgR4"

    def get_metadata(self, obj):
        """Generate metadata for media with manual blurhash"""
        metadata = {
            'width': None,
            'height': None,
            'blurHash': None,
            'description':obj.description,
            'metadataProcessingStatus': 'success',
            'analysisProcessingStatus': 'queued'
        }

        # Only process if file is an image and file is available
        if obj.file_type in ['jpg', 'png', 'jpeg', 'gif', 'webp','bmp','webp','tiff']:
            try:
                if obj.type == 'p':
                # Build file path
                    file_path = os.path.join(
                        settings.MEDIA_ROOT,
                        'images',
                        obj.path,
                        obj.unique_name
                    )
                else:
                    file_path = os.path.join(
                        settings.MEDIA_ROOT,
                        'files',
                        obj.path,
                        obj.unique_name
                    )

                print(f"Path file: {file_path}")
                print(f"File exists: {os.path.exists(file_path)}")

                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")

                # Open file
                with open(file_path, 'rb') as f:
                    # Read image with Pillow
                    image = Image.open(f)

                    # Get image dimensions
                    metadata['width'] = image.width
                    metadata['height'] = image.height
                    print(f"Image dimensions: {metadata['width']}x{metadata['height']}")

                    # Generate blurhash using manual method
                    metadata['blurHash'] = self.generate_manual_blurhash(image)
                    print(f"Generated blurhash: {metadata['blurHash']}")

                    # Close image
                    image.close()

            except Exception as e:
                print(f"Error processing image {obj.id}: {str(e)}")
                import traceback
                traceback.print_exc()
                metadata['metadataProcessingStatus'] = 'error'
                metadata['analysisProcessingStatus'] = 'failed'
        else:
            metadata = {
                'description': obj.description,
            }

        return metadata