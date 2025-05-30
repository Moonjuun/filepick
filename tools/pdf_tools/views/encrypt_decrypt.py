# tools/pdf_tools/views/encrypt_decrypt.py

import io
import uuid
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from tools.pdf_tools.services.uploader import upload_pdf


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='files',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='암호화/복호화할 PDF 파일들',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='mode',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='"encrypt" 또는 "decrypt"',
            required=True
        ),
        openapi.Parameter(
            name='password',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='설정하거나 해제할 비밀번호',
            required=True
        )
    ],
    responses={200: '처리된 PDF URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def encrypt_or_decrypt_pdfs(request):
    """
    PDF 파일에 암호를 설정하거나 해제하여 Supabase에 업로드합니다.
    """
    files = request.FILES.getlist('files')
    mode = request.POST.get('mode')
    password = request.POST.get('password')

    if not files or not mode or not password:
        return JsonResponse({'error': '파일, mode, password는 필수입니다.'}, status=400)

    if mode not in ['encrypt', 'decrypt']:
        return JsonResponse({'error': 'mode는 "encrypt" 또는 "decrypt"만 가능합니다.'}, status=400)

    result_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            if mode == 'decrypt':
                if reader.is_encrypted:
                    try:
                        reader.decrypt(password)
                    except Exception:
                        return JsonResponse({'error': f'PDF 해독 실패: {f.name}'}, status=400)
                for page in reader.pages:
                    writer.add_page(page)

            else:  # encrypt
                for page in reader.pages:
                    writer.add_page(page)
                writer.encrypt(password)

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)

            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"{short_id}.pdf"

            public_url = upload_pdf(
                folder=mode,  # encrypt 또는 decrypt 폴더
                filename=filename,
                content=output.getbuffer()
            )
            result_urls.append(public_url)

        except PdfReadError:
            return JsonResponse({'error': f'PDF 읽기 오류: {f.name}'}, status=400)
        except Exception as e:
            print("Encrypt/Decrypt error:", e)
            continue

    return JsonResponse({'result_urls': result_urls})
