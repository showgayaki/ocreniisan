import re
from . import store_dict

class Extract:
    regex_dict = {
        'date': r'[12]\d{3}[/\-年 ](0?[1-9]|1[0-2])[/\-月 ]([12][0-9]|3[01]|0?[0-9])日?',
        'total': r'合計.*[¥\*][ \d,.]+'
    }

    def __init__(self, texts):
        self.texts = texts

    def extract_info(self):
        response = {}
        # 店舗名、日付、合計金額を抜き取り
        for text in self.texts:
            if not 'store' in response or response['store'] is None:
                response['store'] = self.store_name(text)

            for key, val in self.regex_dict.items():
                search = re.search(val, text)
                if search:
                    if key == 'date' and not 'date' in response:
                        response['date'] = self.payment_date(search.group())
                    elif key == 'total' and not 'total' in response:
                        response['total'] = self.total_amount(search.group())

        # サブカテゴリを入れておく
        response['sub_category'] = store_dict.STORE_DICT[response['store']]
        return response

    def payment_date(self, text):
        p_date = text.translate(str.maketrans({'年': '-', '月': '-', '日': None, '/': '-'}))
        return p_date

    def store_name(self, text):
        for key in store_dict.STORE_DICT.keys():
            if key in text:
                return key

    def total_amount(self, text):
        total_regex = r'[¥\*][ \d,.]+'
        search = re.search(total_regex, text)
        if search:
            total = search.group().translate(str.maketrans({'¥': None, ',': None, '.': None}))
            return int(total)
