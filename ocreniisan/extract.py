import re
from . import store_dict

class Extract:
    regex_dict = {
        'date': r'[12]\d{3}[/\-年 ](0?[1-9]|1[0-2])[/\-月 ]([12][0-9]|3[01]|0?[0-9])日?',
        'total': r'合計.*[¥\*][ \d,.]+'
    }
    response = {}

    def __init__(self, texts):
        self.texts = texts
        self.extract_info()

    def extract_info(self):
        # 店舗名、日付、合計金額を抜き取り
        for text in self.texts:
            if not 'store' in self.response or self.response['store'] is None:
                self.response['store'] = self.store_name(text)

            for key, val in self.regex_dict.items():
                search = re.search(val, text)
                if search:
                    if key == 'date' and not 'date' in self.response:
                        self.response['date'] = self.payment_date(search.group())
                    elif key == 'total' and not 'total' in self.response:
                        self.response['total'] = self.total_amount(search.group())

        # サブカテゴリを入れておく
        self.response['sub_category'] = store_dict.STORE_DICT[self.response['store']]

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
