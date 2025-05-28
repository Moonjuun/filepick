import os
import io
import uuid
import tempfile
import re
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from supabase import create_client, Client
from PyPDF2.errors import PdfReadError
from datetime import datetime


# Supabase 초기화
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_PDF_BUCKET = "pdf-files"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def sanitize_filename(filename: str) -> str:
    """파일명을 Supabase에서 사용할 수 있도록 ASCII-safe하게 변환"""
    name, ext = os.path.splitext(filename)
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    return f"{safe_name}{ext}"


"""
PDF 병합 기능 개요

입력: 여러 개의 PDF 파일
옵션: 없음
동작: 업로드된 모든 PDF 파일을 순서대로 병합
출력: Supabase Storage에 저장된 병합된 PDF 파일의 URL 반환
"""
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='files',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='병합할 PDF 파일들 (최소 2개 이상)',
            required=True,
            multiple=True
        )
    ],
    responses={200: '병합된 PDF 파일의 URL 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def merge_pdfs(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 지원합니다.'}, status=405)

    files = request.FILES.getlist('files')
    if not files or len(files) < 2:
        return JsonResponse({'error': 'PDF 파일은 최소 2개 이상 필요합니다.'}, status=400)

    # PDF 병합
    merger = PdfMerger()
    for f in files:
        merger.append(f)

    output_buffer = io.BytesIO()
    merger.write(output_buffer)
    merger.close()
    output_buffer.seek(0)

    # 파일명 생성 (예: merged/20250529_153402_ab12.pdf)
    short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
    filename = f"merged/{short_id}.pdf"

    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(output_buffer.getbuffer())
        tmp_file_path = tmp_file.name

    # Supabase 업로드
    res = supabase.storage.from_(SUPABASE_PDF_BUCKET).upload(
        path=filename,
        file=tmp_file_path,
        file_options={"content-type": "application/pdf"}
    )

    if hasattr(res, "error") and res.error:
        os.remove(tmp_file_path)
        return JsonResponse({'error': 'Supabase 업로드 실패'}, status=500)

    # public URL 반환
    public_url = supabase.storage.from_(SUPABASE_PDF_BUCKET).get_public_url(filename)

    os.remove(tmp_file_path)
    return JsonResponse({'merged_url': public_url})


"""
PDF 분할 기능 개요

입력: 여러 개의 PDF 파일  
옵션: 분할할 페이지 범위 또는 단일 페이지 번호 (예: "0,2" → 1p, 3p 추출)  
동작: 각 PDF에 동일한 설정 적용하여 분할  
출력: 분할된 PDF 파일들을 Supabase에 저장하고 URL 목록 반환
"""
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='files',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='분할할 PDF 파일들 (다중 업로드 가능)',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='pages',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='추출할 페이지 번호 목록 (예: "0,2")',
            required=True
        )
    ],
    responses={200: '분할된 PDF 파일들의 URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def split_pdfs(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 지원합니다.'}, status=405)

    files = request.FILES.getlist('files')
    pages_str = request.POST.get('pages', '')
    if not files or not pages_str:
        return JsonResponse({'error': '파일과 pages는 필수입니다.'}, status=400)

    try:
        pages = [int(p.strip()) for p in pages_str.split(',') if p.strip().isdigit()]
    except Exception:
        return JsonResponse({'error': 'pages 형식이 잘못되었습니다. (예: "0,2")'}, status=400)

    split_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            for i in pages:
                if i < len(reader.pages):
                    writer.add_page(reader.pages[i])

            # PDF → BytesIO 저장
            split_pdf = io.BytesIO()
            writer.write(split_pdf)
            split_pdf.seek(0)

            # 짧은 파일 이름 생성 (예: split/20250529_153012_ab12.pdf)
            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"split/{short_id}.pdf"

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(split_pdf.getbuffer())
                tmp_file_path = tmp_file.name

            # Supabase 업로드
            res = supabase.storage.from_(SUPABASE_PDF_BUCKET).upload(
                path=filename,
                file=tmp_file_path,
                file_options={"content-type": "application/pdf"}
            )

            if hasattr(res, "error") and res.error:
                os.remove(tmp_file_path)
                continue

            public_url = supabase.storage.from_(SUPABASE_PDF_BUCKET).get_public_url(filename)
            split_urls.append(public_url)

            os.remove(tmp_file_path)

        except Exception as e:
            print("Split error:", e)
            continue

    return JsonResponse({'split_urls': split_urls})



"""
PDF 압축 기능 개요

입력: 여러 개의 PDF 파일  
옵션: 압축 품질 (low, medium, high)  
동작: 이미지 품질 조정 및 불필요한 객체 제거를 통해 PDF 용량 축소  
출력: 압축된 PDF 파일들을 Supabase에 저장하고 URL 목록 반환
"""
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='files',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='압축할 PDF 파일들 (다중 업로드 가능)',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='quality',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='압축 품질 (low, medium, high)',
            required=False,
            default='medium'
        )
    ],
    responses={200: '압축된 PDF 파일들의 URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def compress_pdfs(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 지원합니다.'}, status=405)

    files = request.FILES.getlist('files')
    quality = request.POST.get('quality', 'medium')

    if not files:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    compressed_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # 메타데이터 제거 (간단한 압축 방식)
            writer.add_metadata({})

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)

            # 짧은 파일 이름 생성 (예: compressed/20250529_154812_a1b2.pdf)
            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"compressed/{short_id}.pdf"

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(output.getbuffer())
                tmp_file_path = tmp_file.name

            res = supabase.storage.from_(SUPABASE_PDF_BUCKET).upload(
                path=filename,
                file=tmp_file_path,
                file_options={"content-type": "application/pdf"}
            )

            if hasattr(res, "error") and res.error:
                os.remove(tmp_file_path)
                continue

            public_url = supabase.storage.from_(SUPABASE_PDF_BUCKET).get_public_url(filename)
            compressed_urls.append(public_url)
            os.remove(tmp_file_path)

        except Exception as e:
            print("Compress error:", e)
            continue

    return JsonResponse({'compressed_urls': compressed_urls})


