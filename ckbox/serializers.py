# myapp/serializers.py
from django.contrib.auth.models import Group as DjangoGroup
import os
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
User = get_user_model()

class CKBoxTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        role = "superadmin" if user.is_superuser and user.is_staff else "admin"
        ws = [str(w) for w in Workspace.objects.filter(owner=user).values_list('id', flat=True)]


        # 🔹 Ambil CKBox AUD dari database
        env = EnvironmentConfig.objects.first()
        aud = env.ckbox_project_id if env and env.ckbox_project_id else "default-audience"

        token["aud"] = aud
        token["sub"] = str(user.id)
        token["auth"] = {
            "ckbox": {
                "role": role,
                "workspaces": ws
            }
        }
        return token

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer kustom untuk menambahkan klaim (data) tambahan ke dalam JWT payload.
    """

    def validate(self, attrs):
        # Data default dari validasi user
        data = super().validate(attrs)

        # Tambahkan klaim kustom
        refresh = self.get_token(self.user)

        # Menambahkan role ke payload
        if self.user.is_superuser:
            role = 'superadmin'
        # Anda bisa menambahkan logika lain di sini, misal untuk 'admin' workspace
        else:
            role = 'admin'

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Tambahkan data ke payload access token
        data['access'] = str(refresh.access_token)
        # refresh.access_token.payload adalah dictionary yang bisa dimodifikasi
        refresh.access_token['role'] = role

        # Tambahkan audience (environment ID)
        # Ini bisa diambil dari settings atau model EnvironmentConfig
        from django.conf import settings
        refresh.access_token['aud'] = getattr(settings, 'CKBOX_ENVIRONMENT_ID', 'default-env')

        return data



class WorkspaceGroupSerializer(serializers.ModelSerializer):
    """
    Serializer untuk WorkspaceGroup yang juga menangani pembuatan Group Django.
    """
    name = serializers.CharField(source='name', write_only=True)
    workspace_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = WorkspaceGroup
        fields = ['id', 'name', 'workspace_id']

    def create(self, validated_data):
        name = validated_data.pop('name')
        workspace_id = validated_data.pop('workspace_id')

        django_group = DjangoGroup.objects.create(name=name)
        workspace_group = WorkspaceGroup.objects.create(
            group=django_group,
            workspace_id=workspace_id
        )
        return workspace_group

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



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'owner', 'members', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    assets_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'extensions', 'position', 'assets_count']

    def get_assets_count(self, obj):
        return obj.assets.filter(is_trashed=False).count()

    # class CategorySerializer(serializers.ModelSerializer):
    #     """Serializer untuk model Category dengan format camelCase"""
    #     id = serializers.CharField(read_only=True)
    #     name = serializers.CharField(read_only=True)
    #     position = serializers.IntegerField(read_only=True)
    #     assetsCount = serializers.IntegerField(source='assets_count', read_only=True)
    #     totalAssetsCount = serializers.IntegerField(source='total_assets_count', read_only=True)
    #     isPrivate = serializers.BooleanField(source='is_private', read_only=True)
    #     extensions = serializers.SerializerMethodField()
    #
    #     class Meta:
    #         model = Category
    #         fields = [
    #             'id', 'name', 'position',
    #             'assetsCount', 'totalAssetsCount',
    #             'extensions', 'isPrivate'
    #         ]

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


class FolderSerializer(serializers.ModelSerializer):
    folders = serializers.SerializerMethodField()
    assets_count = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'created_at', 'updated_at',
            'category_id', 'parent_id', 'folders',
            'assets_count', 'created_by','parent', 'children'
        ]

    def get_children(self, obj):
        children = obj.children.all()
        return FolderSerializer(children, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'name': data['name'],
            'createdAt': data['created_at'],
            'updatedAt': data['updated_at'],
            'categoryId': data['category_id'],
            'parentId': data['parent_id'],
            'folders': data['folders'],
            'assetsCount': data['assets_count'],
            'createdBy': data['created_by']
        }

    def get_folders(self, obj):
        # Karena `children` sudah di-prefetch, ini akan sangat cepat
        children = obj.children.all()
        return FolderSerializer(children, many=True, context=self.context).data

    def get_assets_count(self, obj):
        return obj.assets.filter(is_trashed=False).count()

class FolderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer fleksibel untuk membuat folder baru:
    - Jika `categoryId` diberikan → folder root.
    - Jika `parentId` diberikan → subfolder.
    """
    parentId = serializers.UUIDField(write_only=True, required=False)
    categoryId = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Folder
        fields = ['name', 'parentId', 'categoryId']

    def validate(self, attrs):
        """
        Validasi input dasar — salah satu dari categoryId atau parentId harus ada.
        """
        parent_id = attrs.get('parentId')
        category_id = attrs.get('categoryId')

        if not parent_id and not category_id:
            raise serializers.ValidationError({
                "detail": "Either 'categoryId' or 'parentId' must be provided."
            })

        return attrs

    def create(self, validated_data):
        """
        Logika utama untuk membuat folder baru.
        """
        request = self.context['request']
        user = request.user
        workspace_id = request.query_params.get('workspaceId')

        if not workspace_id:
            raise serializers.ValidationError({
                "detail": "workspaceId query parameter is required."
            })

        # --- Cek workspace ---
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            raise serializers.ValidationError({
                "detail": f"Workspace with id '{workspace_id}' not found."
            })

        parent_id = validated_data.get('parentId')
        category_id = validated_data.get('categoryId')
        name = validated_data['name']

        # --- CASE 1: Membuat subfolder ---
        if parent_id:
            parent_folder = get_object_or_404(Folder, id=parent_id, workspace=workspace)

            # Warisi kategori dari parent
            category = parent_folder.category

            # Validasi permission
            if parent_folder.workspace.owner != user:
                raise PermissionDenied("You do not have permission to create a subfolder here.")

            folder = Folder.objects.create(
                name=name,
                workspace=workspace,
                parent=parent_folder,
                category=category,
                created_by=user
            )

        # --- CASE 2: Membuat folder di bawah kategori ---
        elif category_id:
            category = get_object_or_404(Category, id=category_id, workspace=workspace)

            folder = Folder.objects.create(
                name=name,
                workspace=workspace,
                category=category,
                created_by=user
            )

        return folder


