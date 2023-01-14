from fastapi import FastAPI, UploadFile
import shutil
from datetime import datetime
from pathlib import Path
from . import trim, doctext
from .extract import Extract


app = FastAPI(docs_url='/ocreniisan/docs')


@app.post('/ocreniisan')
async def receipt_ocr(receiptImage: UploadFile):
    # 画像保存用ディレクトリがなかったら作成
    image_save_dir = Path(__file__).parent.joinpath('images').resolve()
    if not image_save_dir.is_dir(): image_save_dir.mkdir()

    # アップロードされた画像を保存
    dt_now = datetime.now()
    file_name = f'{dt_now.strftime("%Y%m%d-%H%M%S")}.jpg'
    original_image_path = str(Path(image_save_dir).joinpath(file_name).resolve())
    with open(original_image_path, 'wb+') as buffer:
        shutil.copyfileobj(receiptImage.file, buffer)

    # 画像からレシート部分をトリミング
    try:
        trimmed_image_path = trim.main(original_image_path)
    except Exception as e:
        print(e)
        return {'error': 'レシートを読み取れませんでした。\n写真を撮り直してください。'}

    ocred_filename = Path(trimmed_image_path).name.replace('.png', '_ocred.png')
    ocred_image_path = Path(image_save_dir).joinpath(ocred_filename)
    # OCR実行
    texts = doctext.render_doc_text(trimmed_image_path, ocred_image_path)
    # 画像ファイル削除
    for f in image_save_dir.iterdir():
        f.unlink()

    # 情報抽出
    ext = Extract(texts)
    return ext.response
