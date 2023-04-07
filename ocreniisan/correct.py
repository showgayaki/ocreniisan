from statistics import mean
import math
from pathlib import Path
import cv2


class Correct:
    def __init__(self, lines):
        self.lines = lines
        self.angle = self.rotation_degree()

    def rotation_degree(self):
        """
        行ごとの左上の(x, y)座標、右上の(x, y)座標の平均値から、画像の傾きを求める
        """
        left_x = []
        left_y = []
        right_x = []
        right_y = []

        for line in self.lines:
            left_x.append(line[0][-1].vertices[0].x)
            left_y.append(line[0][-1].vertices[0].y)
            right_x.append(line[-1][-1].vertices[0].x)
            right_y.append(line[-1][-1].vertices[0].y)

        left_x_mean = int(mean(left_x))
        left_y_mean = int(mean(left_y))
        right_x_mean = int(mean(right_x))
        right_y_mean = int(mean(right_y))

        x = right_x_mean - left_x_mean
        y = right_y_mean - left_y_mean
        return math.degrees(math.atan2(y, x))

    def rotate_image(self, image_path):
        suffix = Path(image_path).suffix
        image = cv2.imread(image_path)
        # 画像サイズ(横, 縦)から中心座標を求める
        size = tuple([image.shape[1], image.shape[0]])
        center = tuple([size[0] // 2, size[1] // 2])

        # 回転の変換行列を求める(画像の中心, 回転角度, 拡大率)
        mat = cv2.getRotationMatrix2D(center, self.angle, scale=1.0)
        # アフィン変換(画像, 変換行列, 出力サイズ, 補完アルゴリズム)
        rotated_image = cv2.warpAffine(image, mat, size, flags=cv2.INTER_CUBIC)

        rotated_image_path = image_path.replace(suffix, f'_rotated{suffix}')
        cv2.imwrite(rotated_image_path, rotated_image)
        return rotated_image_path
