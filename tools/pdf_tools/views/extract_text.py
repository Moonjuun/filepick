# tools/pdf_tools/views/extract_text.py

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from tools.pdf_tools.services.extractor import extract_text_from_pdf

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='file',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='텍스트를 추출할 PDF 파일',
            required=True
        )
    ],
    responses={200: '추출된 텍스트 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def extract_text(request):
    """
    업로드된 PDF 파일에서 텍스트를 추출하여 반환합니다.
    """
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    try:
        text = extract_text_from_pdf(uploaded_file)
        return JsonResponse({'extracted_text': text})
    except RuntimeError as e:
        return JsonResponse({'error': str(e)}, status=500)