"""
PDF 페이지 회전 및 삭제 기능 개요

입력: 여러 개의 PDF 파일  
옵션: 회전 각도 (0, 90, 180, 270), 삭제할 페이지 번호들 (예: "1,3")  
동작: 각 PDF 파일에 대해 동일한 설정(회전/삭제)을 적용  
출력: 처리된 PDF 파일들을 Supabase에 저장하고 URL 목록 반환
"""
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='files',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='회전/삭제할 PDF 파일들 (다중 업로드 가능)',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='rotate',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_INTEGER,
            description='회전 각도 (0, 90, 180, 270 중 택)',
            required=False
        ),
        openapi.Parameter(
            name='delete_pages',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='삭제할 페이지 번호 (예: "0,2")',
            required=False
        )
    ],
    responses={200: '처리된 PDF들의 URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def rotate_or_delete_pdfs(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 지원합니다.'}, status=405)

    files = request.FILES.getlist('files')
    rotate = request.POST.get('rotate')
    delete_pages_str = request.POST.get('delete_pages', '')

    if not files:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    delete_pages = set()
    if delete_pages_str:
        try:
            delete_pages = set(int(i.strip()) for i in delete_pages_str.split(',') if i.strip().isdigit())
        except Exception:
            return JsonResponse({'error': 'delete_pages 형식이 잘못되었습니다.'}, status=400)

    if rotate:
        try:
            rotate = int(rotate)
            assert rotate in [0, 90, 180, 270]
        except Exception:
            return JsonResponse({'error': 'rotate 값은 0, 90, 180, 270 중 하나여야 합니다.'}, status=400)

    processed_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            for idx, page in enumerate(reader.pages):
                if idx in delete_pages:
                    continue
                if rotate:
                    page.rotate(rotate)
                writer.add_page(page)

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)

            # 파일명 생성 (예: processed/20250529_160102_abcd.pdf)
            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"processed/{short_id}.pdf"

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(output.getbuffer())
                tmp_file_path = tmp_file.name

            res = supabase.storage.from_(SUPABASE_PDF_BUCKET).upload(
                path=filename,
                file=tmp_file_path,
                file_options={"content-type": "application/pdf"}
            )

            if hasattr(res, "error") and res.error:
                os.remove(tmp_file_path)
                continue

            public_url = supabase.storage.from_(SUPABASE_PDF_BUCKET).get_public_url(filename)
            processed_urls.append(public_url)
            os.remove(tmp_file_path)

        except Exception as e:
            print("Rotate/Delete error:", e)
            continue

    return JsonResponse({'processed_urls': processed_urls})


"""
PDF 암호 설정 / 해제 기능 개요

입력: 여러 개의 PDF 파일  
옵션: 모드 ("encrypt" 또는 "decrypt"), 비밀번호  
동작:  
    - encrypt 모드: 모든 PDF 파일에 동일한 비밀번호 설정  
    - decrypt 모드: 동일한 비밀번호로 모든 PDF 암호 해제  
출력: 처리된 PDF 파일들을 Supabase에 저장하고 URL 목록 반환
"""

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            name='files',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='암호 설정/해제할 PDF 파일들 (다중 업로드 가능)',
            required=True,
            multiple=True
        ),
        openapi.Parameter(
            name='mode',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='"encrypt" 또는 "decrypt"',
            required=True
        ),
        openapi.Parameter(
            name='password',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            description='설정 또는 해제에 사용할 비밀번호',
            required=True
        )
    ],
    responses={200: '처리된 PDF들의 URL 목록 반환'}
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def encrypt_or_decrypt_pdfs(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 지원합니다.'}, status=405)

    files = request.FILES.getlist('files')
    mode = request.POST.get('mode')
    password = request.POST.get('password')

    if not files or not mode or not password:
        return JsonResponse({'error': '파일, mode, password는 필수입니다.'}, status=400)

    if mode not in ['encrypt', 'decrypt']:
        return JsonResponse({'error': 'mode는 "encrypt" 또는 "decrypt"만 가능합니다.'}, status=400)

    result_urls = []

    for f in files:
        try:
            reader = PdfReader(f)
            writer = PdfWriter()

            if mode == 'decrypt':
                if reader.is_encrypted:
                    reader.decrypt(password)
                for page in reader.pages:
                    writer.add_page(page)
            else:  # encrypt
                for page in reader.pages:
                    writer.add_page(page)
                writer.encrypt(password)

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)

            # 파일명 생성 (예: encrypt/20250529_160455_abcd.pdf or decrypt/20250529_160455_abcd.pdf)
            short_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(uuid.uuid4())[:4]
            filename = f"{mode}/{short_id}.pdf"

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(output.getbuffer())
                tmp_file_path = tmp_file.name

            res = supabase.storage.from_(SUPABASE_PDF_BUCKET).upload(
                path=filename,
                file=tmp_file_path,
                file_options={"content-type": "application/pdf"}
            )

            if hasattr(res, "error") and res.error:
                os.remove(tmp_file_path)
                continue

            public_url = supabase.storage.from_(SUPABASE_PDF_BUCKET).get_public_url(filename)
            result_urls.append(public_url)
            os.remove(tmp_file_path)

        except PdfReadError:
            return JsonResponse({'error': f'PDF 해독 실패: {f.name}'}, status=400)
        except Exception as e:
            print("Encrypt/Decrypt error:", e)
            continue

    return JsonResponse({'result_urls': result_urls})