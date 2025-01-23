from logging import getLogger
from pathlib import Path
from google.cloud import vision
import io

from app.core.config import ConfigManager
from app.utils.rotate import rotation_degree, rotate_image


"""
https://cloud.google.com/vision/docs/fulltext-annotations?hl=ja
https://ossyaritoori.hatenablog.com/entry/2022/08/06/%E3%82%B9%E3%82%AD%E3%83%A3%E3%83%B3%E3%81%97%E3%81%9F%E3%83%AC%E3%82%B7%E3%83%BC%E3%83%88%E3%82%92Google_Vision_API%E3%82%92%E4%BD%BF%E3%81%A3%E3%81%A6%E8%87%AA%E5%89%8D%E3%81%A7OCR%E3%81%97
"""


logger = getLogger('ocr')
config = ConfigManager().config


def exec_ocr(image_file_path: Path) -> list:
    # 文字列からレシートの傾きを求めるために、いったんOCR実行
    logger.info('Run OCR.')
    lines = _get_sorted_lines(image_file_path)

    # レシートの傾きを求めて、回転させた画像を保存
    rotation_angle = rotation_degree(lines)
    rotated_image_path = rotate_image(rotation_angle, image_file_path)
    # 回転させた画像で、再度OCR実行
    logger.info('Run OCR after rotation.')
    lines = _get_sorted_lines(rotated_image_path)

    return lines


def _get_sorted_lines(image_file: Path, threshold=20) -> list:
    """Boundingboxの左上の位置を参考に行ごとの文章にParseする

    Args:
        response (_type_): VisionのOCR結果のObject
        threshold (int, optional): 同じ列だと判定するしきい値

    Returns:
        lines: list of [x, y, text, word.boundingbox]
    """
    with io.open(str(image_file), "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    client = vision.ImageAnnotatorClient()
    response = client.document_text_detection(image=image)  # type: ignore
    document = response.full_text_annotation

    # テキスト抽出とソート
    bounds = []
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''
                    for symbol in word.symbols:
                        word_text += symbol.text
                    x = word.bounding_box.vertices[0].x
                    y = word.bounding_box.vertices[0].y
                    bounds.append([x, y, word_text, word.bounding_box])
    bounds.sort(key=lambda x: x[1])

    # 同じ高さのものをまとめる
    old_y = -1
    line = []
    lines = []
    for bound in bounds:
        x = bound[0]
        y = bound[1]
        if old_y == -1:
            old_y = y
        elif old_y - threshold <= y <= old_y + threshold:
            old_y = y
        else:
            old_y = -1
            line.sort(key=lambda x: x[0])
            lines.append(line)
            line = []
        line.append(bound)
    line.sort(key=lambda x: x[0])
    lines.append(line)

    return lines
