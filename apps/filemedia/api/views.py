from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Tags, Category, Folder, Media, Mediahastags
from .serializers import TagsSerializer, CategorySerializer, FolderSerializer, MediaSerializer, MediahastagsSerializer, MediaListSerializer

from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import mimetypes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.contrib.auth import get_user_model
from .serializers import CKBoxTokenObtainPairSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.conf import settings
import jwt
import datetime
import os
from PIL import Image
from django.http import FileResponse, Http404
import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.db.models import Q
from .serializers import MediaSearchSerializer
from .pagination import CustomPagination

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
User = get_user_model()

from rest_framework_simplejwt.views import TokenObtainPairView


class CKBoxTokenObtainPairView(TokenObtainPairView):
    serializer_class = CKBoxTokenObtainPairSerializer


class AdminViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=False, methods=['get','post'])
    def permissions(self, request):
        """Get permissions"""
        try:
            # Get semua categories
            from ..models import Category
            categories = Category.objects.all()

            # Build permissions response
            permissions_data = {
                'items': [{
                    "id": "0e0e66ca4edc",
                    "groupId": "0e0e66ca4edc",
                    "permissionsList": {
                        "category:access": True,
                        "asset:create": True,
                        "asset:delete": True,
                        "asset:metadata:modify": True,
                        "asset:overwrite": True,
                        "folder:create": True,
                        "folder:delete": True,
                        "folder:metadata:modify": True
                    }
                }]
            }

            return Response(permissions_data)

        except Exception as e:
            logger.error(f"Error getting permissions: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            "allowedExtensions": ["avi", "mov", "webm", "mp4", "mp3", "flac", "aac", "ogg","7z", "rar", "zip", "gz", "jpeg", "jpg", "png", "gif","bmp", "webp", "tiff", "doc", "docx", "ppt", "pptx","xls", "xlsx", "odt", "pdf", "txt", "svg"],
            "isAllowedExtensionsEnabled": True
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def images(self, request):
        data = {"default": {"defaultQuality": 80}}
        return Response(data)

    @action(detail=False, methods=['get'])
    def groups(self, request):
        data = {"items": [{"id": "f437cd41039d", "name": "Default", "isDefault": True}]}
        return Response(data)


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'status']
    search_fields = ['name', 'description']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk Category dengan custom pagination
    Tidak perlu override method apapun!
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_private']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'parent']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'favored', 'category', 'folder']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'size']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.action in ["retrieve", "thumbnail_detail"]:
            return [AllowAny()]  # tanpa auth untuk gambar
        return super().get_permissions()

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

            # Construct thumbnail path
            if not media.file:
                raise Http404("Media file not found")

            # Get the original file path
            original_path = media.file.path

            # Construct thumbnail path based on your storage structure
            file_dir = os.path.dirname(original_path)
            file_name = os.path.basename(original_path)

            # Your thumbnail directory structure
            thumb_dir = os.path.join(file_dir, 'thumbnail', str(size))
            thumb_path = os.path.join(thumb_dir, file_name)

            # Check if thumbnail exists
            if not os.path.exists(thumb_path):
                # If thumbnail doesn't exist, generate it on the fly
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
        if self.action in ['list', 'recent', 'trash', 'retrieve']:
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

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['get', 'post'], parser_classes=[JSONParser, FormParser, MultiPartParser])
    def trash(self, request):
        """
        GET  -> ambil semua media di trash (is_deleted=True)
        POST -> tandai media sebagai deleted (is_deleted=True)
        """
        if request.method == 'GET':
            trashed_media = Media.objects.filter(is_deleted=True)
            serializer = self.get_serializer(trashed_media, many=True, context={'request': request})
            return Response({
                'totalCount': trashed_media.count(),
                'items': serializer.data
            })

        elif request.method == 'POST':
            # Support JSON object {"ids": [1,2]} atau langsung array [1,2]
            media_ids = request.data

            if not media_ids:
                try:
                    body = request.body.decode('utf-8')
                    media_ids = json.loads(body)
                except Exception:
                    media_ids = []

            if not media_ids:
                return Response({'error': 'Media IDs required'}, status=status.HTTP_400_BAD_REQUEST)

            Media.objects.filter(id__in=media_ids).update(is_deleted=True)

            return Response({'status': 'deleted', 'ids': media_ids})

    @action(detail=False, methods=['post'], parser_classes=[JSONParser, FormParser, MultiPartParser])
    def restore(self, request):
        """
        Restore media dari trash (is_deleted=False)
        """
        media_ids = request.data.get('ids')

        if not media_ids:
            try:
                body = request.body.decode('utf-8')
                media_ids = json.loads(body)
            except Exception:
                media_ids = []

        if not media_ids:
            return Response({'error': 'Media IDs required'}, status=status.HTTP_400_BAD_REQUEST)

        Media.objects.filter(id__in=media_ids).update(is_deleted=False)

        return Response({'status': 'restored', 'ids': media_ids})

    @action(detail=False, methods=['delete'], parser_classes=[JSONParser, FormParser, MultiPartParser])
    def purge(self, request):
        """
        Hapus permanen dari database
        """
        media_ids = request.data.get('ids')

        if not media_ids:
            try:
                body = request.body.decode('utf-8')
                media_ids = json.loads(body)
            except Exception:
                media_ids = []

        if not media_ids:
            return Response({'error': 'Media IDs required'}, status=status.HTTP_400_BAD_REQUEST)

        Media.objects.filter(id__in=media_ids).delete()

        return Response({'status': 'purged', 'ids': media_ids})


