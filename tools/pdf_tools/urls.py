# tools/pdf_tools/urls.py

from django.urls import path
from .views.merge import merge_pdfs
from .views.split import split_pdfs
from .views.compress import compress_pdfs
from .views.rotate_delete import rotate_or_delete_pdfs
from .views.encrypt_decrypt import encrypt_or_decrypt_pdfs
from .views import merge, split, compress, rotate_delete, encrypt_decrypt, extract_text

urlpatterns = [
    path('merge/', merge_pdfs),                              # PDF 병합
    path('split/', split_pdfs),                              # PDF 분할
    path('compress/', compress_pdfs),                        # PDF 압축
    path('rotate-delete/', rotate_or_delete_pdfs),           # 페이지 회전/삭제
    path('encrypt-decrypt/', encrypt_or_decrypt_pdfs),       # 암호 설정/해제
    path('extract-text/', extract_text.extract_text),        # PDF에서 텍스트 추출

]
