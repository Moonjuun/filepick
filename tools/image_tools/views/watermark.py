# tools/image_tools/views/watermark.py

import io
import uuid
from PIL import Image, ImageDraw, ImageFont
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from tools.image_tools.services.uploader import upload_image


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, description='원본 이미지들', required=True, multiple=True),
        openapi.Parameter('type', openapi.IN_FORM, type=openapi.TYPE_STRING, description='text 또는 image', required=True),
        openapi.Parameter('text', openapi.IN_FORM, type=openapi.TYPE_STRING, description='텍스트 워터마크 내용'),
        openapi.Parameter('position', openapi.IN_FORM, type=openapi.TYPE_STRING, description='위치 (center, bottom-right, top-left)', default='bottom-right'),
        openapi.Parameter('opacity', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='불투명도 (0~255)', default=128),
        openapi.Parameter('watermark_image', openapi.IN_FORM, type=openapi.TYPE_FILE, description='워터마크 이미지 (image 타입일 경우)', required=False),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def add_watermark(request):
    """
    이미지에 텍스트 또는 이미지 워터마크를 삽입한 후 Supabase에 업로드합니다.
    """
    images = request.FILES.getlist('images')
    wm_type = request.POST.get('type', 'text')
    text = request.POST.get('text', 'FilePick')
    opacity = int(request.POST.get('opacity', 128))
    position = request.POST.get('position', 'bottom-right')

    if not images:
        return JsonResponse({'error': '이미지가 없습니다.'}, status=400)

    # 워터마크 이미지 로딩
    wm_img = None
    if wm_type == 'image' and request.FILES.get('watermark_image'):
        try:
            wm_img = Image.open(request.FILES['watermark_image']).convert("RGBA")
        except Exception as e:
            print("Failed to open watermark image:", e)
            wm_img = None

    result_urls = []

    for img_file in images:
        try:
            base_img = Image.open(img_file).convert("RGBA")
            watermark_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))

            if wm_type == 'text':
                draw = ImageDraw.Draw(watermark_layer)
                font_size = int(min(base_img.size) * 0.05)
                try:
                    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x, y = get_position(position, base_img.size, (text_width, text_height))

                draw.text((x, y), text, fill=(0, 0, 0, opacity), font=font)

            elif wm_type == 'image' and wm_img:
                wm_resized = wm_img.resize((int(base_img.size[0] * 0.25), int(base_img.size[1] * 0.25)))
                if opacity < 255:
                    alpha = wm_resized.getchannel('A')
                    new_alpha = alpha.point(lambda p: int(p * (opacity / 255)))
                    wm_resized.putalpha(new_alpha)

                x, y = get_position(position, base_img.size, wm_resized.size)
                watermark_layer.paste(wm_resized, (x, y), wm_resized)

            final_img = Image.alpha_composite(base_img, watermark_layer).convert("RGB")
            img_io = io.BytesIO()
            final_img.save(img_io, "JPEG")
            img_io.seek(0)

            filename = f"{uuid.uuid4()}_watermarked.jpg"
            public_url = upload_image(
                folder="watermarked",
                filename=filename,
                content=img_io.getbuffer(),
                content_type="image/jpeg"
            )
            result_urls.append(public_url)

        except Exception as e:
            print("Watermark error:", e)
            continue

    return JsonResponse({'watermarked_urls': result_urls})


def get_position(position, base_size, wm_size):
    """
    워터마크 위치를 계산합니다.
    """
    bx, by = base_size
    wx, wy = wm_size

    if position == 'top-left':
        return (10, 10)
    elif position == 'top-right':
        return (bx - wx - 10, 10)
    elif position == 'bottom-left':
        return (10, by - wy - 10)
    elif position == 'center':
        return ((bx - wx) // 2, (by - wy) // 2)
    elif position == 'bottom-right':
        return (bx - wx - 10, by - wy - 10)
    else:
        return (10, 10)
