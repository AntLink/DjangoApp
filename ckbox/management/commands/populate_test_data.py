from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import uuid
from ckbox.models import (
    EnvironmentConfig, WorkspaceTemplate, Workspace, WorkspaceMember,
    Category, Folder, Asset, WorkspaceGroup, Permission
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with demo data (for CKBox-style system)'

    def handle(self, *args, **options):
        self.stdout.write('=== Creating demo data ===')

        # 1️⃣ EnvironmentConfig
        env_config, _ = EnvironmentConfig.objects.get_or_create(
            pk=1,
            defaults={
                'allowed_extensions': [
                    'jpg', 'png', 'gif', 'pdf', 'doc', 'docx',
                    'xls', 'xlsx', 'ppt', 'pptx', 'txt'
                ],
                'is_allowed_extensions_enabled': True
            }
        )

        # 2️⃣ Template Workspace
        template, _ = WorkspaceTemplate.objects.get_or_create(
            name='Default Template',
            defaults={
                'categories_templates': [
                    {'name': 'Documents', 'extensions': ['pdf', 'doc', 'docx', 'txt']},
                    {'name': 'Images', 'extensions': ['jpg', 'png', 'gif']},
                    {'name': 'Spreadsheets', 'extensions': ['xls', 'xlsx']}
                ]
            }
        )

        # 3️⃣ Gunakan user ID yang sudah ada
        try:
            user1 = User.objects.get(id=1)
            user2 = User.objects.get(id=2)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ User dengan ID 1 dan 2 harus ada dulu di database"))
            return

        # 4️⃣ Buat workspace
        workspace1, _ = Workspace.objects.get_or_create(
            id=uuid.UUID('33afd884-1118-4049-a891-176def4d815d'),
            defaults={
                'name': 'Workspace Utama',
                'owner': user1,
                'created_from_template': template
            }
        )
        workspace2, _ = Workspace.objects.get_or_create(
            id=uuid.UUID('72943740-1a23-4c40-8c9e-05bb75d7efb3'),
            defaults={
                'name': 'Workspace Kedua',
                'owner': user2,
                'created_from_template': template
            }
        )

        # 5️⃣ Tambah member
        WorkspaceMember.objects.get_or_create(user=user1, workspace=workspace1)
        WorkspaceMember.objects.get_or_create(user=user2, workspace=workspace2)
        WorkspaceMember.objects.get_or_create(user=user2, workspace=workspace1)  # user2 ikut workspace1

        # 6️⃣ Buat kategori
        categories_data = [
            {'name': 'Documents', 'extensions': ['pdf', 'doc', 'docx', 'txt']},
            {'name': 'Images', 'extensions': ['jpg', 'png', 'gif']},
            {'name': 'Spreadsheets', 'extensions': ['xls', 'xlsx']}
        ]

        for workspace in [workspace1, workspace2]:
            for i, cat in enumerate(categories_data):
                Category.objects.get_or_create(
                    workspace=workspace,
                    name=cat['name'],
                    defaults={
                        'extensions': cat['extensions'],
                        'position': i
                    }
                )

        # 7️⃣ Grup & permission
        self.create_workspace_groups_and_permissions(workspace1)
        self.create_workspace_groups_and_permissions(workspace2)

        # 8️⃣ Folder & asset
        self.create_folders_and_assets(workspace1)
        self.create_folders_and_assets(workspace2)

        self.stdout.write(self.style.SUCCESS("✅ Demo data created successfully!"))

    # --- Fungsi bantu ---
    def create_workspace_groups_and_permissions(self, workspace):
        """Buat WorkspaceGroup dan Permission untuk tiap workspace."""
        group_defs = [
            ('Admin', True, {
                "category:access": True,
                "asset:create": True,
                "asset:read": True,
                "asset:delete": True,
                "folder:create": True,
                "folder:delete": True
            }),
            ('Editor', False, {
                "category:access": True,
                "asset:create": True,
                "asset:read": True,
                "asset:delete": False,
                "folder:create": True,
                "folder:delete": False
            }),
            ('Viewer', False, {
                "category:access": True,
                "asset:create": False,
                "asset:read": True,
                "asset:delete": False,
                "folder:create": False,
                "folder:delete": False
            }),
        ]

        for name, is_default, perm_list in group_defs:
            ws_group, _ = WorkspaceGroup.objects.get_or_create(
                workspace=workspace,
                name=name,
                defaults={'is_default': is_default}
            )

            categories = workspace.categories.all()
            permission, _ = Permission.objects.get_or_create(
                group=ws_group,
                defaults={'permissions_list': perm_list}
            )
            permission.categories.set(categories)

        self.stdout.write(self.style.SUCCESS(f'✅ Permissions created for {workspace.name}'))

    def create_folders_and_assets(self, workspace):
        """Buat folder dan beberapa file demo."""
        owner = workspace.owner

        # Ambil kategori
        cat_docs = workspace.categories.filter(name='Documents').first()
        cat_imgs = workspace.categories.filter(name='Images').first()

        # Root folder
        doc_folder, _ = Folder.objects.get_or_create(
            workspace=workspace,
            name='Documents',
            category=cat_docs,
            defaults={'created_by': owner}
        )
        img_folder, _ = Folder.objects.get_or_create(
            workspace=workspace,
            name='Images',
            category=cat_imgs,
            defaults={'created_by': owner}
        )

        # Subfolder
        reports_folder, _ = Folder.objects.get_or_create(
            workspace=workspace,
            name='Reports',
            parent=doc_folder,
            category=cat_docs,
            defaults={'created_by': owner}
        )

        # Demo asset
        assets = [
            ('Project Proposal', 'docx', 1024000, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', doc_folder, cat_docs),
            ('Financial Report', 'pdf', 512000, 'application/pdf', reports_folder, cat_docs),
            ('Team Photo', 'jpg', 2048000, 'image/jpeg', img_folder, cat_imgs),
        ]

        for name, ext, size, mime, folder, cat in assets:
            Asset.objects.get_or_create(
                workspace=workspace,
                name=name,
                extension=ext,
                defaults={
                    'size': size,
                    'mime_type': mime,
                    'folder': folder,
                    'category': cat,
                    'uploaded_by': owner,
                    'file': f'demo_files/{name}.{ext}'
                }
            )

        self.stdout.write(self.style.SUCCESS(f'📁 Created demo assets for {workspace.name}'))
