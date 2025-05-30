# tools/image_tools/views/convert.py

import io
import uuid
from PIL import Image
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from tools.image_tools.services.uploader import upload_image

# 지원 포맷 매핑
SUPPORTED_FORMATS = {
    'JPG': 'JPEG',
    'PNG': 'PNG',
    'WEBP': 'WEBP',
    'BMP': 'BMP',
    'TIFF': 'TIFF',
    'ICO': 'ICO'
}


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'images',
            openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='이미지 또는 PDF 파일들',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            'format',
            openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='변환할 포맷 (예: PNG, JPG)',
            required=True
        ),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def convert_image_format(request):
    """
    업로드된 이미지 또는 PDF 파일들을 지정된 포맷으로 변환하여 Supabase에 업로드하고 URL을 반환합니다.
    """
    images = request.FILES.getlist('images')
    target_format = request.POST.get('format', '').upper()

    if not images or target_format not in SUPPORTED_FORMATS:
        return JsonResponse({'error': '지원하지 않는 포맷이거나 파일이 없습니다.'}, status=400)

    ext = SUPPORTED_FORMATS[target_format]
    converted_urls = []

    for uploaded_file in images:
        try:
            # PDF 파일 처리
            if uploaded_file.name.lower().endswith('.pdf'):
                from pdf2image import convert_from_bytes
                pdf_bytes = uploaded_file.read()
                pages = convert_from_bytes(pdf_bytes)

                for i, page in enumerate(pages):
                    img_io = io.BytesIO()
                    page.convert("RGB").save(img_io, ext)
                    img_io.seek(0)

                    filename = f"{uuid.uuid4()}_page{i+1}.{target_format.lower()}"
                    public_url = upload_image(
                        folder="converted",
                        filename=filename,
                        content=img_io.getbuffer(),
                        content_type=f"image/{target_format.lower()}"
                    )
                    converted_urls.append(public_url)

            # 일반 이미지 처리
            else:
                img = Image.open(uploaded_file).convert("RGB")
                img_io = io.BytesIO()
                img.save(img_io, ext)
                img_io.seek(0)

                filename = f"{uuid.uuid4()}.{target_format.lower()}"
                public_url = upload_image(
                    folder="converted",
                    filename=filename,
                    content=img_io.getbuffer(),
                    content_type=f"image/{target_format.lower()}"
                )
                converted_urls.append(public_url)

        except Exception as e:
            print("Convert error:", e)
            continue

    return JsonResponse({'converted_urls': converted_urls})
