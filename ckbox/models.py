# myapp/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Group as DjangoGroup
from django.core.exceptions import ValidationError
from django.conf import settings


# --- Model User (Opsional, jika ingin kustom) ---
# Jika Anda ingin menggunakan ini, uncomment dan ubah AUTH_USER_MODEL di settings.py
# class User(AbstractUser):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# --- Model Konfigurasi Sistem (Superadmin) ---

class EnvironmentConfig(models.Model):
    """Model untuk menyimpan konfigurasi global aplikasi. Dikelola oleh superadmin."""

    def clean(self):
        if EnvironmentConfig.objects.exists() and not self.pk:
            raise ValidationError("Hanya boleh ada satu konfigurasi lingkungan.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    allowed_extensions = models.JSONField(default=list, blank=True, help_text="Ekstensi file yang diizinkan.")
    is_allowed_extensions_enabled = models.BooleanField(default=True)

    def __str__(self):
        return "Environment Configuration"


class WorkspaceTemplate(models.Model):
    """Template untuk membuat workspace baru dengan struktur awal. Dikelola oleh superadmin."""
    name = models.CharField(max_length=255)
    categories_templates = models.JSONField(default=list, blank=True, help_text="Daftar template kategori.")

    def __str__(self):
        return self.name


# myapp/models.py

# ... model lainnya ...

class ImageQualityConfig(models.Model):
    """
    Model untuk menyimpan konfigurasi kualitas gambar per format.
    Hanya boleh ada satu instance dari model ini.
    """

    def clean(self):
        if ImageQualityConfig.objects.exists() and not self.pk:
            raise ValidationError("Hanya boleh ada satu konfigurasi kualitas gambar.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    configs = models.JSONField(
        default=dict,
        help_text="Konfigurasi kualitas gambar, contoh: {'default': {'defaultQuality': 70}, 'png': {'defaultQuality': 90}}"
    )

    def __str__(self):
        return "Image Quality Configuration"


# --- Model Inti ---
class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_workspaces')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='WorkspaceMember', related_name='workspaces')
    created_at = models.DateTimeField(auto_now_add=True)
    created_from_template = models.ForeignKey(WorkspaceTemplate, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    date_joined = models.DateTimeField(auto_now_add=True)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='categories')
    extensions = models.JSONField(default=list, blank=True)
    position = models.PositiveIntegerField(default=0)
    isPrivate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('name', 'workspace')
        ordering = ['position']


class Folder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='folders')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('name', 'parent', 'workspace')


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)  # Nama tanpa ekstensi
    extension = models.CharField(max_length=10)
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    file = models.FileField(upload_to='ckbox_assets/')

    # Relasi
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='assets')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # width, height, description, customAttributes

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Soft Delete
    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']


class RecentAsset(models.Model):
    """Model untuk melacak aset yang baru saja diakses oleh setiap pengguna."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recent_assets')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'asset')
        ordering = ['-accessed_at']


# --- Model Perizinan (Admin) ---

class WorkspaceGroup(models.Model):
    """Model untuk menambahkan relasi workspace ke Group bawaan Django."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.OneToOneField(DjangoGroup, on_delete=models.CASCADE, related_name='workspace_profile')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='workspace_groups')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.group.name} in {self.workspace.name}"


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(WorkspaceGroup, on_delete=models.CASCADE, related_name='permission_rules')
    categories = models.ManyToManyField(Category, related_name='permission_rules')
    permissions_list = models.JSONField(default=dict)  # Contoh: {"asset:create": True, "folder:delete": False}
