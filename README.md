# 📁 FilePick (파일픽) - 파일 변환 및 편집 웹서비스

**FilePick**은 다양한 형식의 파일을 웹에서 변환, 압축, 편집할 수 있는 Django 기반 웹서비스입니다.

---

## 📌 주요 기능

### 1. 📁 파일 변환

- 문서: PDF ↔ Word, Excel, PPT, HWP 등
- 이미지: JPG ↔ PNG, BMP ↔ JPG, PNG ↔ SVG 등
- 오디오/비디오: MP3 ↔ WAV, MP4 ↔ AVI, MP4 → MP3

### 2. 🖼️ 이미지 처리

- 리사이즈, 크롭
- 포맷 변경 (PNG ↔ JPG 등)
- 압축, 필터 적용
- 워터마크 삽입/제거
- 선택 영역 모자이크

### 3. 📄 문서/PDF 도구

- 병합, 분할, 압축
- 페이지 회전/삭제
- 암호 설정 및 해제
- 텍스트 추출 (OCR 대응 예정)

### 4. 🧰 기타 유틸리티

- ZIP/RAR/7Z 압축 및 해제
- GIF 제작
- 동영상 트리밍
- EXIF 제거
- 문자셋 변환 (UTF-8 ↔ EUC-KR 등)

### 5. 🧠 AI 고급 기능 (예정)

- OCR (광학 문자 인식)
- 이미지 배경 제거
- 음성 → 텍스트 (STT)
- AI 업스케일링

---

## 🧱 프로젝트 구조

```plaintext
tools/
├── image_tools/
│   ├── views/resize.py          # 이미지 리사이즈 API
│   ├── views/compress.py        # 이미지 압축 API
│   └── services/uploader.py     # Supabase 이미지 업로드 래퍼
│
├── pdf_tools/
│   ├── views/merge.py           # PDF 병합 API
│   ├── views/split.py           # PDF 분할 API
│   ├── views/compress.py        # PDF 압축 API
│   ├── views/rotate_delete.py   # 페이지 회전/삭제 API
│   ├── views/encrypt_decrypt.py # 암호 설정/해제 API
│   └── services/uploader.py     # Supabase PDF 업로드 래퍼
│
├── common/
│   ├── storage.py               # Supabase 공통 업로드 함수
│   └── logging_utils.py         # 통합 로깅/에러 핸들링 유틸리티
```

### 🚀 실행 방법

### 1. 가상환경 설정

python -m venv venv
source venv/bin/activate

### 2. 의존성 설치

pip install -r requirements.txt

### 3. 서버 실행

python manage.py runserver
