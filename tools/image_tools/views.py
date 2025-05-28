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
from supabase import create_client, Client
import io
import uuid
import tempfile

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = "images"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
            try:
                img = Image.open(img_file)
                resized_img = img.resize((width, height))

                # Pillow 이미지 → BytesIO 메모리 저장
                img_io = io.BytesIO()
                resized_img.save(img_io, format='PNG')
                img_io.seek(0)

                # Supabase 저장 경로
                filename = f"resized/{uuid.uuid4()}.png"

                # BytesIO → 임시파일 저장
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    tmp_file.write(img_io.getbuffer())
                    tmp_file_path = tmp_file.name

                # Supabase 업로드
                res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=filename,
                    file=tmp_file_path,
                    file_options={"content-type": "image/png"}
                )

                if hasattr(res, "error") and res.error:
                    print("Upload error:", res.error)
                    continue

                public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
                resized_urls.append(public_url)

                # 임시파일 삭제
                os.remove(tmp_file_path)

            except Exception as e:
                print("Exception occurred:", e)
                continue

        return JsonResponse({'resized_urls': resized_urls})

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

# 2. Convert
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
            try:
                if uploaded_file.name.lower().endswith('.pdf') and target_format != 'PDF':
                    from pdf2image import convert_from_bytes
                    pdf_bytes = uploaded_file.read()
                    pages = convert_from_bytes(pdf_bytes)

                    for i, page in enumerate(pages):
                        img_io = io.BytesIO()
                        page.convert("RGB").save(img_io, ext)
                        img_io.seek(0)

                        filename = f"converted/{uuid.uuid4()}_page_{i+1}.{target_format.lower()}"
                        with tempfile.NamedTemporaryFile(suffix=f".{target_format.lower()}", delete=False) as tmp_file:
                            tmp_file.write(img_io.getbuffer())
                            tmp_file_path = tmp_file.name

                        res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                            path=filename,
                            file=tmp_file_path,
                            file_options={"content-type": f"image/{target_format.lower()}"}
                        )

                        if hasattr(res, "error") and res.error:
                            print("Upload error:", res.error)
                            continue

                        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
                        converted_urls.append(public_url)
                        os.remove(tmp_file_path)

                else:
                    img = Image.open(uploaded_file).convert("RGB")
                    img_io = io.BytesIO()
                    img.save(img_io, ext)
                    img_io.seek(0)

                    filename = f"converted/{uuid.uuid4()}.{target_format.lower()}"
                    with tempfile.NamedTemporaryFile(suffix=f".{target_format.lower()}", delete=False) as tmp_file:
                        tmp_file.write(img_io.getbuffer())
                        tmp_file_path = tmp_file.name

                    res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                        path=filename,
                        file=tmp_file_path,
                        file_options={"content-type": f"image/{target_format.lower()}"}
                    )

                    if hasattr(res, "error") and res.error:
                        print("Upload error:", res.error)
                        continue

                    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
                    converted_urls.append(public_url)
                    os.remove(tmp_file_path)

            except Exception as e:
                print("Exception occurred:", e)
                continue

        return JsonResponse({'converted_urls': converted_urls})

    return JsonResponse({'error': 'Invalid request'}, status=400)


# 3. Compress
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, description='이미지들 (jpg/png/webp 등)', required=True, multiple=True),
        openapi.Parameter('quality', openapi.IN_FORM, type=openapi.TYPE_STRING, description='압축 품질 (high/medium/low)', required=False),
    ]
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def compress_image(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        quality_level = request.POST.get('quality', 'medium').lower()

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
                continue

            try:
                img = Image.open(img_file).convert("RGB")
                img_io = io.BytesIO()
                img.save(img_io, "JPEG", quality=quality)
                img_io.seek(0)

                filename = f"compressed/{uuid.uuid4()}.jpg"

                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                    tmp_file.write(img_io.getbuffer())
                    tmp_file_path = tmp_file.name

                res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=filename,
                    file=tmp_file_path,
                    file_options={"content-type": "image/jpeg"}
                )

                if hasattr(res, "error") and res.error:
                    print("Upload error:", res.error)
                    continue

                public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
                compressed_urls.append(public_url)
                os.remove(tmp_file_path)

            except Exception as e:
                print("Exception occurred:", e)
                continue

        return JsonResponse({'compressed_urls': compressed_urls})

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
                    continue

                img_io = io.BytesIO()
                img.save(img_io, "JPEG")
                img_io.seek(0)

                filename = f"filtered/{uuid.uuid4()}_{filter_name}.jpg"
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                    tmp_file.write(img_io.getbuffer())
                    tmp_file_path = tmp_file.name

                res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=filename,
                    file=tmp_file_path,
                    file_options={"content-type": "image/jpeg"}
                )

                if hasattr(res, "error") and res.error:
                    print("Upload error:", res.error)
                    continue

                public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
                filtered_urls.append(public_url)
                os.remove(tmp_file_path)

            except Exception as e:
                print("Exception occurred:", e)
                continue

        return JsonResponse({'filtered_urls': filtered_urls})

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
@csrf_exempt
def add_watermark(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        wm_type = request.POST.get('type', 'text')
        text = request.POST.get('text', 'FilePick')
        opacity = int(request.POST.get('opacity', 128))
        position = request.POST.get('position', 'bottom-right')

        watermark_urls = []

        wm_img = None
        if wm_type == 'image' and request.FILES.get('watermark_image'):
            try:
                wm_img = Image.open(request.FILES['watermark_image']).convert("RGBA")
            except Exception as e:
                print("Failed to open watermark image:", e)
                wm_img = None

        for img_file in images:
            try:
                base_img = Image.open(img_file).convert("RGBA")
                watermark = Image.new("RGBA", base_img.size, (0, 0, 0, 0))

                if wm_type == 'text':
                    draw = ImageDraw.Draw(watermark)
                    font_size = int(min(base_img.size) * 0.05)
                    try:
                        font_path = "/Library/Fonts/Arial.ttf"
                        font = ImageFont.truetype(font_path, font_size)
                    except:
                        font = ImageFont.load_default()
                        font_size = 30

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
                    else:
                        wm_resized.putalpha(255)

                    x, y = get_position(position, base_img.size, wm_resized.size)
                    watermark.paste(wm_resized, (x, y), wm_resized)

                combined = Image.alpha_composite(base_img, watermark).convert("RGB")
                img_io = io.BytesIO()
                combined.save(img_io, "JPEG")
                img_io.seek(0)

                filename = f"watermarked/{uuid.uuid4()}_watermarked.jpg"
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                    tmp_file.write(img_io.getbuffer())
                    tmp_file_path = tmp_file.name

                res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=filename,
                    file=tmp_file_path,
                    file_options={"content-type": "image/jpeg"}
                )

                if hasattr(res, "error") and res.error:
                    print("Upload error:", res.error)
                    continue

                public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
                watermark_urls.append(public_url)
                os.remove(tmp_file_path)

            except Exception as e:
                print("Exception occurred:", e)
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