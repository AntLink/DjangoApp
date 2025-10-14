# assets/tasks.py

import os
from PIL import Image as PilImage
from blurhash import encode
from celery import shared_task
from django.conf import settings
from .models import Asset


@shared_task
def process_asset_file(asset_id):
    """
    Tugas untuk memproses file yang diunggah:
    - Mengekstrak metadata (dimensi, blurhash)
    - Membuat thumbnail dan menyimpan URL-nya di metadata
    """
    try:
        asset = Asset.objects.get(id=asset_id)
        file_path = asset.file.path

        # Pastikan direktori untuk thumbnail ada
        asset_dir = os.path.dirname(file_path)
        image_dir = os.path.join(asset_dir, 'images')
        os.makedirs(image_dir, exist_ok=True)

        if asset.mime_type.startswith('image/'):
            with PilImage.open(file_path) as img:
                width, height = img.size

                # 1. Generate BlurHash
                try:
                    img_copy = img.copy()
                    img_copy.thumbnail((32, 32))
                    blurhash_str = encode(img_copy, x_components=4, y_components=3)
                except Exception:
                    blurhash_str = None

                # 2. Buat Thumbnail dan URL
                image_urls = {}
                thumbnail_sizes = {'80': 'webp', '160': 'webp', '240': 'webp', 'default': 'png'}

                for size_name, format_ext in thumbnail_sizes.items():
                    size_pixels = int(size_name)
                    thumb = img.copy()
                    thumb.thumbnail((size_pixels, size_pixels), PilImage.Resampling.LANCZOS)

                    thumb_filename = f"{size_name}.{format_ext}"
                    thumb_path = os.path.join(image_dir, thumb_filename)
                    thumb.save(thumb_path, format_ext.upper() if format_ext != 'webp' else 'WEBP')

                    # Buat URL relatif
                    relative_path = os.path.relpath(thumb_path, settings.MEDIA_ROOT)
                    image_urls[size_name] = f"{settings.MEDIA_URL}{relative_path.replace(os.sep, '/')}"

                # 3. Update metadata
                asset.metadata.update({
                    'width': width,
                    'height': height,
                    'blurHash': blurhash_str,
                    'imageUrls': image_urls,  # URL disimpan di metadata
                    'metadataProcessingStatus': 'success'
                })
                asset.save(update_fields=['metadata', 'last_modified_at'])
        else:
            asset.metadata.update({'metadataProcessingStatus': 'success'})
            asset.save(update_fields=['metadata', 'last_modified_at'])

    except Asset.DoesNotExist:
        print(f"Asset with id {asset_id} not found.")
    except Exception as e:
        print(f"Error processing asset {asset_id}: {e}")
        try:
            asset = Asset.objects.get(id=asset_id)
            asset.metadata.update({'metadataProcessingStatus': 'failed', 'error': str(e)})
            asset.save(update_fields=['metadata', 'last_modified_at'])
        except Asset.DoesNotExist:
            pass
