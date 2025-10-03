# myapp/management/commands/populate_demo.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import random

from ckbox.models import (
    EnvironmentConfig, WorkspaceTemplate, Workspace, WorkspaceMember,
    Category, Folder, Asset, RecentAsset, WorkspaceGroup, Permission
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with demo data'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')

        # 1. Create EnvironmentConfig
        env_config, created = EnvironmentConfig.objects.get_or_create(
            pk=1,
            defaults={
                'allowed_extensions': ['jpg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'],
                'is_allowed_extensions_enabled': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created EnvironmentConfig'))

        # 2. Create WorkspaceTemplate
        template, created = WorkspaceTemplate.objects.get_or_create(
            name='Default Template',
            defaults={
                'categories_templates': [
                    {'name': 'Documents', 'extensions': ['pdf', 'doc', 'docx', 'txt']},
                    {'name': 'Images', 'extensions': ['jpg', 'png', 'gif']},
                    {'name': 'Spreadsheets', 'extensions': ['xls', 'xlsx']}
                ]
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created WorkspaceTemplate'))

        # 3. Create Users
        user1, created = User.objects.get_or_create(
            username='demo_user1',
            defaults={
                'email': 'user1@example.com',
                'first_name': 'Demo',
                'last_name': 'User1'
            }
        )
        if created:
            user1.set_password('password123')
            user1.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {user1.username}'))

        user2, created = User.objects.get_or_create(
            username='demo_user2',
            defaults={
                'email': 'user2@example.com',
                'first_name': 'Demo',
                'last_name': 'User2'
            }
        )
        if created:
            user2.set_password('password123')
            user2.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {user2.username}'))

        # 4. Create Workspaces
        workspace1, created = Workspace.objects.get_or_create(
            id=uuid.UUID('33afd884-1118-4049-a891-176def4d815d'),
            defaults={
                'name': 'Workspace Utama',
                'owner': user1,
                'created_from_template': template
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created workspace: {workspace1.name}'))

        workspace2, created = Workspace.objects.get_or_create(
            id=uuid.UUID('72943740-1a23-4c40-8c9e-05bb75d7efb3'),
            defaults={
                'name': 'Workspace Kedua',
                'owner': user2,
                'created_from_template': template
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created workspace: {workspace2.name}'))

        # 5. Add members to workspaces
        WorkspaceMember.objects.get_or_create(user=user1, workspace=workspace1)
        WorkspaceMember.objects.get_or_create(user=user2, workspace=workspace2)
        WorkspaceMember.objects.get_or_create(user=user2, workspace=workspace1)  # user2 is also member of workspace1

        # 6. Create Categories for each workspace
        categories_data = [
            {'name': 'Documents', 'extensions': ['pdf', 'doc', 'docx', 'txt']},
            {'name': 'Images', 'extensions': ['jpg', 'png', 'gif']},
            {'name': 'Spreadsheets', 'extensions': ['xls', 'xlsx']}
        ]

        for workspace in [workspace1, workspace2]:
            for i, cat_data in enumerate(categories_data):
                category, created = Category.objects.get_or_create(
                    workspace=workspace,
                    name=cat_data['name'],
                    defaults={
                        'extensions': cat_data['extensions'],
                        'position': i
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created category: {category.name} in {workspace.name}'))

        # 7. Create WorkspaceGroups and Permissions
        self.create_workspace_groups_and_permissions(workspace1)
        self.create_workspace_groups_and_permissions(workspace2)

        # 8. Create Folders and Assets (optional)
        self.create_folders_and_assets(workspace1)
        self.create_folders_and_assets(workspace2)

        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))

    def create_workspace_groups_and_permissions(self, workspace):
        # Create Django Groups
        admin_group, _ = DjangoGroup.objects.get_or_create(name=f'{workspace.name}_Admin')
        editor_group, _ = DjangoGroup.objects.get_or_create(name=f'{workspace.name}_Editor')
        viewer_group, _ = DjangoGroup.objects.get_or_create(name=f'{workspace.name}_Viewer')

        # Create WorkspaceGroups
        ws_admin, _ = WorkspaceGroup.objects.get_or_create(
            workspace=workspace,
            group=admin_group
        )
        ws_editor, _ = WorkspaceGroup.objects.get_or_create(
            workspace=workspace,
            group=editor_group
        )
        ws_viewer, _ = WorkspaceGroup.objects.get_or_create(
            workspace=workspace,
            group=viewer_group
        )

        # Get all categories for this workspace
        categories = workspace.categories.all()

        # Create Permissions for Admin Group
        admin_permissions, _ = Permission.objects.get_or_create(
            group=ws_admin,
            defaults={
                'permissions_list': {
                    "category:access": True,
                    "asset:create": True,
                    "asset:read": True,
                    "asset:delete": True,
                    "folder:create": True,
                    "folder:delete": True
                }
            }
        )
        admin_permissions.categories.set(categories)

        # Create Permissions for Editor Group
        editor_permissions, _ = Permission.objects.get_or_create(
            group=ws_editor,
            defaults={
                'permissions_list': {
                    "category:access": True,
                    "asset:create": True,
                    "asset:read": True,
                    "asset:delete": False,
                    "folder:create": True,
                    "folder:delete": False
                }
            }
        )
        editor_permissions.categories.set(categories)

        # Create Permissions for Viewer Group
        viewer_permissions, _ = Permission.objects.get_or_create(
            group=ws_viewer,
            defaults={
                'permissions_list': {
                    "category:access": True,
                    "asset:create": False,
                    "asset:read": True,
                    "asset:delete": False,
                    "folder:create": False,
                    "folder:delete": False
                }
            }
        )
        viewer_permissions.categories.set(categories)

        self.stdout.write(self.style.SUCCESS(f'Created permissions for {workspace.name}'))

    def create_folders_and_assets(self, workspace):
        # Get categories
        doc_category = workspace.categories.get(name='Documents')
        img_category = workspace.categories.get(name='Images')

        # Create root folders
        doc_folder, _ = Folder.objects.get_or_create(
            workspace=workspace,
            name='Documents',
            category=doc_category,
            defaults={'created_by': workspace.owner}
        )

        img_folder, _ = Folder.objects.get_or_create(
            workspace=workspace,
            name='Images',
            category=img_category,
            defaults={'created_by': workspace.owner}
        )

        # Create subfolders
        reports_folder, _ = Folder.objects.get_or_create(
            workspace=workspace,
            name='Reports',
            parent=doc_folder,
            category=doc_category,
            defaults={'created_by': workspace.owner}
        )

        # Create demo assets (without actual files)
        demo_assets = [
            {
                'name': 'Project Proposal',
                'extension': 'docx',
                'size': 1024000,
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'folder': doc_folder,
                'category': doc_category
            },
            {
                'name': 'Financial Report',
                'extension': 'pdf',
                'size': 512000,
                'mime_type': 'application/pdf',
                'folder': reports_folder,
                'category': doc_category
            },
            {
                'name': 'Team Photo',
                'extension': 'jpg',
                'size': 2048000,
                'mime_type': 'image/jpeg',
                'folder': img_folder,
                'category': img_category
            }
        ]

        for asset_data in demo_assets:
            asset, created = Asset.objects.get_or_create(
                workspace=workspace,
                name=asset_data['name'],
                extension=asset_data['extension'],
                defaults={
                    'size': asset_data['size'],
                    'mime_type': asset_data['mime_type'],
                    'folder': asset_data['folder'],
                    'category': asset_data['category'],
                    'uploaded_by': workspace.owner,
                    'file': f'demo_files/{asset_data["name"]}.{asset_data["extension"]}'  # Dummy path
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created asset: {asset.name}'))