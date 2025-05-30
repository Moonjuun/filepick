from django.urls import path
from .views.docx_to_pdf import convert_docx_to_pdf
from .views.ppt_to_pdf import convert_ppt_to_pdf
from .views.excel_to_pdf import convert_excel_to_pdf

urlpatterns = [
    path('docx-to-pdf/', convert_docx_to_pdf, name='convert-docx-to-pdf'),
    path('ppt-to-pdf/', convert_ppt_to_pdf, name='convert-ppt-to-pdf'), 
    path('excel-to-pdf/', convert_excel_to_pdf, name='convert-excel-to-pdf'),  
]
