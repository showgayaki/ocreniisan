from fastapi import FastAPI, UploadFile
import shutil
from datetime import datetime
from pathlib import Path
import cv2
from . import trim, doctext
from .correct import Correct
from .extract import Extract


app = FastAPI(root_path='/ocreniisan', docs_url='/docs')


@app.post('/')
async def receipt_ocr(receiptImage: UploadFile, trimmed: bool = False):
    # 画像保存用ディレクトリがなかったら作成
    image_save_dir = Path(__file__).parent.joinpath('images').resolve()
    error_dir = image_save_dir.joinpath('error')
    if not image_save_dir.is_dir():
        image_save_dir.mkdir()
    if not error_dir.is_dir():
        error_dir.mkdir()

    # アップロードされた画像を保存
    dt_now = datetime.now()
    file_name = f'{dt_now.strftime("%Y%m%d-%H%M%S")}.jpg'
    original_image_path = str(Path(image_save_dir).joinpath(file_name).resolve())
    with open(original_image_path, 'wb+') as buffer:
        shutil.copyfileobj(receiptImage.file, buffer)

    # 画像を圧縮
    image = cv2.imread(original_image_path)
    cv2.imwrite(original_image_path, image, [int(cv2.IMWRITE_JPEG_QUALITY), 50])

    if trimmed:
        # トリミングされてたらオリジナル画像をそのまま渡す
        trimmed_image_path = original_image_path
    else:
        # 画像からレシート部分をトリミング
        try:
            trimmed_image_path = trim.main(original_image_path)
        except Exception as e:
            # エラー画像保存
            error_image_path = str(error_dir.joinpath(file_name.replace('.jpg', '_trim-error.jpg')))
            shutil.move(original_image_path, error_image_path)

            # エラー全文を返す
            import traceback
            t = traceback.format_exception_only(type(e), e)
            print(traceback.format_exc())
            return {
                'error': 'trim',
                'message': 'レシートを読み取れませんでした。\n写真を撮り直してください。',
                'detail': ''.join(t)
            }

    ocred_filename = Path(trimmed_image_path).name.replace('.jpg', '_ocred.jpg')
    ocred_image_path = Path(image_save_dir).joinpath(ocred_filename)

    # 文字列からレシートの傾きを求めるために、いったんOCR実行
    lines = doctext.render_doc_text(trimmed_image_path, ocred_image_path)
    # レシートの傾きを求めて、回転させた画像を保存
    correct = Correct(lines)
    rotated_image_path = correct.rotate_image(trimmed_image_path)
    # 回転させた画像で、再度OCR実行
    lines = doctext.render_doc_text(rotated_image_path, ocred_image_path)

    # 情報抽出
    ext = Extract(lines)
    try:
        response = ext.extract_info()
    except Exception as e:
        # エラー画像保存
        error_image_path = str(error_dir.joinpath(file_name.replace('.jpg', '_ocr-error.jpg')))
        shutil.move(original_image_path, error_image_path)

        # エラー全文を返す
        import traceback
        t = traceback.format_exception_only(type(e), e)
        print(traceback.format_exc())
        return {
            'error': 'extract',
            'message': '情報抽出中に何かおかしなことが起きました。',
            'detail': ''.join(t)
        }

    # 画像ファイル削除
    for f in image_save_dir.iterdir():
        if f.is_file():
            f.unlink()

    return response


@app.get(app.root_path + '/openapi.json')
def custom_swagger_ui_html():
    return app.openapi()
