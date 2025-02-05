import re
import math
from app.core.store_dict import STORE_DICT


class Extract:
    def __init__(self) -> None:
        pass

    def receipt_detail(self, lines: list) -> dict:
        distance_threshold = 30  # 商品名と金額の距離の閾値(これ以上離れていたら金額とみなす)
        response = {}
        line_text = ''
        last_line_text = ''
        word = ''
        distance_item_and_amount = 0
        is_items_area = False
        item_amount_lines = []
        date_line_index = 9999  # テキトーな大きい数字を入れておく

        for line_index in range(len(lines)):
            last_line_text = line_text
            line_text = ''
            # 行のwordごとの処理
            for word_index in range(len(lines[line_index])):
                # wordオブジェクトの[2]がテキスト
                word = lines[line_index][word_index][2]

                # 1個前のword(商品名)の右端と今回のword(金額)の左端の距離が、ある程度離れて記載されている
                if word_index > 0:
                    distance_item_and_amount = lines[line_index][word_index][-1].vertices[0].x - lines[line_index][word_index - 1][-1].vertices[1].x

                if distance_item_and_amount > distance_threshold:
                    # 小計or合計行はフォントが大きい場合があるので「,」(「.」に誤検知)と数字との間が空いて、別のwordとして認識されることがある
                    # 「小計」も「小」と「計」が別のwordとして認識されることがある
                    # そのため直前の文字が「.」「,」の場合と、今回のwordが「計」の場合は、line_textに連結する
                    # 「1, 000」 → 「1,000」
                    # 「小 計」 → 「小計」
                    if line_text[-1] == ',' or line_text[-1] == '.' or word == '計':
                        line_text += word
                    else:
                        line_text = '{}_{}'.format(line_text, word)
                        distance_item_and_amount = 0
                        # まいばすけっと対策：商品金額のあとに「A」という文字列が付いていた
                        # そのため、行の最終単語が数字でない場合は行をbreakする
                        if is_items_area and (word_index == len(lines[line_index]) - 1) and (self.amount_str_to_int(word) == 0):
                            line_text = '_'.join(line_text.split('_')[:-1])
                            break
                else:
                    line_text += word

            # 商品ごとの金額記載エリアに入ったかの検証
            line_text = line_text.replace('¥', '')
            line_text_splited = line_text.split('_')
            # 時間の記載箇所に数字が含まれているため、日付行より下の行から検証を開始する
            if line_index > date_line_index:
                if not is_items_area and len(line_text_splited) > 1:
                    item_amount = self.amount_str_to_int(line_text_splited[-1])
                    if item_amount:
                        is_items_area = True
                        # ------
                        # 商品名
                        # 個数✖️単価 合計
                        # ------
                        # となっているレシートの
                        # 商品一覧の最初の行に、複数購入のものが来た場合用の処理
                        # 前の行をappendしておく(*1)
                        if len(item_amount_lines) == 0:
                            item_amount_lines.append(last_line_text)

            # 店舗名を抜き取り
            if 'store' not in response or response['store'] is None:
                response['store'] = self.store_name(line_text)
            else:
                # 店名が入ったらサブカテゴリを入れておく
                response['subcategory'] = STORE_DICT[response['store']]

            # 日付を抜き取り
            payment_date = self.payment_date(line_text)
            if payment_date:
                response['date'] = payment_date
                date_line_index = line_index

            # 小計を抜き取り
            if '小計' in line_text:
                # 小計が記載されていたら、商品詳細エリア終了
                is_items_area = False
                date_line_index = 9999
                if 'subtotal' not in response:
                    response['subtotal'] = self.amount_str_to_int(line_text_splited[-1])

            if '合計' in line_text:
                # 小計がないレシートもあるようなので、ここでも初期化
                is_items_area = False
                date_line_index = 9999

                response['total'] = self.amount_str_to_int(line_text_splited[-1])

                # 小計がないレシートはおそらく税込表示なので、小計と税合計はnullにしておく
                if 'subtotal' not in response:
                    response['subtotal'] = None
            elif is_items_area:
                if '割引' in line_text and '金額' in line_text:
                    continue
                elif '小計' not in line_text:
                    item_amount_lines.append(line_text)

            # 合計が入ったら以降の行は見ません
            if 'total' in response:
                break

        items_list = self.items_amount(item_amount_lines)
        response['items'] = items_list

        # with open('key/file.json', 'w') as f:
        #     import json
        #     json.dump(response, f, indent=4, ensure_ascii=False)

        print(response)
        return response

    def items_amount(self, amount_lines):
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
            # 金額の記載があれば「商品名_1,000」の形で来るので、「_」でsplitできる
            item_and_amount_splited = line.split('_')
            amount = self.amount_str_to_int(item_and_amount_splited[-1])

            # 金額が取れていればアンダースコア前までがitem_name
            # 金額が取れていなければ、商品名中のアンダースコアなので、lineがitem_name
            if len(item_and_amount_splited) > 1 and amount != 0:
                item_name = ''.join(item_and_amount_splited[:-1])
            else:
                item_name = line

            # 個数✖️単価の記載になっているか検証
            item_count_and_amount = re.findall(r'\d+', item_name)
            item_count_and_amount = [int(i) for i in item_count_and_amount]

            if amount > 0:
                # 今回の行の金額と個数✖️単価が等しければ、前の行には金額の記載がないはず
                # item_nameを結合して、すでにappendした分は削除(pop)
                if amount == math.prod(item_count_and_amount):
                    item_name = '{} {}'.format(items_amount_list[-1]['name'], item_name)
                    items_amount_list.pop()
            else:
                # 前の行の金額と今回の行の個数✖️単価が等しければ、前の行には金額が書かれているはず
                # item_nameを結合して、すでにappendした分は削除(pop)
                if len(items_amount_list) > 0 and items_amount_list[-1]['amount'] == math.prod(item_count_and_amount):
                    item_name = '{} {}'.format(items_amount_list[-1]['name'], item_name)
                    amount = items_amount_list[-1]['amount']
                    items_amount_list.pop()
                elif len(items_amount_list) == 0:
                    # (*1)の場合の最初の処理(担当者記載行を想定)
                    # 金額部分はすべて0でappendしておく
                    items_amount_list.append({
                        'name': item_name,
                        'amount': 0,
                    })
                    continue

            if item_name:
                # 担当者記載行は削除
                if (len(items_amount_list) > 0
                        and items_amount_list[-1]['amount'] == 0):
                    items_amount_list.pop()

                items_amount_list.append({
                    'name': item_name,
                    'amount': amount,
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
        search = re.search(REGEX, text.replace('_', ''))
        if search:
            p_date = search.group().translate(str.maketrans({'年': '-', '月': '-', '日': None, '/': '-'}))
        return p_date

    def store_name(self, text):
        for key in STORE_DICT.keys():
            if key in text:
                return key
