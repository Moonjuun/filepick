# tools/pdf_tools/views/merge.py

import io
import uuid
from datetime import datetime
from PyPDF2 import PdfMerger
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
            description='병합할 PDF 파일들 (최소 2개)',
            required=True,
            multiple=True
        )
    ],
    responses={200: '병합된 PDF 파일의 URL 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def merge_pdfs(request):
    """
    업로드된 여러 PDF 파일을 병합하여 Supabase에 저장하고 URL을 반환합니다.
    """
    files = request.FILES.getlist('files')

    if not files or len(files) < 2:
        return JsonResponse({'error': 'PDF 파일은 최소 2개 이상 필요합니다.'}, status=400)

    try:
        # PDF 병합
        merger = PdfMerger()
        for f in files:
            merger.append(f)

        output_buffer = io.BytesIO()
        merger.write(output_buffer)
        merger.close()
        output_buffer.seek(0)

        # 파일명 생성
        short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
        filename = f"{short_id}.pdf"

        # Supabase 업로드
        public_url = upload_pdf(
            folder="merged",
            filename=filename,
            content=output_buffer.getbuffer()
        )

        return JsonResponse({'merged_url': public_url})

    except Exception as e:
        print("Merge error:", e)
        return JsonResponse({'error': 'PDF 병합 중 오류 발생'}, status=500)
