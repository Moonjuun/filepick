# tools/image_tools/services/uploader.py

from tools.common.storage import upload_to_supabase

def upload_image(
    folder: str,           # 예: "resized", "compressed"
    filename: str,         # 예: "abc1234.jpg"
    content: bytes,        # 이미지 바이트 데이터 (예: img_io.getbuffer())
    content_type: str = "image/jpeg"  # 기본: JPEG
) -> str:
    """
    이미지 파일을 Supabase Storage의 'images' 버킷에 업로드하고 public URL을 반환합니다.

    예:
        upload_image(
            folder="converted",
            filename="xyz5678.png",
            content=img_io.getbuffer(),
            content_type="image/png"
        )
    """
    return upload_to_supabase(
        bucket="images",
        folder=folder,
        filename=filename,
        content=content,
        content_type=content_type
    )
