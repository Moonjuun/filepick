# tools/file_convert_tools/views/mp4_to_mp3.py

import os
import uuid
import tempfile
import subprocess
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from tools.file_convert_tools.services.uploader import upload_converted_file


@api_view(['POST'])
@parser_classes([MultiPartParser])
def convert_mp4_to_mp3(request):
    try:
        uploaded_file = request.FILES['file']
        file_ext = os.path.splitext(uploaded_file.name)[-1].lower()

        if file_ext != '.mp4':
            return JsonResponse({'error': 'MP4 파일만 지원됩니다.'}, status=400)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            temp_input.write(uploaded_file.read())
            temp_input_path = temp_input.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_output:
            temp_output_path = temp_output.name

        # FFmpeg를 이용한 MP3 추출
        command = [
            "ffmpeg", "-i", temp_input_path,
            "-map", "a",  # 오디오 스트림만 추출
            "-acodec", "libmp3lame", "-y", temp_output_path
        ]

        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 업로드 및 응답
        file_id = str(uuid.uuid4())
        filename = f"{os.path.splitext(uploaded_file.name)[0]}_{file_id}.mp3"
        url = upload_converted_file(
            folder="audio",
            filename=filename,
            file_path=temp_output_path,
            content_type="audio/mpeg"
        )

        os.remove(temp_input_path)
        os.remove(temp_output_path)

        return JsonResponse({'url': url})

    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': f'변환 실패: {e.stderr.decode("utf-8")}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'변환 실패: {str(e)}'}, status=500)
