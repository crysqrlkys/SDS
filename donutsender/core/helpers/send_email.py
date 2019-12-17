from django.core.mail import send_mail
from django.conf import settings

from donutsender.core.models import User


def send_withdrawal_notification_email(user, data):
    user = User.objects.get(pk=user)
    if user.settings.email_is_enabled:
        send_mail(
            subject='DonutSender withdrawal',
            message='',
            from_email=settings.EMAIL_HOST,
            recipient_list=[user.email],
            fail_silently=True
        )


def send_donation_notification_email(receiver, data):
    if receiver.settings.email_is_enabled:
        send_mail(
            subject='You have a new donation',
            message='',
            from_email=settings.EMAIL_HOST,
            recipient_list=[receiver.email],
            fail_silently=True
        )
