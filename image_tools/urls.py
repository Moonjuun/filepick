from django.urls import path
from .views import resize_image, convert_image_format

urlpatterns = [
    path('resize/', resize_image),
    path('convert/', convert_image_format),  # 새 API 추가
]
