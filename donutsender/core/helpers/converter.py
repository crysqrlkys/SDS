import requests
import json


class CurrencyConverter:

    def __init__(self):
        pass

    def convert(self, money, from_cur, to_cur):
        params = (
            ('to', from_cur.upper()),
            ('from', to_cur.upper()),
            ('amount', money),
        )
        response = requests.get('https://xecdapi.xe.com/v1/convert_to.json/', params=params,
                                auth=('somekindofacompany251085016', '3ohjgqr834m76i4vd92g14sqjf'))
        data = response.json()
        return data['from'][0]['mid']
