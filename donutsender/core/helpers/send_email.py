from django.core.mail import send_mail
from django.conf import settings

from donutsender.core.models import User


def send_withdrawal_notification_email(pp, money):
    if pp.user.settings.email_is_enabled:
        send_mail(
            subject='DonutSender withdrawal',
            message=f'You just withdraw {round(money,2)} {pp.preferable_currency}!',
            from_email=settings.EMAIL_HOST,
            recipient_list=[pp.user.email],
            fail_silently=True
        )


def send_donation_notification_email(receiver, data):
    if receiver.settings.email_is_enabled:
        from_user = data.get('from_name')
        money = data.get('money')
        currency = data.get('currency')
        message = data.get('message')
        send_mail(
            subject='You have a new donation',
            message=f'{from_user} just donated you {money} {currency}! It\'s said: {message}',
            from_email=settings.EMAIL_HOST,
            recipient_list=[receiver.email],
            fail_silently=True
        )
