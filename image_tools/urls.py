from django.urls import path
from .views import resize_image

urlpatterns = [
    path('resize/', resize_image),
]
