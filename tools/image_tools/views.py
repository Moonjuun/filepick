import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# 1. Resize
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
        openapi.Parameter('width', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='가로', required=True),
        openapi.Parameter('height', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='세로', required=True),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def resize_image(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        width = int(request.POST.get('width', 300))
        height = int(request.POST.get('height', 300))
        images = request.FILES.getlist('images')

        resized_urls = []

        for img_file in images:
            path = default_storage.save('original/' + img_file.name, img_file)
            img = Image.open(os.path.join(settings.MEDIA_ROOT, path))
            resized_img = img.resize((width, height))

            resized_path = 'resized/resized_' + img_file.name
            full_resized_path = os.path.join(settings.MEDIA_ROOT, resized_path)
            os.makedirs(os.path.dirname(full_resized_path), exist_ok=True)
            resized_img.save(full_resized_path)

            resized_urls.append(settings.MEDIA_URL + resized_path)

        return JsonResponse({
            'resized_urls': resized_urls
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)



SUPPORTED_FORMATS = {
    'JPG': 'JPEG',
    'PNG': 'PNG',
    'WEBP': 'WEBP',
    'BMP': 'BMP',
    'TIFF': 'TIFF',
    'ICO': 'ICO',
    'PDF': 'PDF',
}

# 2. Compress
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, description='이미지들', required=True, multiple=True),
        openapi.Parameter('quality', openapi.IN_FORM, type=openapi.TYPE_STRING, description='압축 품질 (high/medium/low)', required=True),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def convert_image_format(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        target_format = request.POST.get('format', 'PNG').upper()

        if target_format not in SUPPORTED_FORMATS:
            return JsonResponse({'error': 'Unsupported format'}, status=400)

        ext = SUPPORTED_FORMATS[target_format]
        converted_urls = []

        for uploaded_file in images:
            original_path = default_storage.save('original/' + uploaded_file.name, uploaded_file)
            full_input_path = os.path.join(settings.MEDIA_ROOT, original_path)

            # PDF → 이미지로 변환
            if uploaded_file.name.lower().endswith('.pdf') and target_format != 'PDF':
                from pdf2image import convert_from_path
                output_dir = os.path.join(settings.MEDIA_ROOT, 'converted')
                os.makedirs(output_dir, exist_ok=True)

                try:
                    pages = convert_from_path(full_input_path)
                except Exception:
                    continue  # PDF 변환 실패 시 skip

                for i, page in enumerate(pages):
                    converted_filename = f"{os.path.splitext(uploaded_file.name)[0]}_page_{i+1}.{target_format.lower()}"
                    output_path = os.path.join(output_dir, converted_filename)
                    page.convert("RGB").save(output_path, ext)
                    converted_urls.append(settings.MEDIA_URL + 'converted/' + converted_filename)

            else:
                try:
                    img = Image.open(full_input_path)
                    filename_wo_ext = os.path.splitext(uploaded_file.name)[0]
                    converted_filename = f"{filename_wo_ext}.{target_format.lower()}"
                    converted_path = f"converted/{converted_filename}"
                    full_output_path = os.path.join(settings.MEDIA_ROOT, converted_path)

                    os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
                    img.convert("RGB").save(full_output_path, ext)
                    converted_urls.append(settings.MEDIA_URL + converted_path)
                except Exception:
                    continue  # 이미지 변환 실패 시 skip

        return JsonResponse({
            'converted_urls': converted_urls
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

# 3. Convert
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, description='이미지들 or PDF', required=True, multiple=True),
        openapi.Parameter('format', openapi.IN_FORM, type=openapi.TYPE_STRING, description='변환 포맷 (jpg/png/webp/pdf 등)', required=True),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def compress_image(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        quality_level = request.POST.get('quality', 'medium').lower()

        # 허용된 확장자
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
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
                continue  # 지원되지 않는 확장자는 skip

            original_path = default_storage.save('original/' + img_file.name, img_file)
            full_input_path = os.path.join(settings.MEDIA_ROOT, original_path)

            try:
                img = Image.open(full_input_path).convert("RGB")
                filename_wo_ext = os.path.splitext(img_file.name)[0]
                compressed_filename = f"{filename_wo_ext}_compressed.jpg"
                compressed_path = f"compressed/{compressed_filename}"
                full_output_path = os.path.join(settings.MEDIA_ROOT, compressed_path)

                os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
                img.save(full_output_path, "JPEG", quality=quality)

                compressed_urls.append(settings.MEDIA_URL + compressed_path)
            except Exception:
                continue  # 오류 발생 시 해당 파일 건너뜀

        return JsonResponse({
            'compressed_urls': compressed_urls
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

# 4. Filter
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, description='이미지들', required=True, multiple=True),
        openapi.Parameter('filter', openapi.IN_FORM, type=openapi.TYPE_STRING, description='필터 이름 (grayscale, sepia 등)', required=True),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def apply_filter(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        filter_name = request.POST.get('filter', 'grayscale').lower()

        filtered_urls = []

        for img_file in images:
            original_path = default_storage.save('original/' + img_file.name, img_file)
            full_input_path = os.path.join(settings.MEDIA_ROOT, original_path)

            try:
                img = Image.open(full_input_path).convert("RGB")
            except Exception:
                continue  # 이미지 열기 실패시 skip

            # 필터 적용
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
                continue  # 지원하지 않는 필터는 skip

            # 저장
            filename_wo_ext = os.path.splitext(img_file.name)[0]
            filtered_filename = f"{filename_wo_ext}_{filter_name}.jpg"
            filtered_path = f"filtered/{filtered_filename}"
            full_output_path = os.path.join(settings.MEDIA_ROOT, filtered_path)

            os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
            img.save(full_output_path, "JPEG")

            filtered_urls.append(settings.MEDIA_URL + filtered_path)

        return JsonResponse({
            'filtered_urls': filtered_urls
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

# 5. Watermark
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, description='이미지들', required=True, multiple=True),
        openapi.Parameter('type', openapi.IN_FORM, type=openapi.TYPE_STRING, description='text 또는 image', required=True),
        openapi.Parameter('text', openapi.IN_FORM, type=openapi.TYPE_STRING, description='텍스트 워터마크 내용'),
        openapi.Parameter('position', openapi.IN_FORM, type=openapi.TYPE_STRING, description='위치 (center, bottom-right, top-left)', default='bottom-right'),
        openapi.Parameter('opacity', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='불투명도 0~255'),
        openapi.Parameter('watermark_image', openapi.IN_FORM, type=openapi.TYPE_FILE, description='워터마크 이미지 (선택)', required=False),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def add_watermark(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        wm_type = request.POST.get('type', 'text')
        text = request.POST.get('text', 'FilePick')
        opacity = int(request.POST.get('opacity', 128))
        position = request.POST.get('position', 'bottom-right')

        watermark_urls = []

        # 이미지 워터마크 준비
        wm_img = None
        if wm_type == 'image' and request.FILES.get('watermark_image'):
            wm_path = default_storage.save('wm/' + request.FILES['watermark_image'].name, request.FILES['watermark_image'])
            wm_img = Image.open(os.path.join(settings.MEDIA_ROOT, wm_path)).convert("RGBA")

        for img_file in images:
            try:
                original_path = default_storage.save('original/' + img_file.name, img_file)
                full_input_path = os.path.join(settings.MEDIA_ROOT, original_path)
                base_img = Image.open(full_input_path).convert("RGBA")

                watermark = Image.new("RGBA", base_img.size, (0, 0, 0, 0))

                if wm_type == 'text':
                    draw = ImageDraw.Draw(watermark)
                    font_size = int(min(base_img.size) * 0.05)
                    try:
                        font_path = "/Library/Fonts/Arial.ttf"  # macOS 기준
                        font = ImageFont.truetype(font_path, font_size)
                    except:
                        font = ImageFont.load_default()
                        font_size = 30  # 기본 폰트 보정

                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    text_size = (text_width, text_height)
                    x, y = get_position(position, base_img.size, text_size)

                    draw.text((x, y), text, fill=(0, 0, 0, opacity), font=font)

                elif wm_type == 'image' and wm_img:
                    wm_resized = wm_img.resize((int(base_img.size[0] * 0.25), int(base_img.size[1] * 0.25)))
                    if opacity < 255:
                        alpha = wm_resized.getchannel('A')
                        new_alpha = alpha.point(lambda p: int(p * (opacity / 255)))
                        wm_resized.putalpha(new_alpha)
                    else:
                        wm_resized.putalpha(255)

                    x, y = get_position(position, base_img.size, wm_resized.size)
                    watermark.paste(wm_resized, (x, y), wm_resized)

                combined = Image.alpha_composite(base_img, watermark).convert("RGB")

                filename_wo_ext = os.path.splitext(img_file.name)[0]
                output_filename = f"{filename_wo_ext}_watermarked.jpg"
                output_path = f"watermarked/{output_filename}"
                full_output_path = os.path.join(settings.MEDIA_ROOT, output_path)
                os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
                combined.save(full_output_path, "JPEG")

                watermark_urls.append(settings.MEDIA_URL + output_path)

            except Exception as e:
                continue

        return JsonResponse({'watermarked_urls': watermark_urls})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_position(position, base_size, wm_size):
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