# tools/pdf_tools/views/rotate_delete.py

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
            description='회전 또는 삭제할 PDF 파일들',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='rotate',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_INTEGER,
            description='회전 각도 (0, 90, 180, 270)',
            required=False
        ),
        openapi.Parameter(
            name='delete_pages',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='삭제할 페이지 번호들 (예: "0,2")',
            required=False
        )
    ],
    responses={200: '처리된 PDF URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def rotate_or_delete_pdfs(request):
    """
    각 PDF 파일에 대해 페이지 회전 또는 삭제를 적용하고 Supabase에 업로드합니다.
    """
    files = request.FILES.getlist('files')
    rotate = request.POST.get('rotate')
    delete_pages_str = request.POST.get('delete_pages', '')

    if not files:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    # 삭제할 페이지 인덱스 파싱
    delete_pages = set()
    if delete_pages_str:
        try:
            delete_pages = set(int(i.strip()) for i in delete_pages_str.split(',') if i.strip().isdigit())
        except Exception:
            return JsonResponse({'error': 'delete_pages 형식이 잘못되었습니다.'}, status=400)

    # 회전 각도 검증
    if rotate:
        try:
            rotate = int(rotate)
            assert rotate in [0, 90, 180, 270]
        except Exception:
            return JsonResponse({'error': 'rotate 값은 0, 90, 180, 270 중 하나여야 합니다.'}, status=400)

    processed_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            for idx, page in enumerate(reader.pages):
                if idx in delete_pages:
                    continue
                if rotate:
                    page.rotate(rotate)
                writer.add_page(page)

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)

            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"{short_id}.pdf"

            public_url = upload_pdf(
                folder="processed",
                filename=filename,
                content=output.getbuffer()
            )
            processed_urls.append(public_url)

        except Exception as e:
            print("Rotate/Delete error:", e)
            continue

    return JsonResponse({'processed_urls': processed_urls})
