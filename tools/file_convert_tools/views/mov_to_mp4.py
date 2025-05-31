import os
import tempfile
import subprocess
from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from tools.file_convert_tools.services.uploader import upload_converted_file

@api_view(['POST'])
@parser_classes([MultiPartParser])
def convert_mov_to_mp4(request):
    try:
        file = request.FILES['file']
        if not file.name.lower().endswith('.mov'):
            return JsonResponse({'error': 'MOV 파일만 업로드 가능합니다.'}, status=400)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mov") as temp_mov:
            temp_mov.write(file.read())
            temp_mov_path = temp_mov.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_mp4:
            temp_mp4_path = temp_mp4.name

        ffmpeg_cmd = [
            'ffmpeg',
            '-i', temp_mov_path,
            '-c:v', 'libx264',  # 비디오 코덱
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',      # 오디오 코덱
            '-b:a', '192k',
            temp_mp4_path
        ]
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output_url = upload_converted_file(
            folder='mov-to-mp4',
            filename=os.path.basename(temp_mp4_path),
            file_path=temp_mp4_path,
            content_type="video/mp4"
        )

        os.remove(temp_mov_path)
        os.remove(temp_mp4_path)

        return JsonResponse({'url': output_url})
    
    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': f'FFmpeg 오류: {e.stderr.decode("utf-8", errors="ignore")}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'변환 실패: {str(e)}'}, status=500)
