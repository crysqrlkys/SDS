from datetime import datetime
from decimal import Decimal

import pytz

from donutsender.core.helpers.converter import CurrencyConverter
from donutsender.core.models import CashRegister, PaymentPage, User


class CommissionHandler:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user = User.objects.get(id=user_id)

    def commission_charge(self, money, old_money):
        percent = Decimal(0.05)
        cash_register = CashRegister.load()
        cash_register.amount += money * percent
        cash_register.save()

        self.user.balance -= old_money * (1 - percent)
        self.user.last_withdraw = datetime.now().replace(tzinfo=pytz.utc)
        self.user.user.save()

    def validate_over_currency(self, data):
        users_payment_page, _ = PaymentPage.objects.get_or_create(user_id=self.user_id)

        user_currency = users_payment_page.preferable_currency
        usd = 'USD'

        money = Decimal(data.get('money'))
        money_in_user_currency = money

        # same currency
        if money > users_payment_page.user.balance:
            return False

        if usd != user_currency:
            converter = CurrencyConverter()
            money = converter.convert(money, user_currency, usd)

        money_after_commission_charge = money - (money * Decimal(0.05))

        if money_after_commission_charge >= 5:
            self.commission_charge(money, old_money=money_in_user_currency)
            return True
        return False
