# tools/pdf_tools/views/compress.py

import io
import uuid
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
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
            description='압축할 PDF 파일들',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='quality',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='압축 품질 (low, medium, high)',
            required=False,
            default='medium'
        )
    ],
    responses={200: '압축된 PDF URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def compress_pdfs(request):
    """
    PDF 파일들의 메타데이터를 제거하여 경량화한 후 Supabase에 업로드합니다.
    """
    files = request.FILES.getlist('files')
    quality = request.POST.get('quality', 'medium')

    if not files:
        return JsonResponse({'error': '압축할 파일이 없습니다.'}, status=400)

    compressed_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # 압축 효과는 미미하지만, 메타데이터 제거
            writer.add_metadata({})

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)

            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"{short_id}.pdf"

            public_url = upload_pdf(
                folder="compressed",
                filename=filename,
                content=output.getbuffer()
            )
            compressed_urls.append(public_url)

        except Exception as e:
            print("Compress error:", e)
            continue

    return JsonResponse({'compressed_urls': compressed_urls})
