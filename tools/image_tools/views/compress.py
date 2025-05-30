# tools/image_tools/views/compress.py

import os
import io
import uuid
from PIL import Image
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from tools.image_tools.services.uploader import upload_image


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'images',
            openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='압축할 이미지 파일들',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            'quality',
            openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='압축 품질 (high, medium, low)',
            required=False,
            default='medium'
        ),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def compress_image(request):
    """
    여러 이미지를 JPEG로 압축하여 Supabase에 업로드하고 public URL 목록을 반환합니다.
    """
    images = request.FILES.getlist('images')
    quality_level = request.POST.get('quality', 'medium').lower()

    if not images:
        return JsonResponse({'error': '압축할 이미지가 없습니다.'}, status=400)

    # 지원 포맷
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']

    # 품질 매핑
    quality_map = {
        'high': 85,
        'medium': 65,
        'low': 40
    }
    quality = quality_map.get(quality_level, 65)

    compressed_urls = []

    for img_file in images:
        ext = os.path.splitext(img_file.name)[1].lower()
        if ext not in allowed_extensions:
            continue

        try:
            img = Image.open(img_file).convert("RGB")
            img_io = io.BytesIO()
            img.save(img_io, "JPEG", quality=quality)
            img_io.seek(0)

            filename = f"{uuid.uuid4()}.jpg"
            public_url = upload_image(
                folder="compressed",
                filename=filename,
                content=img_io.getbuffer(),
                content_type="image/jpeg"
            )
            compressed_urls.append(public_url)

        except Exception as e:
            print("Compress error:", e)
            continue

    return JsonResponse({'compressed_urls': compressed_urls})
