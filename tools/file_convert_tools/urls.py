from django.urls import path
from .views.docx_to_pdf import convert_docx_to_pdf
from .views.ppt_to_pdf import convert_ppt_to_pdf
from .views.excel_to_pdf import convert_excel_to_pdf
from .views.mp4_to_mp3 import convert_mp4_to_mp3

urlpatterns = [
    path('docx-to-pdf/', convert_docx_to_pdf, name='convert-docx-to-pdf'),
    path('ppt-to-pdf/', convert_ppt_to_pdf, name='convert-ppt-to-pdf'), 
    path('excel-to-pdf/', convert_excel_to_pdf, name='convert-excel-to-pdf'), 
    path('mp4-to-mp3/', convert_mp4_to_mp3, name='convert-mp4-to-mp3'),
]