class AssetSerializer(serializers.ModelSerializer):
    image_urls = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'extension', 'size', 'mime_type', 'url', 'image_urls',
            'category_id', 'folder_id', 'uploaded_by', 'uploaded_at', 'last_modified_at',
            'metadata', 'tags', 'is_trashed'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at', 'last_modified_at', 'is_trashed']

    def get_image_urls(self, obj):
        if obj.mime_type.startswith('image/'):
            request = self.context.get('request')
            return {
                '80': request.build_absolute_uri(f"/api/assets/{obj.id}/thumbs/80.webp"),
                '160': request.build_absolute_uri(f"/api/assets/{obj.id}/thumbs/160.webp"),
                'default': request.build_absolute_uri(obj.file.url),
            }
        return None

    def get_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url)

    def create(self, validated_data):
        file_obj = validated_data.pop('file')
        validated_data['mime_type'] = file_obj.content_type
        validated_data['size'] = file_obj.size
        validated_data['extension'] = file_obj.name.split('.')[-1].lower()
        validated_data['name'] = file_obj.name.rsplit('.', 1)[0]
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class AssetListSerializer(serializers.ModelSerializer):
    """Serializer khusus untuk aksi list dengan format respons yang diinginkan"""
    id = serializers.CharField(source='pk')
    extension = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    imageUrls = serializers.SerializerMethodField()
    mimeType = serializers.CharField(source='extension')
    categoryId = serializers.SerializerMethodField()  # Diubah menjadi SerializerMethodField
    folderId = serializers.SerializerMethodField()  # Diubah menjadi SerializerMethodField
    size = serializers.SerializerMethodField()
    uploadedAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%dT%H:%M:%S.%fZ')
    lastModifiedAt = serializers.DateTimeField(source='updated_at', format='%Y-%m-%dT%H:%M:%S.%fZ')
    lastUsedAt = serializers.DateTimeField(source='updated_at', format='%Y-%m-%dT%H:%M:%S.%fZ')
    tags = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = Asset
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
        if obj.extension not in ['jpg', 'png', 'jpeg', 'gif', 'webp', 'bmp', 'webp', 'tiff']:
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
            if (os.path.exists(thumb_path)):
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
            'description': obj.description,
            'metadataProcessingStatus': 'success',
            'analysisProcessingStatus': 'queued'
        }

        # Only process if file is an image and file is available
        if obj.extension in ['jpg', 'png', 'jpeg', 'gif', 'webp', 'bmp', 'webp', 'tiff']:
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



class WorkspaceTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceTemplate
        fields = '__all__'


class RecentAssetSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)

    class Meta:
        model = RecentAsset
        fields = ['asset', 'accessed_at']


class CategoryAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk endpoint /admin/categories GET.
    """
    extensionsInUse = serializers.SerializerMethodField()

    class Meta:
        model = Category
        # --- SESUAIKAN URUTAN FIELD ---
        fields = ['id', 'name', 'position','isPrivate', 'extensions', 'extensionsInUse']

    def get_extensionsInUse(self, obj):
        used_exts = Asset.objects.filter(category=obj, is_trashed=False).values_list('extension', flat=True).distinct()
        return list(used_exts)


class CategoryCreateAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk endpoint /admin/categories POST.
    """

    class Meta:
        model = Category
        fields = ['name', 'extensions']


class EnvironmentConfigAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentConfig
        fields = ['allowedExtensions', 'isAllowedExtensionsEnabled']
        # Ganti nama field untuk mencocokan API CKBox
        field_mappings = {
            'allowed_extensions': 'allowedExtensions',
            'is_allowed_extensions_enabled': 'isAllowedExtensionsEnabled'
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ganti nama key di output JSON
        data['allowedExtensions'] = data.pop('allowed_extensions')
        data['isAllowedExtensionsEnabled'] = data.pop('is_allowed_extensions_enabled')
        return data


class ImageQualityConfigSerializer(serializers.ModelSerializer):
    """
    Serializer untuk mengembalikan konfigurasi gambar tanpa kunci 'configs'.
    """

    class Meta:
        model = ImageQualityConfig
        fields = []  # Tidak perlu mendefinisikan fields karena kita menimpa representasi

    def to_representation(self, instance):
        """
        Menimpa metode untuk mengembalikan dictionary 'configs' secara langsung.
        """
        # instance.configs adalah field JSONField di model
        return instance.configs if instance.configs else {}


class WorkspaceGroupAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk endpoint /api/admin/groups
    - bisa untuk list, create, update
    - workspace diambil dari query param, jadi tidak dikirim di body
    """
    isDefault = serializers.BooleanField(source='is_default', required=False)

    class Meta:
        model = WorkspaceGroup
        fields = ['id', 'name', 'isDefault']


class GroupCreateAdminSerializer(serializers.ModelSerializer):
    """
    Serializer untuk POST /admin/groups.
    """
    name = serializers.CharField(write_only=True)
    workspace_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = WorkspaceGroup
        fields = ['name', 'workspace_id']

    def create(self, validated_data):
        name = validated_data.pop('name')
        workspace_id = validated_data.pop('workspace_id')
        django_group = DjangoGroup.objects.create(name=name)
        workspace_group = WorkspaceGroup.objects.create(
            group=django_group,
            workspace_id=workspace_id
        )
        return workspace_group

