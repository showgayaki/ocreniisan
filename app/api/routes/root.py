from logging import getLogger
from fastapi import APIRouter, UploadFile
from datetime import datetime
import shutil

from app.core.config import ConfigManager
from app.core.logger import load_looger
from app.services.ocr import exec_ocr
from app.services.trim import exec_trim
from app.services.extract import Extract
from app.utils.compress import comporess_file_size
from app.utils.error import save_error_image


load_looger()
logger = getLogger('ocr')

router = APIRouter()
config = ConfigManager().config


@router.post('/')
async def receipt_ocr(receiptImage: UploadFile, trimmed: bool = False) -> dict:
    # 画像保存用ディレクトリがなかったら作成
    if not config.IMAGE_SAVE_DIR.is_dir():
        logger.info('Create image save directory.')
        config.IMAGE_SAVE_DIR.mkdir()
    if not config.ERROR_DIR.is_dir():
        logger.info('Create error image directory.')
        config.ERROR_DIR.mkdir()

    # アップロードされた画像を保存
    dt_now = datetime.now()
    file_name = f'{dt_now.strftime("%Y%m%d-%H%M%S")}.jpg'
    original_image_path = config.IMAGE_SAVE_DIR.joinpath(file_name).resolve()
    with open(str(original_image_path), 'wb+') as buffer:
        logger.info(f'Save image: {original_image_path}')
        shutil.copyfileobj(receiptImage.file, buffer)

    # 画像を圧縮
    comporess_file_size(original_image_path)

    if trimmed:
        # トリミングされてたらオリジナル画像をそのまま渡す
        logger.info('Image is already trimmed.')
        trimmed_image_path = original_image_path
    else:
        logger.info('Trimming image.')
        # 画像からレシート部分をトリミング
        try:
            trimmed_image_path = exec_trim(str(original_image_path))
            logger.info(f'Trimmed image: {trimmed_image_path}')
        except Exception as e:
            logger.error('Failed to trim image.')
            # エラー画像保存
            error_message = save_error_image(
                'trim',
                original_image_path,
                'レシートを読み取れませんでした。\n写真を撮り直してください。',
                e
            )
            return error_message

    # OCR実行
    try:
        lines = exec_ocr(trimmed_image_path)
    except Exception as e:
        logger.error('Failed to run OCR.')
        # エラー画像保存
        error_message = save_error_image(
            'ocr',
            original_image_path,
            'OCR処理中に何かおかしなことが起きました。',
            e
        )
        return error_message

    # 情報抽出
    logger.info('Extract information.')
    extract = Extract()
    try:
        response = extract.receipt_detail(lines)
    except Exception as e:
        logger.error('Failed to extract information.')
        # エラー画像保存
        error_message = save_error_image(
            'extract',
            original_image_path,
            '情報抽出中に何かおかしなことが起きました。',
            e
        )
        return error_message

    # 画像ファイル削除
    logger.info('Delete image files.')
    for f in config.IMAGE_SAVE_DIR.iterdir():
        if f.is_file():
            logger.info(f'Delete: [{f}]')
            f.unlink()

    return response
