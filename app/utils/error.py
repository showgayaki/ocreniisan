from logging import getLogger
from pathlib import Path
import traceback
import shutil

from app.core.config import ConfigManager


config = ConfigManager().config
logger = getLogger('ocr')


def save_error_image(error_type: str, image_path: Path, message: str, e: Exception) -> dict:
    file_name = Path(image_path).name
    suffix = Path(image_path).suffix
    # エラー画像保存
    error_image_path = config.ERROR_DIR.joinpath(file_name.replace(f'.{suffix}', f'_{error_type}-error.{suffix}'))
    shutil.move(str(image_path), str(error_image_path))
    logger.info(f'Moved error image: [{image_path}] to [{error_image_path}]')

    # エラー全文を返す
    t = traceback.format_exception_only(type(e), e)
    logger.error(traceback.format_exc())
    return {
        'error': error_type,
        'message': message,
        'detail': ''.join(t)
    }
