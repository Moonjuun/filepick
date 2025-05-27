from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from PIL import Image, ImageFilter, ImageEnhance
from django.core.files.storage import default_storage
from django.conf import settings
import os

@csrf_exempt
def resize_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        img_file = request.FILES['image']
        width = int(request.POST.get('width', 300))  # 기본 300px
        height = int(request.POST.get('height', 300))

        # 원본 저장
        path = default_storage.save('original/' + img_file.name, img_file)

        # Pillow로 열기 + 리사이즈
        img = Image.open(os.path.join(settings.MEDIA_ROOT, path))
        resized_img = img.resize((width, height))
        
        # 저장할 경로
        resized_path = 'resized/resized_' + img_file.name
        full_resized_path = os.path.join(settings.MEDIA_ROOT, resized_path)
        os.makedirs(os.path.dirname(full_resized_path), exist_ok=True)
        resized_img.save(full_resized_path)

        # URL로 반환
        return JsonResponse({
            'resized_url': settings.MEDIA_URL + resized_path
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

@csrf_exempt
def convert_image_format(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        target_format = request.POST.get('format', 'PNG').upper()

        if target_format not in SUPPORTED_FORMATS:
            return JsonResponse({'error': 'Unsupported format'}, status=400)

        ext = SUPPORTED_FORMATS[target_format]
        original_path = default_storage.save('original/' + uploaded_file.name, uploaded_file)
        full_input_path = os.path.join(settings.MEDIA_ROOT, original_path)

        # 입력이 PDF인 경우 → 이미지로 변환
        if uploaded_file.name.lower().endswith('.pdf') and target_format != 'PDF':
            output_dir = os.path.join(settings.MEDIA_ROOT, 'converted')
            os.makedirs(output_dir, exist_ok=True)

            images = convert_from_path(full_input_path)
            urls = []
            for i, page in enumerate(images):
                converted_filename = f"{os.path.splitext(uploaded_file.name)[0]}_page_{i+1}.{target_format.lower()}"
                output_path = os.path.join(output_dir, converted_filename)
                page.convert("RGB").save(output_path, ext)
                urls.append(settings.MEDIA_URL + 'converted/' + converted_filename)

            return JsonResponse({'converted_urls': urls})

        # 일반 이미지 → 다른 포맷 (or PDF) 변환
        img = Image.open(full_input_path)
        filename_wo_ext = os.path.splitext(uploaded_file.name)[0]
        converted_filename = f"{filename_wo_ext}.{target_format.lower()}"
        converted_path = f"converted/{converted_filename}"
        full_output_path = os.path.join(settings.MEDIA_ROOT, converted_path)

        os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
        img.convert("RGB").save(full_output_path, ext)

        return JsonResponse({
            'converted_url': settings.MEDIA_URL + converted_path
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def compress_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        img_file = request.FILES['image']
        quality_level = request.POST.get('quality', 'medium').lower()

        # 허용된 확장자 목록 (이미지 파일만 허용)
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        ext = os.path.splitext(img_file.name)[1].lower()

        if ext not in allowed_extensions:
            return JsonResponse({'error': 'Only image files can be compressed.'}, status=400)

        quality_map = {
            'high': 85,
            'medium': 65,
            'low': 40
        }
        quality = quality_map.get(quality_level, 65)

        # 저장 경로
        original_path = default_storage.save('original/' + img_file.name, img_file)
        full_input_path = os.path.join(settings.MEDIA_ROOT, original_path)

        # 열기 + 압축 저장
        img = Image.open(full_input_path).convert("RGB")
        filename_wo_ext = os.path.splitext(img_file.name)[0]
        compressed_filename = f"{filename_wo_ext}_compressed.jpg"
        compressed_path = f"compressed/{compressed_filename}"
        full_output_path = os.path.join(settings.MEDIA_ROOT, compressed_path)
        os.makedirs(os.path.dirname(full_output_path), exist_ok=True)

        img.save(full_output_path, "JPEG", quality=quality)

        return JsonResponse({
            'compressed_url': settings.MEDIA_URL + compressed_path
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def apply_filter(request):
    if request.method == 'POST' and request.FILES.get('image'):
        img_file = request.FILES['image']
        filter_name = request.POST.get('filter', 'grayscale').lower()

        original_path = default_storage.save('original/' + img_file.name, img_file)
        full_input_path = os.path.join(settings.MEDIA_ROOT, original_path)

        try:
            img = Image.open(full_input_path).convert("RGB")
        except Exception:
            return JsonResponse({'error': 'Unsupported image file.'}, status=400)

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
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)  # 1.0 = 원본

        elif filter_name == 'brightness':
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.3)  # 1.0 = 원본

        elif filter_name == 'edge':
            img = img.filter(ImageFilter.FIND_EDGES)

        else:
            return JsonResponse({'error': 'Unsupported filter type'}, status=400)

        # 저장
        filename_wo_ext = os.path.splitext(img_file.name)[0]
        filtered_filename = f"{filename_wo_ext}_{filter_name}.jpg"
        filtered_path = f"filtered/{filtered_filename}"
        full_output_path = os.path.join(settings.MEDIA_ROOT, filtered_path)
        os.makedirs(os.path.dirname(full_output_path), exist_ok=True)

        img.save(full_output_path, "JPEG")

        return JsonResponse({
            'filtered_url': settings.MEDIA_URL + filtered_path
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)
