# accounts/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
import uuid
import os
from django.conf import settings
from PIL import Image


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_POST, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class UploadProfileImageView(View):
    def post(self, request):
        try:
            if 'photo' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'Tidak ada file yang diupload'}, status=400)

            image_file = request.FILES['photo']

            # Validasi file
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'File harus berupa gambar'}, status=400)

            if image_file.size > 5 * 1024 * 1024:  # 5MB
                return JsonResponse({'success': False, 'error': 'Ukuran file terlalu besar. Maksimal 5MB.'}, status=400)

            # Nama file unik
            ext = os.path.splitext(image_file.name)[1].lower()
            file_name = f"profile_{uuid.uuid4().hex}{ext}"
            save_dir = os.path.join(settings.MEDIA_ROOT, 'photo')
            os.makedirs(save_dir, exist_ok=True)

            file_path = os.path.join(save_dir, file_name)

            # Buka dengan Pillow
            img = Image.open(image_file)

            # Konversi ke RGB kalau gambar mode lain (PNG bisa pakai RGBA)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize max 1080px (biar nggak terlalu besar)
            img.thumbnail((1080, 1080))
            img.save(file_path, quality=90)

            # Buat thumbnail 200x200
            thumb_name = f"thumb_{file_name}"
            thumb_path = os.path.join(save_dir, thumb_name)

            thumb_img = img.copy()
            thumb_img.thumbnail((200, 200))
            thumb_img.save(thumb_path, quality=85)

            # Update user profile
            if hasattr(request.user, 'profile'):
                # Hapus foto lama kalau ada
                if request.user.profile.photo:
                    old_image_path = os.path.join(settings.MEDIA_ROOT, request.user.profile.photo.name)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

                request.user.profile.photo.name = f'photo/{file_name}'
                request.user.profile.save()

            image_url = f"{settings.MEDIA_URL}photo/{file_name}"
            thumb_url = f"{settings.MEDIA_URL}photo/{thumb_name}"

            return JsonResponse({
                'success': True,
                'message': 'Upload berhasil',
                'image_url': image_url,
                'thumb_url': thumb_url
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Terjadi kesalahan: {str(e)}'}, status=500)
