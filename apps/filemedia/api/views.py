from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Tags, Category, Folder, Media, Mediahastags
from .serializers import TagsSerializer, CategorySerializer, FolderSerializer, MediaSerializer, MediahastagsSerializer, MediaListSerializer
from .pagination import CustomPagination
from rest_framework.response import Response
import jwt
import datetime
from django.conf import settings
from rest_framework import status, views
from rest_framework.decorators import action

from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging
import os
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from wsgiref.util import FileWrapper
import mimetypes

logger = logging.getLogger(__name__)

class AdminViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Mengembalikan data kategori dari model Category
        Format response:
        {
            "totalCount": 3,
            "offset": 0,
            "limit": 500,
            "items": [...]
        }
        """
        try:
            # Import model di sini untuk menghindari circular import


            # Ambil semua kategori dari model
            categories = Category.objects.all().order_by('position')

            # Get pagination parameters
            limit = int(request.GET.get('limit', 500))
            offset = int(request.GET.get('offset', 0))

            # Hitung total count
            total_count = categories.count()

            # Apply pagination
            categories = categories[offset:offset + limit]

            # Transform data ke format yang diinginkan
            categories_data = []
            for category in categories:
                # Parse extensions JSON string ke array
                extensions_list = []
                if category.extensions:
                    try:
                        extensions_list = json.loads(category.extensions)
                    except json.JSONDecodeError:
                        # Jika bukan JSON valid, jadikan array dengan 1 elemen
                        extensions_list = [category.extensions] if category.extensions else []

                categories_data.append({
                    "id": str(category.id),
                    "name": category.name,
                    "position": category.position,
                    "assetsCount": category.get_assets_count(),
                    "totalAssetsCount": category.get_total_assets_count(),
                    "extensions": extensions_list,
                    "isPrivate": category.is_private
                })

            # Format response sesuai keinginan
            response_data = {
                "totalCount": total_count,
                "offset": offset,
                "limit": limit,
                "items": categories_data
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in categories endpoint: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['get'])
    def environmentConfig(self, request):
        data = {
            "allowedExtensions": [
                "avi",
                "mov",
                "webm",
                "mp4",
                "mp3",
                "flac",
                "aac",
                "ogg",
                "7z",
                "rar",
                "zip",
                "gz",
                "jpeg",
                "jpg",
                "png",
                "gif",
                "bmp",
                "webp",
                "tiff",
                "doc",
                "docx",
                "ppt",
                "pptx",
                "xls",
                "xlsx",
                "odt",
                "pdf",
                "txt",
                "svg"
            ],
            "isAllowedExtensionsEnabled": True
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def images(self,request):
        data = {"default":{"defaultQuality":80}}
        return Response(data)

    @action(detail=False, methods=['get'])
    def groups(self, request):
        data = {"items":[{"id":"f437cd41039d","name":"Default","isDefault":True}]}
        return Response(data)

class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'status']
    search_fields = ['name', 'description']


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk Category dengan custom pagination
    Tidak perlu override method apapun!
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPagination  # Cukup ini saja!
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_private']


class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'parent']


class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'favored', 'category', 'folder']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'size']

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve method to handle thumbnail requests"""
        # Check if this is a thumbnail request
        thumb_type = request.query_params.get('type')
        size_param = request.query_params.get('size')

        if thumb_type == 'thumbs' and size_param:
            return self.serve_thumbnail(request, kwargs.get('pk'), size_param)

        # Default behavior for normal retrieve
        return super().retrieve(request, *args, **kwargs)

    def serve_thumbnail(self, request, media_id, size):
        """Serve thumbnail image file directly"""
        try:
            # Get media object
            media = get_object_or_404(Media, id=media_id)
            size_int = int(size)
            # Validate size parameter
            # try:
            #     size_int = int(size)
            #     if size_int not in [160, 320, 384, 280, 373, 507, 533, 538, 498, 480, 640, 800, 960, 1120, 1280, 1440, 1600,1920]:
            #         return HttpResponse("Invalid size parameter", status=400)
            # except ValueError:
            #     return HttpResponse("Size must be a number", status=400)

            # Construct thumbnail path
            if not media.file:
                raise Http404("Media file not found")

            # Get the original file path
            original_path = media.file.path

            # Construct thumbnail path based on your storage structure
            # Assuming thumbnails are stored in: media_root/thumbnail/{size}/filename
            file_dir = os.path.dirname(original_path)
            file_name = os.path.basename(original_path)

            # Your thumbnail directory structure
            thumb_dir = os.path.join(file_dir, 'thumbnail', str(size))
            thumb_path = os.path.join(thumb_dir, file_name)

            # Alternative path if using different structure
            # thumb_path = os.path.join(settings.MEDIA_ROOT, 'thumbnail', str(size), file_name)

            # Check if thumbnail exists
            if not os.path.exists(thumb_path):
                # If thumbnail doesn't exist, you might want to generate it on the fly
                # or return the original image as fallback
                return self.generate_or_fallback_thumbnail(media, thumb_path, size_int, original_path)

            # Serve the thumbnail file
            return self.serve_file(thumb_path)

        except Media.DoesNotExist:
            raise Http404("Media not found")
        except Exception as e:
            return HttpResponse(f"Error serving thumbnail: {str(e)}", status=500)

    def generate_or_fallback_thumbnail(self, media, thumb_path, size, original_path):
        """Generate thumbnail on the fly or return fallback"""
        from apps.filemedia.images import ManageImage
        try:
            # Try to generate thumbnail on the fly
            manager = ManageImage()

            # Create thumbnail directory if it doesn't exist
            thumb_dir = os.path.dirname(thumb_path)
            os.makedirs(thumb_dir, exist_ok=True)

            # Generate thumbnail
            manager.resize_image_thumb(original_path, thumb_path, size)

            # Serve the newly generated thumbnail
            return self.serve_file(thumb_path)

        except Exception as e:
            # If generation fails, serve original image as fallback
            print(f"Thumbnail generation failed, serving original: {str(e)}")
            return self.serve_file(original_path)

    def serve_file(self, file_path):
        """Serve file with proper headers"""
        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Get file info
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Determine content type
        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        # Create response with file
        response = HttpResponse(content_type=content_type)
        response['Content-Length'] = file_size
        response['Content-Disposition'] = f'inline; filename="{file_name}"'

        # Cache headers (1 day cache)
        response['Cache-Control'] = 'public, max-age=86400'

        # Write file to response
        with open(file_path, 'rb') as file:
            response.write(file.read())

        return response

    @action(detail=True, methods=['get'], url_path='thumbnail')
    def thumbnail_detail(self, request, pk=None):
        """Alternative endpoint for thumbnail: /api/media/{id}/thumbnail/?size=480"""
        size = request.query_params.get('size', '480')
        return self.serve_thumbnail(request, pk, size)

    def get_serializer_class(self):
        if self.action in ['list', 'recent', 'trash','retrieve']:
            return MediaListSerializer
        return MediaSerializer

    def list(self, request, *args, **kwargs):
        # Extract query parameters
        category_id = request.query_params.get('categoryId')
        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 10))
        sort_by = request.query_params.get('sortBy', 'lastModifiedAt')
        order = request.query_params.get('order', 'desc')
        workspace_id = request.query_params.get('workspaceId')

        # Start with base queryset
        queryset = Media.objects.filter(is_deleted=False)

        # Apply category filter if provided
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Apply sorting
        sort_mapping = {
            'lastModifiedAt': 'updated_at',
            'name': 'name',
            'size': 'size'
        }
        sort_field = sort_mapping.get(sort_by, 'updated_at')
        if order == 'desc':
            sort_field = f'-{sort_field}'
        queryset = queryset.order_by(sort_field)

        # Get total count before pagination
        total_count = queryset.count()

        # Apply pagination
        end = offset + limit
        queryset = queryset[offset:end]

        # Serialize data
        serializer = self.get_serializer(queryset, many=True, context={'request': request})

        # Format response
        response_data = {
            'totalCount': total_count,
            'offset': offset,
            'limit': limit,
            'items': serializer.data
        }

        return Response(response_data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent media (last 10 items)"""
        recent_media = Media.objects.filter(is_deleted=False).order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_media, many=True, context={'request': request})

        response_data = {
            'totalCount': recent_media.count(),
            'offset': 0,
            'limit': 10,
            'items': serializer.data
        }
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def trash(self, request):
        """Get deleted media"""
        trashed_media = Media.objects.filter(is_deleted=True)
        serializer = self.get_serializer(trashed_media, many=True, context={'request': request})

        response_data = {
            'totalCount': trashed_media.count(),
            'offset': 0,
            'limit': trashed_media.count(),
            'items': serializer.data
        }
        return Response(response_data)


class MediahastagsViewSet(viewsets.ModelViewSet):
    queryset = Mediahastags.objects.all()
    serializer_class = MediahastagsSerializer


@method_decorator(csrf_exempt, name='dispatch')
class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet untuk endpoint autentikasi dan otorisasi
    """
    permission_classes = [AllowAny]  # Tambahkan ini untuk bypass autentikasi
    authentication_classes = []

    @action(detail=False, methods=['get'])
    def limits(self, request):
        data = {
            "maxImageInMegapixelsLimit": 50,
            "maxFileSizeInBytesLimit": 50000000,
            "pricingPlanName": "ckbox.pro",
            "isMaxBandwidthExceeded": False,
            "isMaxStorageSizeExceeded": False
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def workspaces(self, request):
        data = {"items": [{"id": "b31838d7db045edd5b6c", "name": "ckbox-demo-workspace-DGMh-pql"}]}
        return Response(data)

    @action(detail=False, methods=['get'])
    def token(self, request):
        """Generate JWT token"""
        try:
            # Generate payload sesuai contoh
            payload = {
                'sub': 'ckbox-demo',
                'iat': int(datetime.datetime.utcnow().timestamp()),
                'aud': 'zBGplCJ8k9Ds5SL0cyno',
                'auth': {
                    'ckbox': {
                        'role': 'admin',
                        'workspaces': ['b31838d7db045edd5b6c']
                    }
                },
                'jti': 'ntdvAIeckoD6TvC5VjeRrNxGik_QkMqda'
            }

            # Generate token dengan secret key
            secret_key = getattr(settings, 'JWT_SECRET_KEY', 'your-secret-key-here')
            token = jwt.encode(payload, secret_key, algorithm='HS256')

            # Return response dengan format yang diminta
            return Response({
                'file': token
            })

        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post'])
    def authorizeprivateaccess(self, request):
        """Authorize private access"""
        token = request.data.get('token', '')

        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # secret_key = getattr(settings, 'JWT_SECRET_KEY', 'your-secret-key-here')
        # try:
        #     payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        # except jwt.ExpiredSignatureError:
        #     return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)
        # except jwt.InvalidTokenError:
        #     return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'status': 'authorized',
            'message': 'Private access granted'
        })

    @action(detail=False, methods=['get'])
    def permissions(self, request):
        """Get permissions"""
        try:
            # Get semua categories

            categories = Category.objects.all()

            # Build permissions response
            permissions_data = {}

            for category in categories:
                # Set permissions untuk setiap category
                permissions_data[str(category.id)] = {
                    "category:access": True,
                    "asset:create": True,
                    "asset:delete": True,
                    "asset:metadata:modify": True,
                    "asset:overwrite": True,
                    "folder:create": True,
                    "folder:delete": True,
                    "folder:metadata:modify": True
                }

            return Response(permissions_data)

        except Exception as e:
            logger.error(f"Error getting permissions: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
