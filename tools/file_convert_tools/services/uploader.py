# tools/file_convert_tools/services/uploader.py

from tools.common.storage import upload_to_supabase

def upload_converted_file(
        folder: str, 
        filename: str, 
        file_path: str, 
        content_type: str = "application/pdf"
        ) -> str:
    """
    변환된 파일을 Supabase의 'converted-files' 버킷에 업로드
    """
    with open(file_path, "rb") as f:
        return upload_to_supabase(
            bucket="converted-files",  # ← Supabase의 파일 변환 전용 버킷
            folder=folder,
            filename=filename,
            content=f.read(),
            content_type=content_type
        )
