from django.urls import path
from .views import resize_image, convert_image_format, compress_image, apply_filter

urlpatterns = [
    path('resize/', resize_image),
    path('convert/', convert_image_format), 
    path('compress/', compress_image),
    path('filter/', apply_filter)
]