class MediaThumbnailView(APIView):
    permission_classes = [AllowAny]  # Bisa diubah ke IsAuthenticated kalau private

    def get(self, request, pk, size, format=None):
        """
        Endpoint: /api/media/<pk>/thumbs/<size>.webp
        Contoh:   /api/media/367/thumbs/747x560.webp
        """
        try:
            media = Media.objects.get(pk=pk)
        except Media.DoesNotExist:
            raise Http404("Media not found")

        # Parse ukuran dari URL
        try:
            width, height = map(int, size.lower().replace(".webp", "").split("x"))
        except ValueError:
            raise Http404("Invalid size format, use WIDTHxHEIGHT.webp")

        # Lokasi file asli dan thumbnail
        src_path = media.file.path
        thumb_rel_path = f"thumbnails/{pk}/{width}x{height}.webp"
        thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_rel_path)

        # Kalau thumbnail belum ada → generate dulu
        if not os.path.exists(thumb_path):
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)

            try:
                with Image.open(src_path) as img:
                    img.thumbnail((width, height))
                    img.save(thumb_path, "WEBP")
            except Exception as e:
                raise Http404(f"Error generating thumbnail: {e}")

        # Return thumbnail
        return FileResponse(open(thumb_path, "rb"), content_type="image/webp")


class MediaSearchView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'search'
    pagination_class = CustomPagination

    def post(self, request, *args, **kwargs):
        search_phrase = request.data.get('searchPhrase', '')
        filters = request.data.get('filters', {})
        pagination_data = request.data.get('pagination', {})

        # Base queryset
        queryset = Media.objects.filter(is_deleted=False)

        # Search filter
        if search_phrase:
            queryset = queryset.filter(
                Q(name__icontains=search_phrase) |
                Q(description__icontains=search_phrase) |
                Q(tags__name__icontains=search_phrase)
            ).distinct()

        # Category filter
        categories = filters.get('categories', {}).get('in', [])
        if categories:
            queryset = queryset.filter(category__id__in=categories)

        # Extension filter
        extensions = filters.get('extensions', {}).get('in', [])
        if extensions:
            ext_queries = [Q(name__iendswith=f'.{ext}') for ext in extensions]
            queryset = queryset.filter(Q(*ext_queries))

        # Tags filter
        tags_in = filters.get('tags', {}).get('in', [])
        if tags_in:
            queryset = queryset.filter(tags__name__in=tags_in)

        # Uploaded date filter
        uploaded_at = filters.get('uploadedAt', {})
        uploaded_from = uploaded_at.get('from')
        if uploaded_from:
            queryset = queryset.filter(created_at__gte=uploaded_from)

        # Modified date filter
        last_modified_at = filters.get('lastModifiedAt', {})
        last_modified_from = last_modified_at.get('from')
        last_modified_to = last_modified_at.get('to')
        if last_modified_from and last_modified_to:
            queryset = queryset.filter(updated_at__range=(last_modified_from, last_modified_to))
        elif last_modified_from:
            queryset = queryset.filter(updated_at__gte=last_modified_from)
        elif last_modified_to:
            queryset = queryset.filter(updated_at__lte=last_modified_to)

        # Sorting
        sort_by = pagination_data.get('sortBy', 'updated_at')
        order = pagination_data.get('order', 'desc')

        sort_mapping = {
            'lastModifiedAt': 'updated_at',
            'uploadedAt': 'created_at',
            'name': 'name',
            'size': 'size'
        }
        sort_field = sort_mapping.get(sort_by, 'updated_at')
        if order == 'desc':
            sort_field = f'-{sort_field}'
        queryset = queryset.order_by(sort_field)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        context = {'request': request}
        if page is not None:
            serializer = MediaSearchSerializer(page, many=True, context=context)
            return paginator.get_paginated_response(serializer.data)

        serializer = MediaSearchSerializer(queryset, many=True, context=context)
        return Response({
            'items': serializer.data,
            'limit': pagination_data.get('limit', 50),
            'offset': pagination_data.get('offset', 0),
            'totalCount': queryset.count()
        }, status=status.HTTP_200_OK)


