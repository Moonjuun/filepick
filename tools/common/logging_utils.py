# tools/common/logging_utils.py

import logging
import traceback
from django.http import JsonResponse

# 기본 로깅 설정
logger = logging.getLogger("filepick")
logger.setLevel(logging.INFO)

# 콘솔 핸들러 추가
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def log_exception(error: Exception, context: str = ""):
    """
    예외 로그를 기록하고 콘솔에 스택트레이스를 출력합니다.
    """
    logger.error(f"[ERROR] {context} - {str(error)}")
    traceback_str = traceback.format_exc()
    logger.debug(traceback_str)


def json_error(message: str, status: int = 400) -> JsonResponse:
    """
    일관된 에러 응답 JSON 객체 반환
    """
    return JsonResponse({"error": message}, status=status)


def json_success(data: dict, status: int = 200) -> JsonResponse:
    """
    일관된 성공 응답 JSON 객체 반환
    """
    return JsonResponse(data, status=status)


def log_info(message: str):
    """
    일반 정보 로그 출력
    """
    logger.info(message)


def log_debug(message: str):
    """
    디버그 로그 출력
    """
    logger.debug(message)
