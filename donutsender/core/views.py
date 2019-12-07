from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from donutsender.core.models import Payment, PaymentPage
from donutsender.core.serializers import UserSerializer, PaymentSerializer, PaymentPageSerializer
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
    action_permissions = {
        IsAdminOrSelf: ['create'],
        IsAdminUser: ['list'],
        AllowAny: ['retrieve']
    }


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

    def _validate_over_payment_page(self):
        pass

    def create(self, request, *args, **kwargs):
        sender = request.data.get('from_user')
        if sender and request.user.id != sender:
            raise PermissionDenied

        # validate

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
