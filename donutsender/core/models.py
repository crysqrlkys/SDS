from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import DO_NOTHING
from django.utils.translation import gettext as _

from donutsender.core.helpers.base_model import BaseModel
from donutsender.core.helpers.singleton_model import Singleton


class User(AbstractUser, BaseModel):
    username = models.CharField(max_length=20, unique=True, validators=[UnicodeUsernameValidator])
    email = models.EmailField(_('email address'), unique=True)

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # in payment page currency
    balance = models.DecimalField(default=0, decimal_places=2, max_digits=12,
                                  validators=[MinValueValidator(Decimal(0))])

    last_withdraw = models.DateTimeField(auto_now_add=True, null=True)
    auto_withdraw_is_enabled = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class PaymentPage(BaseModel):
    user = models.OneToOneField('User', on_delete=DO_NOTHING)
    background_image = models.ImageField(upload_to='background_images/', blank=True, null=True)
    preferable_currency = models.CharField(max_length=3, default='USD')
    minimum_donate_sum = models.DecimalField(default=Decimal(0.1), decimal_places=2, max_digits=12,
                                             validators=[MinValueValidator(Decimal(0.1))])
    bio = models.CharField(max_length=1000, default='Write a message to your donators :)')
    button_text = models.CharField(max_length=50, default='Send')
    message_max_length = models.PositiveIntegerField(default=300, validators=[MaxValueValidator(1000)])

    def __str__(self):
        return f'{self.user.username}\'s payment page'


class Notifications(BaseModel):
    user = models.OneToOneField('User', on_delete=DO_NOTHING)
    email_is_enabled = models.BooleanField(default=True)
    pop_up_is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'notifications'

    def __str__(self):
        return f'Notification settings for: {self.user.username}'


class Payment(BaseModel):
    from_name = models.CharField(max_length=20, default='Anonymous', help_text='Required. 20 characters or fewer.')
    from_user = models.ForeignKey('User', related_name='payments_from_me', blank=True, null=True, on_delete=DO_NOTHING)
    to_user = models.ForeignKey('User', related_name='payments_to_me', on_delete=DO_NOTHING)
    message = models.CharField(max_length=300)
    money = models.DecimalField(default=Decimal(0.1), decimal_places=2, max_digits=12,
                                validators=[MinValueValidator(Decimal(0.1))])
    currency = models.CharField(max_length=3, default='USD')

    REQUIRED_FIELDS = ['from_name', 'to_user', 'currency']

    def __str__(self):
        return f'{self.from_name} donated {self.money} to {self.to_user.username}'


class Withdrawal(BaseModel):
    # in USD
    money = models.DecimalField(default=Decimal(5), decimal_places=2, max_digits=12,
                                validators=[MinValueValidator(Decimal(5))])
    method = models.CharField(default='card', max_length=20)
    # card number, phone numbers, etc.
    additional_info = models.CharField(max_length=100)
    user = models.ForeignKey('User', related_name='withdrawals', on_delete=DO_NOTHING)

    def __str__(self):
        return f'{self.user.username} withdrawn {self.money} by {self.method}'


class CashRegister(Singleton):
    # in USD
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=12)

    class Meta:
        # because it's singleton
        verbose_name_plural = 'cash register'

    def __str__(self):
        return f'Current sum: {self.amount}'
