from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, exceptions

from rest_framework import generics, mixins, views
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from donutsender.core.models import Payment
from donutsender.core.serializers import UserSerializer, PaymentSerializer
from tools.action_based_permissions import ActionBasedPermission
from tools.cystom_permissions import IsOwnerOrAdmin


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class PaymentViewSet(viewsets.GenericViewSet,
                     mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (ActionBasedPermission,)
    action_permissions = {
        AllowAny: ['create'],
        IsOwnerOrAdmin: ['retrieve', 'list'],
    }

    def create(self, request, *args, **kwargs):
        sender = request.data.get('from_user')
        if sender and request.user.id != sender:
            raise exceptions.PermissionDenied
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
