# tools/image_tools/views/filter.py

import io
import uuid
from PIL import Image, ImageFilter, ImageEnhance
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
            description='필터를 적용할 이미지들',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            'filter',
            openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='적용할 필터 이름 (예: grayscale, sepia, sharpen)',
            required=True
        ),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def apply_filter(request):
    """
    여러 이미지에 지정된 필터를 적용하여 Supabase에 업로드하고 public URL 목록을 반환합니다.
    """
    images = request.FILES.getlist('images')
    filter_name = request.POST.get('filter', 'grayscale').lower()

    if not images:
        return JsonResponse({'error': '이미지가 없습니다.'}, status=400)

    filtered_urls = []

    for img_file in images:
        try:
            img = Image.open(img_file).convert("RGB")

            if filter_name == 'grayscale':
                img = img.convert('L').convert('RGB')

            elif filter_name == 'sepia':
                width, height = img.size
                pixels = img.load()
                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                        pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))

            elif filter_name == 'sharpen':
                img = img.filter(ImageFilter.SHARPEN)

            elif filter_name == 'blur':
                img = img.filter(ImageFilter.BLUR)

            elif filter_name == 'contrast':
                img = ImageEnhance.Contrast(img).enhance(1.5)

            elif filter_name == 'brightness':
                img = ImageEnhance.Brightness(img).enhance(1.3)

            elif filter_name == 'edge':
                img = img.filter(ImageFilter.FIND_EDGES)

            else:
                continue  # 잘못된 필터 이름 무시

            img_io = io.BytesIO()
            img.save(img_io, "JPEG")
            img_io.seek(0)

            filename = f"{uuid.uuid4()}_{filter_name}.jpg"
            public_url = upload_image(
                folder="filtered",
                filename=filename,
                content=img_io.getbuffer(),
                content_type="image/jpeg"
            )
            filtered_urls.append(public_url)

        except Exception as e:
            print("Filter error:", e)
            continue

    return JsonResponse({'filtered_urls': filtered_urls})
