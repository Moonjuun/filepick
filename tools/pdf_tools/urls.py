from django.urls import path
from . import views

urlpatterns = [
    path('merge/', views.merge_pdfs),
    path('split/', views.split_pdfs),
    path('compress/', views.compress_pdfs),
    path('rotate-delete/', views.rotate_or_delete_pdfs),
    path('encrypt-decrypt/', views.encrypt_or_decrypt_pdfs),
]
