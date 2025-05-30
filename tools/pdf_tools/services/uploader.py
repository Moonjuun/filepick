# tools/pdf_tools/services/uploader.py

from tools.common.storage import upload_to_supabase

def upload_pdf(
    folder: str,           # 예: "merged", "split", "compressed"
    filename: str,         # 예: "20250601_123456_abcd.pdf"
    content: bytes         # PDF 파일의 바이트 데이터 (예: BytesIO.getbuffer())
) -> str:
    """
    PDF 파일을 Supabase Storage의 'pdf-files' 버킷에 업로드하고 public URL을 반환합니다.

    예:
        upload_pdf(
            folder="compressed",
            filename="doc1234.pdf",
            content=output.getbuffer()
        )
    """
    return upload_to_supabase(
        bucket="pdf-files",
        folder=folder,
        filename=filename,
        content=content,
        content_type="application/pdf"
    )
