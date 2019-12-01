from django.contrib.auth import get_user_model
from rest_framework import viewsets

from donutsender.core.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
