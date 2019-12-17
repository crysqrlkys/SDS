from datetime import datetime
from decimal import Decimal

import pytz

from donutsender.core.helpers.converter import CurrencyConverter
from donutsender.core.helpers.send_email import send_withdrawal_notification_email
from donutsender.core.models import CashRegister, PaymentPage, User


class CommissionHandler:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user = User.objects.get(id=user_id)
        self.percent = Decimal(0.05)

    def commission_charge(self, money, old_money):
        cash_register = CashRegister.load()
        cash_register.amount += money * self.percent
        cash_register.save()

        self.user.balance -= old_money * (1 - self.percent)
        self.user.last_withdraw = datetime.now().replace(tzinfo=pytz.utc)
        self.user.save()

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
            send_withdrawal_notification_email(users_payment_page, money_in_user_currency * (1 - self.percent))
            return True
        return False
