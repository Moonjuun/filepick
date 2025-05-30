# tools/image_tools/urls.py

from django.urls import path
from .views.resize import resize_image
from .views.convert import convert_image_format
from .views.compress import compress_image
from .views.filter import apply_filter
from .views.watermark import add_watermark
from .views.exif_remove import remove_exif_metadata

urlpatterns = [
    path('resize/', resize_image),                  # 이미지 리사이즈
    path('convert/', convert_image_format),         # 포맷 변환
    path('compress/', compress_image),              # 이미지 압축
    path('filter/', apply_filter),                  # 필터 적용
    path('watermark/', add_watermark),              # 워터마크 삽입
    path('remove-exif/', remove_exif_metadata),     # EXIF 메타데이터 제거
]
