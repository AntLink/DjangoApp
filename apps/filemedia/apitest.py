from nifty.modeladmin import Admin
from functools import update_wrapper
from django.urls import reverse_lazy
from django.http import HttpResponse
import json


class ApiAdmin(Admin):
    def get_urls(self):
        from django.urls import path
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            path('', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            path('categories', wrap(self.categories), name='%s_%s_categories' % info),
            path('categories/<path:obj_id>', wrap(self.categories_id), name='%s_%s_categories_id' % info),
            path('auth/authorizePrivateAccess', wrap(self.auth), name='%s_%s_auth' % info),
            path('v2/workspaces', wrap(self.workspaces), name='%s_%s_workspaces' % info),
            path('limits', wrap(self.limits), name='%s_%s_limits' % info),
            path('permissions', wrap(self.permissions), name='%s_%s_permissions' % info),
            path('folders', wrap(self.folders), name='%s_%s_folders' % info),
            path('folders/id/<path:obj_id>', wrap(self.foldersid), name='%s_%s_folders' % info),
            path('assets', wrap(self.allassets), name='%s_%s_assets_all' % info),
            path('assets/id/<path:obj_id>', wrap(self.getassets), name='%s_%s_assets_id' % info),
            # path('assets/up/', wrap(self.allassets), name='%s_%s_assets' % info),
            path('assets/recent', wrap(self.recent), name='%s_%s_recent' % info),
            path('assets/trash', wrap(self.trash), name='%s_%s_trash' % info),
            path('admin/categories', wrap(self.admincategories), name='%s_%s_admin_categories' % info),
            path('admin/environmentConfig', wrap(self.adminconfig), name='%s_%s_admin_config' % info),
            path('admin/images', wrap(self.adminimages), name='%s_%s_admin_images' % info),
            path('admin/groups', wrap(self.admingroups), name='%s_%s_admin_groups' % info),
            path('admin/permissions', wrap(self.adminpermissions), name='%s_%s_admin_permissions' % info),
        ]
        return urlpatterns

    from django.views.decorators.csrf import csrf_exempt
    @csrf_exempt
    def auth(self, request):
        store = {

            "1": {
                "category:access": True,
                "asset:create": True,
                "asset:delete": True,
                "asset:metadata:modify": True,
                "asset:overwrite": True,
                "folder:create": True,
                "folder:delete": True,
                "folder:metadata:modify": True
            },
            "2": {
                "category:access": True,
                "asset:create": True,
                "asset:delete": True,
                "asset:metadata:modify": True,
                "asset:overwrite": True,
                "folder:create": True,
                "folder:delete": True,
                "folder:metadata:modify": True
            },
            "3": {
                "category:access": True,
                "asset:create": True,
                "asset:delete": True,
                "asset:metadata:modify": True,
                "asset:overwrite": True,
                "folder:create": True,
                "folder:delete": True,
                "folder:metadata:modify": True
            }

        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def categories_id(self, request, obj_id):
        store = {
            "id": obj_id,
            "name": "Images",
            "position": 1,
            "assetsCount": 21,
            "totalAssetsCount": 24,
            "extensions": [
                "jpeg",
                "jpg",
                "png",
                "gif",
                "bmp",
                "webp",
                "tiff"
            ],
            "isPrivate": False
        }

        return HttpResponse(json.dumps(store), content_type='application/json')

    def categories(self, request):
        store = {
            "totalCount": 3,
            "offset": 0,
            "limit": 500,
            "items": [
                {
                    "id": "1",
                    "name": "Images",
                    "position": 1,
                    "assetsCount": 21,
                    "totalAssetsCount": 24,
                    "extensions": [
                        "jpeg",
                        "jpg",
                        "png",
                        "gif",
                        "bmp",
                        "webp",
                        "tiff"
                    ],
                    "isPrivate": False
                },
                {
                    "id": "2",
                    "name": "Files",
                    "position": 2,
                    "assetsCount": 1,
                    "totalAssetsCount": 1,
                    "extensions": [
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
                        "txt"
                    ],
                    "isPrivate": False
                },
                {
                    "id": "3",
                    "name": "Documents",
                    "position": 3,
                    "assetsCount": 4,
                    "totalAssetsCount": 4,
                    "extensions": [
                        "doc",
                        "docx",
                        "ppt",
                        "pptx",
                        "xls",
                        "xlsx",
                        "odt",
                        "pdf",
                        "txt"
                    ],
                    "isPrivate": False
                }
            ]
        }

        return HttpResponse(json.dumps(store), content_type='application/json')

    def adminconfig(self, request):
        store = {
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

        return HttpResponse(json.dumps(store), content_type='application/json')

    def admincategories(self, request):
        store = {
            "totalCount": 3,
            "offset": 0,
            "limit": 500,
            "items": [
                {
                    "id": "1",
                    "name": "Images",
                    "position": 1,
                    "assetsCount": 14,
                    "totalAssetsCount": 17,
                    "extensions": [
                        "jpeg",
                        "jpg",
                        "png",
                        "gif",
                        "bmp",
                        "webp",
                        "tiff"
                    ],
                    "isPrivate": False
                },
                {
                    "id": "2",
                    "name": "Files",
                    "position": 2,
                    "assetsCount": 3,
                    "totalAssetsCount": 3,
                    "extensions": [
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
                        "txt"
                    ],
                    "isPrivate": False
                },
                {
                    "id": "3",
                    "name": "Documents",
                    "position": 3,
                    "assetsCount": 3,
                    "totalAssetsCount": 3,
                    "extensions": [
                        "doc",
                        "docx",
                        "ppt",
                        "pptx",
                        "xls",
                        "xlsx",
                        "odt",
                        "pdf",
                        "txt"
                    ],
                    "isPrivate": False
                }
            ]
        }

        return HttpResponse(json.dumps(store), content_type='application/json')

    def adminimages(self, request):
        store = {"default": {"defaultQuality": 80}}

        return HttpResponse(json.dumps(store), content_type='application/json')

    def admingroups(self, request):
        store = {"items": [{"id": "f437cd41039d", "name": "Default", "isDefault": True}]}

        return HttpResponse(json.dumps(store), content_type='application/json')

    def adminpermissions(self, request):
        store = {
            "items": [
                {
                    "id": "f437cd41039d",
                    "groupId": "f437cd41039d",
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
                }
            ]
        }

        return HttpResponse(json.dumps(store), content_type='application/json')

    def permissions(self, request):
        store = {
            "1": {
                "category:access": True,
                "asset:create": True,
                "asset:delete": True,
                "asset:metadata:modify": True,
                "asset:overwrite": True,
                "folder:create": True,
                "folder:delete": True,
                "folder:metadata:modify": True
            },
            "2": {
                "category:access": True,
                "asset:create": True,
                "asset:delete": True,
                "asset:metadata:modify": True,
                "asset:overwrite": True,
                "folder:create": True,
                "folder:delete": True,
                "folder:metadata:modify": True
            },
            "3": {
                "category:access": True,
                "asset:create": True,
                "asset:delete": True,
                "asset:metadata:modify": True,
                "asset:overwrite": True,
                "folder:create": True,
                "folder:delete": True,
                "folder:metadata:modify": True
            }
        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def workspaces(self, request):
        store = {"items": [{"id": "b31838d7db045edd5b6c", "name": "ckbox-demo-workspace-DGMh-pql"}]}
        return HttpResponse(json.dumps(store), content_type='application/json')

    def limits(self, request):
        store = {
            "maxImageInMegapixelsLimit": 50,
            "maxFileSizeInBytesLimit": 50000000,
            "pricingPlanName": "ckbox.pro",
            "isMaxBandwidthExceeded": False,
            "isMaxStorageSizeExceeded": False
        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def folders(self, request):
        store = {
            "items": [
                {
                    "id": "SIOzYPwafC-a",
                    "name": "Plants",
                    "createdAt": "2025-09-21T09:23:10.417Z",
                    "updatedAt": "2025-09-21T09:23:10.417Z",
                    "categoryId": "1",
                    "folders": [
                        {
                            "id": "1Kfk3RyAQ3yT",
                            "name": "Linux",
                            "createdAt": "2025-09-22T10:45:27.390Z",
                            "updatedAt": "2025-09-22T10:45:27.390Z",
                            "categoryId": "1",
                            "parentId": "SIOzYPwafC-a",
                            "folders": [],
                            "assetsCount": 0
                        }
                    ],
                    "assetsCount": 3
                }
            ]
        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def foldersid(self, request, obj_id):
        store = {
            "id": "1Kfk3RyAQ3yT",
            "name": "Linux",
            "createdAt": "2025-09-22T10:45:27.390Z",
            "updatedAt": "2025-09-22T10:45:27.390Z",
            "categoryId": "1",
            "parentId": "SIOzYPwafC-a",
            "folders": [],
            "assetsCount": 0
        }

        return HttpResponse(json.dumps(store), content_type='application/json')

    def recent(self, request):
        store = {
            "totalCount": 19,
            "offset": 0,
            "limit": 1,
            "items": [
                {
                    "id": "-Iwoyr_oB-du",
                    "name": "222",
                    "extension": "png",
                    "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/file",
                    "imageUrls": {
                        "103": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/103.webp",
                        "206": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/206.webp",
                        "309": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/309.webp",
                        "412": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/412.webp",
                        "515": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/515.webp",
                        "618": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/618.webp",
                        "721": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/721.webp",
                        "824": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/824.webp",
                        "927": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/927.webp",
                        "1024": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/1024.webp",
                        "default": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/1024.png"
                    },
                    "mimeType": "image/png",
                    "categoryId": "1",
                    "folderId": 'null',
                    "size": 1030621,
                    "uploadedAt": "2025-09-21T19:24:26.600Z",
                    "lastModifiedAt": "2025-09-21T19:24:26.853Z",
                    "lastUsedAt": "2025-09-22T05:57:30.271Z",
                    "tags": [],
                    "metadata": {
                        "width": 1024,
                        "height": 747,
                        "blurHash": "KHBDH7~q?b-=-;%Mt7%Mxv",
                        "metadataProcessingStatus": "success",
                        "analysisProcessingStatus": "queued"
                    }
                }
            ]
        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def trash(self, request):
        store = {
            "totalCount": 1,
            "offset": 0,
            "limit": 1,
            "items": [
                {
                    "id": "2OumfngcBocr",
                    "name": "Linux-Tutorial",
                    "extension": "pdf",
                    "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/2OumfngcBocr/file",
                    "mimeType": "application/pdf",
                    "categoryId": "2",
                    "folderId": None,
                    "size": 842174,
                    "uploadedAt": "2025-09-21T19:26:21.891Z",
                    "lastModifiedAt": "2025-09-21T19:26:21.891Z",
                    "lastUsedAt": "2025-09-21T19:26:21.891Z",
                    "tags": [],
                    "metadata": {}
                }
            ]
        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def allassets(self, request):
        store = {
            "totalCount": 21,
            "offset": 0,
            "limit": 5,
            "items": [
                {
                    "id": 1,
                    "name": "cozy-industrial-loft-living",
                    "extension": "jpg",
                    "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/file",
                    "imageUrls": {
                        "284": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/284.webp",
                        "568": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/568.webp",
                        "852": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/852.webp",
                        "1136": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/1136.webp",
                        "1420": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/1420.webp",
                        "1704": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/1704.webp",
                        "1988": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/1988.webp",
                        "2272": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/2272.webp",
                        "2556": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/2556.webp",
                        "2832": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/2832.webp",
                        "default": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/4BF5Q1U8Qs0O/images/2832.jpeg"
                    },
                    "mimeType": "image/jpeg",
                    "categoryId": "1",
                    "folderId": 'null',
                    "size": 760899,
                    "uploadedAt": "2025-09-22T02:52:12.025Z",
                    "lastModifiedAt": "2025-09-22T02:52:12.374Z",
                    "lastUsedAt": "2025-09-22T02:52:12.374Z",
                    "tags": [],
                    "metadata": {
                        "description": "A warmly lit apartment living room blends industrial elements like exposed ductwork with cozy vintage furniture and plants.",
                        "width": 2832,
                        "height": 1593,
                        "blurHash": "KRD+*oMx9b~pM{Rk%1t7WE",
                        "metadataProcessingStatus": "success",
                        "analysisProcessingStatus": "queued"
                    }
                },
                {
                    "id": 2,
                    "name": "admin",
                    "extension": "jpg",
                    "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/file",
                    "imageUrls": {
                        "80": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/80.webp",
                        "160": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/160.webp",
                        "240": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/240.webp",
                        "320": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/320.webp",
                        "400": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/400.webp",
                        "480": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/480.webp",
                        "512": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/512.webp",
                        "default": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/YQAULjBrSvpb/images/512.jpeg"
                    },
                    "mimeType": "image/jpeg",
                    "categoryId": "1",
                    "folderId": 'null',
                    "size": 59625,
                    "uploadedAt": "2025-09-21T19:29:15.680Z",
                    "lastModifiedAt": "2025-09-21T19:29:15.931Z",
                    "lastUsedAt": "2025-09-21T19:29:15.931Z",
                    "tags": [],
                    "metadata": {
                        "width": 512,
                        "height": 288,
                        "blurHash": "K4BWSlS6I8^%~V00W7jYR5",
                        "metadataProcessingStatus": "success",
                        "analysisProcessingStatus": "queued"
                    }
                },
                {
                    "id": 3,
                    "name": "a",
                    "extension": "jpg",
                    "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/file",
                    "imageUrls": {
                        "80": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/80.webp",
                        "160": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/160.webp",
                        "240": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/240.webp",
                        "320": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/320.webp",
                        "400": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/400.webp",
                        "480": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/480.webp",
                        "560": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/560.webp",
                        "640": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/640.webp",
                        "default": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/aRLNkslNPkQs/images/640.jpeg"
                    },
                    "mimeType": "image/jpeg",
                    "categoryId": "1",
                    "folderId": 'null',
                    "size": 198669,
                    "uploadedAt": "2025-09-21T19:28:24.520Z",
                    "lastModifiedAt": "2025-09-21T19:28:24.825Z",
                    "lastUsedAt": "2025-09-21T19:28:24.825Z",
                    "tags": [],
                    "metadata": {
                        "width": 640,
                        "height": 480,
                        "blurHash": "K5B:a0E1R5%K}]Mw-PIoRQ",
                        "metadataProcessingStatus": "success",
                        "analysisProcessingStatus": "queued"
                    }
                },
                {
                    "id": 4,
                    "name": "222",
                    "extension": "png",
                    "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/file",
                    "imageUrls": {
                        "103": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/103.webp",
                        "206": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/206.webp",
                        "309": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/309.webp",
                        "412": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/412.webp",
                        "515": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/515.webp",
                        "618": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/618.webp",
                        "721": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/721.webp",
                        "824": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/824.webp",
                        "927": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/927.webp",
                        "1024": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/1024.webp",
                        "default": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/-Iwoyr_oB-du/images/1024.png"
                    },
                    "mimeType": "image/png",
                    "categoryId": "1",
                    "folderId": 'null',
                    "size": 1030621,
                    "uploadedAt": "2025-09-21T19:24:26.600Z",
                    "lastModifiedAt": "2025-09-21T19:24:26.853Z",
                    "lastUsedAt": "2025-09-21T19:24:26.853Z",
                    "tags": [],
                    "metadata": {
                        "width": 1024,
                        "height": 747,
                        "blurHash": "KHBDH7~q?b-=-;%Mt7%Mxv",
                        "metadataProcessingStatus": "success",
                        "analysisProcessingStatus": "queued"
                    }
                },
                {
                    "id": 5,
                    "name": "cholla-cactus-blue-sky-2025-09-22 03.22",
                    "extension": "jpg",
                    "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/file",
                    "imageUrls": {
                        "103": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/103.webp",
                        "206": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/206.webp",
                        "309": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/309.webp",
                        "412": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/412.webp",
                        "515": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/515.webp",
                        "618": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/618.webp",
                        "721": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/721.webp",
                        "824": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/824.webp",
                        "927": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/927.webp",
                        "1024": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/1024.webp",
                        "default": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/Wy6CNbxURwQ9/images/1024.jpeg"
                    },
                    "mimeType": "image/jpeg",
                    "categoryId": "1",
                    "folderId": 'null',
                    "size": 71082,
                    "uploadedAt": "2025-09-21T19:23:04.950Z",
                    "lastModifiedAt": "2025-09-21T19:23:05.250Z",
                    "lastUsedAt": "2025-09-21T19:23:05.250Z",
                    "tags": [],
                    "metadata": {
                        "description": "he spiny, green arms of a cholla cactus reach up towards a clear, vibrant blue sky.",
                        "width": 1024,
                        "height": 576,
                        "blurHash": "KQED|+lBs+BtM|SjM}wZaK",
                        "metadataProcessingStatus": "success",
                        "analysisProcessingStatus": "queued"
                    }
                }
            ]
        }
        return HttpResponse(json.dumps(store), content_type='application/json')

    def getassets(self, request, obj_id):
        store = {
            "id": obj_id,
            "name": "lush-greenery-white-stucco-wall",
            "extension": "jpg",
            "url": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/file",
            "imageUrls": {
                "128": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/128.webp",
                "256": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/256.webp",
                "384": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/384.webp",
                "512": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/512.webp",
                "640": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/640.webp",
                "768": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/768.webp",
                "896": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/896.webp",
                "1024": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/1024.webp",
                "1152": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/1152.webp",
                "1280": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/1280.webp",
                "default": "https://ckbox.cloud/b31838d7db045edd5b6c/assets/ytAh65GXpWmn/images/1280.jpeg"
            },
            "mimeType": "image/jpeg",
            "categoryId": "1",
            "folderId": None,
            "size": 205106,
            "uploadedAt": "2025-09-21T09:23:10.422Z",
            "lastModifiedAt": "2025-09-21T09:23:10.422Z",
            "lastUsedAt": "2025-09-21T09:23:10.422Z",
            "tags": [
                "foliage",
                "garden",
                "greenery",
                "plants",
                "sunlight",
                "white wall"
            ],
            "metadata": {
                "description": "A variety of lush green plants and foliage flourishes against a bright, sunlit white stucco wall.",
                "width": 1280,
                "height": 1920,
                "blurHash": "KlNA#3a{M^~Xs+RiD%M{t7",
                "metadataProcessingStatus": "success"
            }
        }
        return HttpResponse(json.dumps(store), content_type='application/json')
