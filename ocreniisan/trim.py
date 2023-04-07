import cv2
import math
import numpy as np
import os
import sys
import re


"""
https://yrarchi.net/receipt_ocr/
https://yrarchi.net/rectangle_detection_detail2/#idea4
https://github.com/yrarchi/household_accounts
"""


class GetReceiptContours:
    def __init__(self, input_path):
        self.save_dir = os.path.join(os.path.dirname(__file__), 'images')
        if not os.path.isdir(self.save_dir):
            os.mkdir(self.save_dir)

        self.input_file = cv2.imread(input_path)
        self.input_filename = os.path.splitext(os.path.basename(input_path))[0]
        self.height, self.width, _ = self.input_file.shape
        self.img_size = self.height * self.width
        self.binary_img = self.binarize()
        self.contours = self.find_contours()
        self.approx_contours = self.approximate_contours()
        self.rectangle_contours = self.limited_to_rectangles()
        # self.draw_contours()

    def binarize(self):
        """
        画像を2値化する
        """
        # グレースケールに変換
        gray_img = cv2.cvtColor(self.input_file, cv2.COLOR_BGR2GRAY)
        # 適応的閾値処理
        binary_img = cv2.adaptiveThreshold(
            gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 255, 2
        )
        # ガウシアンフィルタで画像の平滑化
        size = (3, 3)
        blur = cv2.GaussianBlur(binary_img, size, 0)
        # 大津の手法を使った画像の２値化
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # 白黒反転
        th = cv2.bitwise_not(th)
        # 大津の手法を使った画像の２値化
        _, th = cv2.threshold(th, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # 白黒反転で元に戻す
        th = cv2.bitwise_not(th)
        return th

    def noise_reduction(self, img):
        """
        ノイズ処理(中央値フィルタ)を行う
        """
        median = cv2.medianBlur(img, 9)
        return median

    def find_contours(self):
        """
        輪郭の一覧を得る
        """
        # 輪郭取得
        contours, _ = cv2.findContours(self.binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # 面積が大きい順に並べ替える。
        contours = list(contours)
        contours.sort(key=cv2.contourArea, reverse=True)

        # copy_input_file = self.input_file.copy()
        # draw_contours_file = cv2.drawContours(
        #     copy_input_file, contours, -1, (0, 0, 255, 255), 10
        # )

        # cv2.imwrite(
        #     '{}/write_all_contours_{}.png'.format(
        #         self.save_dir, self.input_filename
        #     ),
        #     draw_contours_file,
        # )
        return contours

    def approximate_contours(self):
        """
        輪郭を条件で絞り込んで矩形のみにする
        """
        approx_contours = []
        for i, cnt in enumerate(self.contours):
            arclen = cv2.arcLength(cnt, True)
            area = cv2.contourArea(cnt)
            if arclen != 0 and self.img_size * 0.02 < area < self.img_size * 0.9:
                approx_contour = cv2.approxPolyDP(
                    cnt, epsilon=0.01 * arclen, closed=True
                )
                approx_contours.append(approx_contour)
        return approx_contours

    def limited_to_rectangles(self):
        def get_max_abs_cosine(contour):
            cos_list = []
            for i in range(4):
                points = [contour[i], contour[(i + 1) % 4], contour[(i + 3) % 4]]
                vec_1 = points[1] - points[0]
                vec_2 = points[2] - points[0]
                norm_1 = np.linalg.norm(vec_1)
                norm_2 = np.linalg.norm(vec_2)
                inner_product = np.inner(vec_1, vec_2)
                cos = inner_product / (norm_1 * norm_2)
                cos_list.append(cos)
            return max(list(map(abs, cos_list)))

        rectangle_contours = []
        contour = self.approx_contours[0]
        if len(contour) == 4:  # 頂点が4点の輪郭のみにする
            max_abs_cos = get_max_abs_cosine(contour)
            if max_abs_cos < math.cos(math.radians(80)):  # なす角が80°~100°のみにする
                rectangle_contours.append(contour)

        return rectangle_contours

    def draw_contours(self):
        """
        輪郭を画像に書き込む
        """
        if len(self.rectangle_contours) == 0:
            sys.exit('画像からレシートの外枠を検知できなかったので終了します')
        copy_input_file = self.input_file.copy()
        draw_contours_file = cv2.drawContours(
            copy_input_file, self.rectangle_contours, -1, (0, 0, 255, 255), 10
        )
        cv2.imwrite(
            '{}/write_contours_{}.jpg'.format(self.save_dir, self.input_filename),
            draw_contours_file,
        )


class GetEachReceiptImg(GetReceiptContours):
    def __init__(self, input_path):
        super().__init__(input_path)
        for i in range(len(self.rectangle_contours)):
            receipt_no = i
            self.sorted_corner_list = self.get_sorted_corner_list(receipt_no)
            self.width, self.height = self.get_length_receipt()
            # self.projective_transformation(receipt_no)

    def get_sorted_corner_list(self, receipt_no):
        corner_list = [self.rectangle_contours[receipt_no][i][0] for i in range(4)]
        corner_x = list(map(lambda x: x[0], corner_list))
        corner_y = list(map(lambda x: x[1], corner_list))

        west_1, west_2 = (
            corner_x.index(sorted(corner_x)[0]),
            corner_x.index(sorted(corner_x)[1]),
        )  # 左側2点のインデックス
        if west_1 == west_2:
            west_1, west_2 = [
                i for i, x in enumerate(corner_x) if x == sorted(corner_x)[0]
            ]
        north_west = (
            west_1 if corner_y[west_1] > corner_y[west_2] else west_2
        )  # 左上の点のインデックス
        south_west = west_2 if west_1 == north_west else west_1

        east_1, east_2 = [i for i in range(len(corner_x)) if i not in [west_1, west_2]]
        north_east = east_1 if corner_y[east_1] > corner_y[east_2] else east_2
        south_east = east_2 if east_1 == north_east else east_1

        sorted_corner_list = [
            corner_list[i] for i in [north_west, south_west, south_east, north_east]
        ]  # 左上から反時計回り
        return sorted_corner_list

    def get_length_receipt(self):
        width = np.linalg.norm(self.sorted_corner_list[0] - self.sorted_corner_list[3])
        height = np.linalg.norm(self.sorted_corner_list[0] - self.sorted_corner_list[2])
        return width, height

    def projective_transformation(self, receipt_no=0):
        pts_before = np.float32(self.sorted_corner_list)
        pts_after = np.float32(
            [[0, self.height], [0, 0], [self.width, 0], [self.width, self.height]]
        )
        M = cv2.getPerspectiveTransform(pts_before, pts_after)
        dst = cv2.warpPerspective(
            self.input_file, M, (int(self.width), int(self.height))
        )

        image_path = '{}/{}_{}_trimmed.jpg'.format(
            self.save_dir, self.input_filename, receipt_no
        )
        # 画像を圧縮して保存
        cv2.imwrite(image_path, dst, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        return image_path


def get_input_path_list(relative_path, extension):
    current_path = os.path.dirname(__file__)
    input_filename_list = os.listdir(os.path.join(current_path, relative_path))
    filename = r'\.({}|{})$'.format(extension, extension.upper())
    input_filename_extension_list = [
        f for f in input_filename_list if re.search(filename, f)
    ]
    if len(input_filename_extension_list) == 0:
        sys.exit('{}ファイルがないため処理を終了します'.format(extension))
    input_path_list = list(
        map(
            lambda x: os.path.join(current_path, relative_path, x),
            input_filename_extension_list,
        )
    )
    return input_path_list


def main(input_path):
    print('処理中...')
    GetReceiptContours(input_path)
    geri = GetEachReceiptImg(input_path)
    trimmed_image_path = geri.projective_transformation()
    return trimmed_image_path


# if __name__ == "__main__":
#     input_path = ''
#     main(input_path)
