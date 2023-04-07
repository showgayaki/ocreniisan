from enum import Enum
import io

from google.cloud import vision
from PIL import Image, ImageDraw


"""
https://cloud.google.com/vision/docs/fulltext-annotations?hl=ja
https://ossyaritoori.hatenablog.com/entry/2022/08/06/%E3%82%B9%E3%82%AD%E3%83%A3%E3%83%B3%E3%81%97%E3%81%9F%E3%83%AC%E3%82%B7%E3%83%BC%E3%83%88%E3%82%92Google_Vision_API%E3%82%92%E4%BD%BF%E3%81%A3%E3%81%A6%E8%87%AA%E5%89%8D%E3%81%A7OCR%E3%81%97
"""


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def draw_boxes(image, lines, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for line in lines:
        draw.polygon(
            [
                # top left
                line[0][-1].vertices[0].x,
                line[0][-1].vertices[0].y,
                # top right
                line[-1][-1].vertices[1].x,
                line[-1][-1].vertices[1].y,
                # bottom right
                line[-1][-1].vertices[2].x,
                line[-1][-1].vertices[2].y,
                # bottom left
                line[0][-1].vertices[3].x,
                line[0][-1].vertices[3].y,
            ],
            None,
            color,
        )
    return image


def get_sorted_lines(image_file, threshold=20):
    """Boundingboxの左上の位置を参考に行ごとの文章にParseする

    Args:
        response (_type_): VisionのOCR結果のObject
        threshold (int, optional): 同じ列だと判定するしきい値

    Returns:
        lines: list of [x, y, text, word.boundingbox]
    """
    with io.open(image_file, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    client = vision.ImageAnnotatorClient()
    response = client.document_text_detection(image=image)
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


def render_doc_text(filein, fileout):
    lines = get_sorted_lines(filein)
    image = Image.open(filein)

    draw_boxes(image, lines, "green")
    if fileout != 0:
        image.save(fileout)
    else:
        image.show()

    return lines
