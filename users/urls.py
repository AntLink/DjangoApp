# accounts/urls.py
from django.urls import path
from .views import UploadProfileImageView

urlpatterns = [
    path('upload-profile-image/', UploadProfileImageView.as_view(), name='upload_profile_image'),
]