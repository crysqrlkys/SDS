from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import *
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import *
from rest_framework import status

from donutsender.core.helpers.commission_handler import CommissionHandler
from donutsender.core.helpers.converter import CurrencyConverter
from donutsender.core.helpers.send_email import send_withdrawal_notification_email, send_donation_notification_email
from donutsender.core.models import Payment, PaymentPage, Withdrawal, Settings, User
from donutsender.core.serializers import UserSerializer, PaymentSerializer, PaymentPageSerializer, WithdrawalSerializer, \
    SettingsSerializer
from donutsender.core.helpers.action_based_permissions import ActionBasedPermission
from donutsender.core.helpers.custom_permissions import IsSenderOrReceiverOrAdmin, IsAdminOrSelf, IsAdminOrOwner


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        IsAdminOrSelf: ['retrieve', 'list'],
    }

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = self.filter_queryset(self.queryset)
        else:
            queryset = self.queryset.filter(id=self.request.user.id)
        return queryset


class PaymentPageViewSet(viewsets.ModelViewSet):
    queryset = PaymentPage.objects.all()
    serializer_class = PaymentPageSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        IsAuthenticated: ['create'],
        IsAdminUser: ['list', 'destroy'],
        AllowAny: ['retrieve'],
        IsAdminOrOwner: ['update', 'partial_update'],
    }

    def get_object(self):
        username = self.kwargs.get('pk')
        payment_page = get_user_model().objects.get(username=username).paymentpage
        self.check_object_permissions(self.request, payment_page)
        return payment_page

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.paymentpage:
            return Response(data={'error': 'Can\'t create two or more payment pages'}, status=status.HTTP_409_CONFLICT)
        super().create(request, *args, **kwargs)


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

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = self.filter_queryset(self.queryset)
        else:
            queryset = self.queryset.filter(
                Q(from_user_id=self.request.user.id) |
                Q(to_user_id=self.request.user.id)
            )
        return queryset

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
        sender = User.objects.filter(username=request.data.get('from_user')).first()
        if not sender:  # can be None or empty
            sender_id = None
        else:
            sender_id = sender.id
        if sender_id and request.user.id != sender_id:
            raise PermissionDenied

        receiver = User.objects.filter(username=request.data.get('to_user')).first()
        if not receiver:
            return Response({'error': 'Receiver not found'}, status=status.HTTP_404_NOT_FOUND)
        if not self._validate_over_payment_page(receiver.id, request.data):
            raise ValidationError

        data = request.data
        from_user = User.objects.filter(username=data.pop('from_user')).first()
        to_user = User.objects.filter(username=data.pop('to_user')).first()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, from_user=from_user, to_user=to_user)
        headers = self.get_success_headers(data)
        send_donation_notification_email(receiver, serializer.data)
        # ser_data = self.get_serializer_class()(instance).data
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, **kwargs):
        return Payment.objects.create(**kwargs, **serializer.validated_data)


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

    def create(self, request, *args, **kwargs):
        user = int(request.data.get('user'))

        if user != request.user.id:
            raise PermissionDenied

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        commission_handler = CommissionHandler(user)

        if not commission_handler.validate_over_currency(request.data):
            raise ValidationError

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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


class SettingsViewSet(viewsets.GenericViewSet,
                      ListModelMixin,
                      RetrieveModelMixin,
                      UpdateModelMixin,
                      CreateModelMixin):
    queryset = Settings.objects.all()
    serializer_class = SettingsSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        IsAdminUser: ['retrieve'],
        IsAdminOrOwner: ['update', 'partial_update', 'list']
    }

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = self.filter_queryset(self.queryset)
        else:
            queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def get_object(self):
        settings = self.kwargs.get('pk')
        instance = self.get_queryset().get(id=settings)
        self.check_object_permissions(self.request, instance)
        return instance
