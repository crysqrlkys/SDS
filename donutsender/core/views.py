from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from donutsender.core.helpers.converter import CurrencyConverter
from donutsender.core.models import Payment, PaymentPage, Withdrawal, CashRegister
from donutsender.core.serializers import UserSerializer, PaymentSerializer, PaymentPageSerializer, WithdrawalSerializer
from donutsender.core.helpers.action_based_permissions import ActionBasedPermission
from donutsender.core.helpers.custom_permissions import IsSenderOrReceiverOrAdmin, IsAdminOrSelf


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        IsAdminOrSelf: ['retrieve'],
        IsAdminUser: ['list']
    }


class PaymentPageViewSet(viewsets.ModelViewSet):
    queryset = PaymentPage.objects.all()
    serializer_class = PaymentPageSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        IsAdminOrSelf: ['create'],
        IsAdminUser: ['list'],
        AllowAny: ['retrieve']
    }

    def retrieve(self, request, *args, **kwargs):
        username = kwargs.get('pk')
        user = get_user_model().objects.get(username=username)

        payment_page = user.paymentpage

        serializer = self.get_serializer(payment_page)
        return Response(serializer.data)


class PaymentViewSet(viewsets.GenericViewSet,
                     CreateModelMixin,
                     ListModelMixin,
                     RetrieveModelMixin):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        AllowAny: ['create'],
        IsSenderOrReceiverOrAdmin: ['retrieve', 'list'],
    }

    def list(self, request, *args, **kwargs):
        if request.user.is_staff:
            queryset = self.filter_queryset(self.get_queryset())
        else:
            queryset = Payment.objects.filter(
                Q(from_user_id=request.user.id) |
                Q(to_user_id=request.user.id)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        request_user = request.user
        if request_user.is_staff:
            instance = self.get_object()
        else:
            pk = kwargs.get('pk')
            qs = Payment.objects.filter(pk=pk)
            instance = get_object_or_404(qs)

            if instance.from_user:
                if instance.from_user.id != request_user.id:
                    raise PermissionDenied

            if instance.to_user.id != request_user.id:
                raise PermissionDenied

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _add_to_balance(self, user, money):
        user.balance += money
        user.save()

    def _validate_over_payment_page(self, receiver, data):
        receivers_payment_page, _ = PaymentPage.objects.get_or_create(user_id=receiver)

        needed_currency = receivers_payment_page.preferable_currency
        request_currency = data.get('currency')
        money = Decimal(data.get('money'))
        if needed_currency != request_currency:
            converter = CurrencyConverter()

            money = converter.convert(money, request_currency, needed_currency)

        request_data = {
            'length': len(data.get('message')),
            'sum': money
        }

        validation_results = {
            'message_length': receivers_payment_page.message_max_length >= request_data['length'],
            'donate_sum': receivers_payment_page.minimum_donate_sum <= request_data['sum']
        }

        valid = all(list(validation_results.values()))

        if valid:
            self._add_to_balance(user=receivers_payment_page.user, money=money)
        return valid

    def create(self, request, *args, **kwargs):
        sender = request.data.get('from_user')
        if sender == '':
            sender = None
        else:
            sender = int(sender)

        if sender and request.user.id != sender:
            raise PermissionDenied

        receiver = request.data.get('to_user')
        if not self._validate_over_payment_page(receiver, request.data):
            raise ValidationError

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class WithdrawalViewSet(viewsets.GenericViewSet,
                        CreateModelMixin,
                        ListModelMixin,
                        RetrieveModelMixin):
    queryset = Withdrawal.objects.all()
    serializer_class = WithdrawalSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        IsAuthenticated: ['create'],
        IsAdminOrSelf: ['retrieve', 'list'],
    }

    def _commission_charge(self, money, old_money, user):
        percent = Decimal(0.05)
        cash_register = CashRegister.load()
        cash_register.amount += money * percent
        cash_register.save()

        user.balance -= old_money
        user.save()

    def _validate_over_currency(self, user, data):
        users_payment_page, _ = PaymentPage.objects.get_or_create(user_id=user)

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
            self._commission_charge(money, old_money=money_in_user_currency, user=users_payment_page.user)
            return True
        return False

    def create(self, request, *args, **kwargs):
        user = int(request.data.get('user'))

        if user != request.user.id:
            raise PermissionDenied

        if not self._validate_over_currency(user, request.data):
            raise ValidationError

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        if request.user.is_staff:
            queryset = self.filter_queryset(self.get_queryset())
        else:
            queryset = Withdrawal.objects.filter(user=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        request_user = request.user
        if request_user.is_staff:
            instance = self.get_object()
        else:
            pk = kwargs.get('pk')
            qs = Withdrawal.objects.filter(pk=pk)
            instance = get_object_or_404(qs)

            if instance.user.id != request_user.id:
                raise PermissionDenied

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
