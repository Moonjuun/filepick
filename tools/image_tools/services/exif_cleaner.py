# tools/image_tools/services/exif_cleaner.py

from PIL import Image
import io

def remove_exif(image_file) -> io.BytesIO:
    """EXIF 메타데이터를 제거한 이미지를 반환합니다."""
    image = Image.open(image_file)

    # EXIF 제거를 위해 새 이미지에 복사
    data = list(image.getdata())
    no_exif_image = Image.new(image.mode, image.size)
    no_exif_image.putdata(data)

    output = io.BytesIO()
    no_exif_image.save(output, format=image.format)
    output.seek(0)
    return output
