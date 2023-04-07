import re
import math
from .store_dict import STORE_DICT


class Extract:
    def __init__(self, lines):
        self.lines = lines

    def extract_info(self):
        distance_threshold = 30  # 商品名と金額の距離の閾値(これ以上離れていたら金額とみなす)
        response = {}
        line_text = ''
        word = ''
        distance_item_and_amount = 0
        is_items_area = False
        item_amount_lines = []
        date_line_index = 9999  # テキトーな大きい数字を入れておく
        subtotal = 0

        for line_index in range(len(self.lines)):
            line_text = ''

            # 日付の下にレジ担当者の名前などが来ることがあるので、「date_line_index + 1」している
            # お店(レシート)によってはダメかも
            if line_index > date_line_index + 1:
                is_items_area = True

            # 行のwordごとの処理
            for word_index in range(len(self.lines[line_index])):
                # wordオブジェクトの[2]がテキスト
                word = self.lines[line_index][word_index][2]

                # 1個前のword(商品名)の右端と今回のword(金額)の左端の距離が、ある程度離れて記載されている
                if is_items_area or ('小計' in line_text) or ('合計' in line_text):
                    distance_item_and_amount = self.lines[line_index][word_index][-1].vertices[0].x - self.lines[line_index][word_index - 1][-1].vertices[1].x

                if distance_item_and_amount > distance_threshold:
                    # 小計or合計行はフォントが大きい場合があるので「,」(「.」に誤検知)と数字との間が空いて、別のwordとして認識されることがある
                    # 「小計」も「小」と「計」が別のwordとして認識されることがある
                    # そのため直前の文字が「.」「,」の場合と、今回のwordが「計」の場合は、line_textに連結する
                    # 「1, 000」 → 「1,000」
                    # 「小 計」 → 「小計」
                    if line_text[-1] == ',' or line_text[-1] == '.' or word == '計':
                        line_text += word
                    else:
                        line_text = line_text.replace(' ', '_')
                        line_text = '{} {}'.format(line_text, word)
                        distance_item_and_amount = 0
                else:
                    line_text += word

            # 店舗名を抜き取り
            if 'store' not in response or response['store'] is None:
                response['store'] = self.store_name(line_text)
            else:
                # 店名が入ったらサブカテゴリを入れておく
                response['sub_category'] = STORE_DICT[response['store']]

            # 日付を抜き取り
            payment_date = self.payment_date(line_text)
            if payment_date:
                response['date'] = payment_date
                date_line_index = line_index

            # 「小計 ¥1,000」が1行と認識されず、「¥1,000」が先に認識されてしまうことがあったので
            # 金額のみの行があれば、商品金額欄は終了とみなす
            if '小計' in line_text:
                subtotal = self.amount_str_to_int(word)

            if subtotal > 0:
                is_items_area = False
                date_line_index = 9999
                if 'subtotal' not in response:
                    response['subtotal'] = subtotal
                    subtotal = 0

            if is_items_area and '小計' not in line_text:
                item_amount_lines.append(line_text)

            if '合計' in line_text:
                total = self.amount_str_to_int(line_text.split(' ')[-1])
                response['tax_total'] = total - response['subtotal']
                response['total'] = total

            # 合計が入ったら以降の行は見ません
            if 'total' in response:
                break

        items_list = self.items_amount(item_amount_lines, response['subtotal'], response['tax_total'])
        response['items'] = items_list

        # with open('key/file.json', 'w') as f:
        #     import json
        #     json.dump(response, f, indent=4, ensure_ascii=False)

        return response

    def items_amount(self, amount_lines, subtotal, tax_total):
        """
        商品ごとの金額を取得する。
        下記を満たしていれば、商品の金額が書かれているはず。
        - 1個前のword(商品名)の右端と今回のword(金額)の左端の距離が、ある程度離れている
        - 「小計」より前に記載されている
        - 数字である
        """
        items_amount_list = []
        item_name = ''
        amount = 0

        for line in amount_lines:
            # 金額の記載があれば「商品名 1,000」の形で来るので、半角スペースでsplitできる
            item_and_amount_splited = line.split(' ')
            amount = self.amount_str_to_int(item_and_amount_splited[-1])

            # 金額が取れていればスペース前までがitem_name
            # 取れなければ商品名中のスペースなので、lineがitem_name
            if len(item_and_amount_splited) > 1 and amount > 0:
                item_name = ''.join(item_and_amount_splited[:-1])
            else:
                item_name = line

            # 個数✖️単価の記載になっているか検証
            item_count_and_amount = re.findall(r'\d+', item_name)
            item_count_and_amount = [int(i) for i in item_count_and_amount]

            if amount > 0:
                item_name = ''.join(item_and_amount_splited[:-1])
                # 今回の行の金額と個数✖️単価が等しければ、前の行には金額の記載がないはず
                # item_nameを結合して、すでにappendした分は削除(pop)
                if amount == math.prod(item_count_and_amount):
                    item_name = '{} {}'.format(items_amount_list[-1]['name'], item_name)
                    items_amount_list.pop()
            else:
                item_name = line
                # 前の行の金額と今回の行の個数✖️単価が等しければ、前の行には金額が書かれているはず
                # item_nameを結合して、すでにappendした分は削除(pop)
                if items_amount_list[-1]['amount'] == math.prod(item_count_and_amount):
                    item_name = '{} {}'.format(items_amount_list[-1]['name'], item_name)
                    amount = items_amount_list[-1]['amount']
                    items_amount_list.pop()

            if item_name:
                # 税額の処理
                # 軽減税率の考慮は無理なので、税総額を商品金額で按分する
                # テキトーに丸めただけ、数円のズレは諦める
                tax_per_item = round(tax_total * round(amount / subtotal, 2))
                amount_tax_in = amount + tax_per_item

                items_amount_list.append({
                    'name': item_name,
                    'amount': amount,
                    'tax': tax_per_item,
                    'amount_tax_in': amount_tax_in,
                })

        # with open('key/item_list.json', 'w') as f:
        #     import json
        #     json.dump(items_amount_list, f, indent=4, ensure_ascii=False)
        return items_amount_list

    def amount_str_to_int(self, text):
        # いらない文字削除。カンマがドットに検知されることもあるのでドットも入れている
        for char in ['¥', ',', '.', '※', '*', '%']:
            text = text.replace(char, '')

        # intにキャストできたら金額
        try:
            amount = int(text)
        except ValueError:
            amount = 0
        return amount

    def payment_date(self, text):
        REGEX = r'[12]\d{3}[/\-年 ](0?[1-9]|1[0-2])[/\-月 ]([12][0-9]|3[01]|0?[0-9])日?'
        p_date = None
        search = re.search(REGEX, text)
        if search:
            p_date = search.group().translate(str.maketrans({'年': '-', '月': '-', '日': None, '/': '-'}))
        return p_date

    def store_name(self, text):
        for key in STORE_DICT.keys():
            if key in text:
                return key
