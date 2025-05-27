from django.shortcuts import render
from django.http import JsonResponse
from PIL import Image
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

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
