# tools/image_tools/views/resize.py

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
            name='images',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='여러 이미지 파일',
            required=True,
            multiple=True
        ),
        openapi.Parameter('width', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='가로 크기', required=True),
        openapi.Parameter('height', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='세로 크기', required=True),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def resize_image(request):
    """
    여러 이미지를 입력받아 지정된 크기로 리사이즈한 후,
    Supabase Storage에 업로드하고 public URL 목록을 반환합니다.
    """
    images = request.FILES.getlist('images')
    if not images:
        return JsonResponse({'error': 'images는 필수입니다.'}, status=400)

    try:
        width = int(request.POST.get('width'))
        height = int(request.POST.get('height'))
    except Exception:
        return JsonResponse({'error': 'width와 height는 정수여야 합니다.'}, status=400)

    resized_urls = []

    for img_file in images:
        try:
            img = Image.open(img_file)
            resized_img = img.resize((width, height))

            # BytesIO에 저장
            img_io = io.BytesIO()
            resized_img.save(img_io, format='PNG')
            img_io.seek(0)

            # 고유 파일명 생성
            filename = f"{uuid.uuid4()}.png"

            # 업로드 및 public URL 반환
            public_url = upload_image(
                folder="resized",
                filename=filename,
                content=img_io.getbuffer(),
                content_type="image/png"
            )
            resized_urls.append(public_url)

        except Exception as e:
            print("Resize error:", e)
            continue

    return JsonResponse({'resized_urls': resized_urls})
