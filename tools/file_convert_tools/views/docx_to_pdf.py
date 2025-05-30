import os
import uuid
import tempfile
import subprocess
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from tools.file_convert_tools.services.uploader import upload_converted_file

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='file',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='변환할 DOCX 파일',
            required=True
        )
    ],
    responses={200: '변환된 PDF 파일 URL'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def convert_docx_to_pdf(request):
    """
    DOCX 파일을 PDF로 변환 후 Supabase에 업로드합니다.
    LibreOffice CLI를 사용하므로 리눅스/macOS에서도 동작합니다.
    """
    uploaded_file = request.FILES.get('file')
    if not uploaded_file or not uploaded_file.name.endswith('.docx'):
        return JsonResponse({'error': 'DOCX 파일이 필요합니다.'}, status=400)

    try:
        # 임시 .docx 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
            tmp_docx.write(uploaded_file.read())
            tmp_docx_path = tmp_docx.name

        # LibreOffice로 변환
        output_dir = tempfile.mkdtemp()
        subprocess.run([
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            tmp_docx_path
        ], check=True)

        # 변환된 파일 경로
        base_name = os.path.splitext(os.path.basename(tmp_docx_path))[0]
        converted_path = os.path.join(output_dir, base_name + ".pdf")

        # Supabase에 업로드
        filename = f"{uuid.uuid4()}.pdf"
        public_url = upload_converted_file(
            folder="docx-to-pdf",
            filename=filename,
            file_path=converted_path,
            content_type="application/pdf"
        )

        # 정리
        os.remove(tmp_docx_path)
        os.remove(converted_path)

        return JsonResponse({'converted_url': public_url})

    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': 'LibreOffice 변환 실패. 설치 여부를 확인하세요.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'변환 실패: {str(e)}'}, status=500)
