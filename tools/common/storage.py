# tools/common/storage.py

import os
import tempfile
from supabase import create_client

# Supabase 환경 변수에서 URL과 서비스 키를 불러옵니다.
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Supabase 클라이언트 초기화
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_to_supabase(
    bucket: str,           # 예: "images", "pdf-files"
    folder: str,           # 예: "resized", "compressed"
    filename: str,         # 예: "abc1234.jpg"
    content: bytes,        # 이미지나 PDF 파일의 바이트 데이터
    content_type: str = "application/octet-stream"  # MIME 타입 (기본값: 일반 파일)
) -> str:
    """
    Supabase Storage에 파일을 업로드하고, 공개 URL을 반환합니다.

    예:
        upload_to_supabase(
            bucket="images",
            folder="converted",
            filename="abc1234.png",
            content=img_io.getbuffer(),
            content_type="image/png"
        )

    실패 시 Exception을 발생시키며, 성공 시 공개 접근 가능한 URL을 문자열로 반환합니다.
    """
    # Supabase 내 전체 경로 구성 (예: converted/abc1234.png)
    path = f"{folder}/{filename}"

    # 임시 파일로 저장 (Supabase 라이브러리가 파일 경로 기반으로 업로드함)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name  # 경로 기억해두기

    # Supabase 업로드 실행
    res = supabase.storage.from_(bucket).upload(
        path=path,
        file=tmp_file_path,
        file_options={"content-type": content_type}
    )

    # 업로드 이후 임시 파일 삭제
    os.remove(tmp_file_path)

    # 업로드 실패 시 에러 반환
    if hasattr(res, "error") and res.error:
        raise Exception(f"Supabase 업로드 실패: {res.error}")

    # 성공한 경우 public URL 반환
    return supabase.storage.from_(bucket).get_public_url(path)