class MediahastagsViewSet(viewsets.ModelViewSet):
    queryset = Mediahastags.objects.all()
    serializer_class = MediahastagsSerializer
    permission_classes = [IsAuthenticated]


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet untuk endpoint autentikasi dan otorisasi
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """
        Override untuk memberi permission berbeda per-action
        """
        if self.action in ['ckbox_login', 'register']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'])
    def ckbox_login(self, request):
        """
        Endpoint untuk login user dan mendapatkan token JWT khusus CKBox
        """
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Gunakan custom serializer untuk CKBox
        refresh = CKBoxTokenObtainPairSerializer.get_token(user)
        access_token = refresh.access_token

        # Ambil nilai lifetime dari settings SimpleJWT
        access_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
        refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

        return Response({
            'refresh': str(refresh),
            'access': str(access_token),
            'access_token_lifetime': int(access_lifetime.total_seconds()),
            'refresh_token_lifetime': int(refresh_lifetime.total_seconds()),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })

    @action(detail=False, methods=['post'])
    def ckbox_token_refresh(self, request):
        """
        Refresh token khusus untuk CKBox
        """
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            user = User.objects.get(id=user_id)

            # Buat access baru
            access_token = refresh.access_token

            # Ambil nilai lifetime dari settings SimpleJWT
            access_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
            refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

            return Response({
                'refresh': str(refresh),  # ⬅️ ditambahkan biar sama dengan login
                'access': str(access_token),
                'access_token_lifetime': int(access_lifetime.total_seconds()),
                'refresh_token_lifetime': int(refresh_lifetime.total_seconds()),
                'user': {  # ⬅️ ditambahkan biar sama dengan login
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        except Exception:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Endpoint untuk login user dan mendapatkan token JWT biasa
        """
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        # Ambil nilai lifetime dari settings SimpleJWT
        access_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
        refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'access_token_lifetime': int(access_lifetime.total_seconds()),
            'refresh_token_lifetime': int(refresh_lifetime.total_seconds()),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })

    @action(detail=False, methods=['post'])
    def token_refresh(self, request):
        """
        Refresh token umum (biasa)
        """
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)

            # Ambil nilai lifetime dari settings SimpleJWT
            access_lifetime = api_settings.ACCESS_TOKEN_LIFETIME

            return Response({
                'access': str(refresh.access_token),
                'access_token_lifetime': int(access_lifetime.total_seconds())
            })
        except Exception as e:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Endpoint untuk registrasi user baru
        """
        from .serializers import UserSerializer

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            # Ambil nilai lifetime dari settings SimpleJWT
            access_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
            refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'access_token_lifetime': int(access_lifetime.total_seconds()),
                'refresh_token_lifetime': int(refresh_lifetime.total_seconds()),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        data = {"items": [{"id": 12, "name": "Dangger"},{"id": 1, "name": "test 2"}]}
        return Response(data)

    @action(detail=False, methods=['get'])
    def token(self, request):
        """Generate JWT token (untuk compatibility dengan existing code)"""
        try:
            # Generate payload sesuai contoh
            payload = {
                'sub': 'ckbox-demo',
                'iat': int(datetime.datetime.utcnow().timestamp()),
                'aud': 'zBGplCJ8k9Ds5SL0cyno',
                'auth': {
                    'ckbox': {
                        'role': 'admin',
                        'workspaces': [12]
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

    @action(detail=False, methods=['post'])
    def authorizeprivateaccess(self, request):
        payload = {
            "aud": "ckbox",
            "sub": "ckbox-demo",  # contoh static
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            "auth": {
                "ckbox": {
                    "role": "admin",  # bisa juga "user"
                    "workspaces": ["default"]
                }
            }
        }

        token = jwt.encode(payload, settings.CKBOX_SECRET, algorithm="HS256")

        response = HttpResponse(status=204)
        response.set_cookie(
            key="CKBox-Auth",
            value=token,
            httponly=True,
            secure=not settings.DEBUG,  # True di production
            samesite="Strict",
        )
        return response

    @action(detail=False, methods=['get'])
    def permissions(self, request):
        """Get permissions"""
        try:
            # Get semua categories
            from ..models import Category
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

class SuperAdminWorkspacesTemplateView(APIView):
    permission_classes = []  # kalau mau tanpa login, bisa pakai []

    def get(self, request):
        data = {
            "categoriesTemplates": [
                {
                    "name": "Images",
                    "extensions": ["jpeg", "jpg", "png", "gif", "bmp", "webp", "tiff"]
                },
                {
                    "name": "Files",
                    "extensions": [
                        "jpg","png","jpeg","gif","webp","bmp","tiff",
                        "avi","mov","webm","mp4","mp3","flac","aac","ogg",
                        "7z","rar","zip","gz","doc","docx","ppt","pptx",
                        "xls","xlsx","odt","pdf","txt"
                    ]
                },
                {
                    "name": "Documents",
                    "extensions": ["doc","docx","ppt","pptx","xls","xlsx","odt","pdf","txt"]
                }
            ]
        }
        return Response(data, status=status.HTTP_200_OK)


class WorkspaceMetadataView(APIView):
    def get(self, request, *args, **kwargs):
        # bisa ambil workspaceId dari query param kalau mau dinamis
        workspace_id = request.GET.get("workspaceId", "ws_12345")
        data = {
            "status": "ok"
        }
        return Response(data, status=status.HTTP_200_OK)
