from django.urls import path
from .views.docx_to_pdf import convert_docx_to_pdf

urlpatterns = [
    path('docx-to-pdf/', convert_docx_to_pdf, name='convert-docx-to-pdf'),
]
