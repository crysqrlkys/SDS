from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'url', 'username', 'email', 'avatar', 'password')
        extra_kwargrs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
        }


class LoginUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email')
