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
    background_image = models.ImageField(upload_to='background_images/', blank=True, null=True)

    balance = models.DecimalField(default=0, decimal_places=2, max_digits=12,
                                  validators=[MinValueValidator(Decimal(0))])
    preferable_currency = models.CharField(max_length=3, default='BYN')
    minimum_donate_sum = models.DecimalField(default=1, decimal_places=2, max_digits=12,
                                             validators=[MinValueValidator(Decimal(0.1))])
    bio = models.CharField(max_length=1000, default='Write a message to your donators :)')
    button_text = models.CharField(max_length=50, default='Send')
    message_max_length = models.PositiveIntegerField(default=300, validators=[MaxValueValidator(1000)])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class Notifications(BaseModel):
    user = models.OneToOneField('User', on_delete=DO_NOTHING)
    email_is_enabled = models.BooleanField(default=True)
    pop_up_is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f'Notification settings for: {self.user.username}'


class Payment(BaseModel):
    from_name = models.CharField(max_length=20, default='Anonymous', help_text='Required. 20 characters or fewer.')
    from_user = models.ForeignKey('User', related_name='payments_from_me', blank=True, null=True, on_delete=DO_NOTHING)
    to_user = models.ForeignKey('User', related_name='payments_to_me', on_delete=DO_NOTHING)
    message = models.CharField(max_length=300)
    money = models.DecimalField(default=5, decimal_places=2, max_digits=12)

    REQUIRED_FIELDS = ['from_name', 'to_user']

    def __str__(self):
        return f'{self.from_name} donated {self.money} to {self.to_user.username}'


class CashRegister(Singleton):
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=12)

    def __str__(self):
        return f'Current sum: {self.amount}'
