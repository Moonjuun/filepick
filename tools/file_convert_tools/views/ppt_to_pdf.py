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
            description='PPT 또는 PPTX 파일',
            required=True
        )
    ],
    responses={200: '변환된 PDF 파일 URL'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def convert_ppt_to_pdf(request):
    """
    업로드된 PPT(PPTX) 파일을 PDF로 변환하여 Supabase에 업로드합니다.
    """
    uploaded_file = request.FILES.get('file')
    if not uploaded_file or not uploaded_file.name.lower().endswith(('.ppt', '.pptx')):
        return JsonResponse({'error': 'PPT 또는 PPTX 파일이 필요합니다.'}, status=400)

    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_input:
            tmp_input.write(uploaded_file.read())
            input_path = tmp_input.name

        # LibreOffice로 변환 수행
        output_dir = tempfile.mkdtemp()
        command = [
            "soffice", "--headless", "--convert-to", "pdf",
            "--outdir", output_dir,
            input_path
        ]
        subprocess.run(command, check=True)

        # 변환된 파일 경로 구성
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.pdf")

        # Supabase 업로드
        filename = f"{uuid.uuid4()}.pdf"
        public_url = upload_converted_file(
            folder="ppt-to-pdf",
            filename=filename,
            file_path=output_path,
            content_type="application/pdf"
        )

        # 정리
        os.remove(input_path)
        os.remove(output_path)

        return JsonResponse({'converted_url': public_url})

    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': f'LibreOffice 변환 실패: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'처리 실패: {str(e)}'}, status=500)
