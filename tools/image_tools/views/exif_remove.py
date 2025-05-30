# tools/image_tools/views/exif_remove.py

import uuid
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from tools.image_tools.services.exif_cleaner import remove_exif
from tools.image_tools.services.uploader import upload_image

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'images',
            openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='EXIF 정보를 제거할 이미지 파일들',
            required=True,
            multiple=True
        ),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def remove_exif_metadata(request):
    images = request.FILES.getlist('images')
    if not images:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    cleaned_urls = []

    for img in images:
        try:
            cleaned_io = remove_exif(img)
            filename = f"{uuid.uuid4()}_noexif.{img.name.split('.')[-1].lower()}"

            public_url = upload_image(
                folder="no_exif",
                filename=filename,
                content=cleaned_io.getbuffer(),
                content_type=img.content_type
            )
            cleaned_urls.append(public_url)
        except Exception as e:
            print("EXIF remove error:", e)
            continue

    return JsonResponse({'cleaned_urls': cleaned_urls})
