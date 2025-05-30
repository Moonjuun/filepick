# tools/pdf_tools/views/split.py

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
            description='분할할 PDF 파일들',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='pages',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='분할할 페이지 번호 (예: "0,2")',
            required=True
        )
    ],
    responses={200: '분할된 PDF URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def split_pdfs(request):
    """
    업로드된 PDF 파일들에서 지정된 페이지만 추출하여 Supabase에 업로드합니다.
    """
    files = request.FILES.getlist('files')
    pages_str = request.POST.get('pages', '')

    if not files or not pages_str:
        return JsonResponse({'error': '파일과 pages는 필수입니다.'}, status=400)

    try:
        pages = [int(p.strip()) for p in pages_str.split(',') if p.strip().isdigit()]
    except Exception:
        return JsonResponse({'error': 'pages 형식이 잘못되었습니다. 예: "0,2"'}, status=400)

    split_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            for i in pages:
                if 0 <= i < len(reader.pages):
                    writer.add_page(reader.pages[i])

            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            output_buffer.seek(0)

            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"{short_id}.pdf"

            public_url = upload_pdf(
                folder="split",
                filename=filename,
                content=output_buffer.getbuffer()
            )
            split_urls.append(public_url)

        except Exception as e:
            print("Split error:", e)
            continue

    return JsonResponse({'split_urls': split_urls})
