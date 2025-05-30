# tools/pdf_tools/services/extractor.py

import io
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_obj) -> str:
    """
    PDF 파일에서 텍스트를 추출하여 반환합니다.
    """
    text = ""
    try:
        reader = PdfReader(file_obj)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        raise RuntimeError(f"텍스트 추출 실패: {str(e)}")
    return text.strip()
