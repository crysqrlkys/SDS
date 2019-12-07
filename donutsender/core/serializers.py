from rest_framework import serializers

from donutsender.core.models import User, CashRegister, Payment, PaymentPage


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = (
            'username',
            'email',
            'avatar',
            'balance',
            'password'
        )

        extra_kwargs = {
            'password': {'write_only': True},
            'balance': {'read_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def save(self, request):
        data = request.data
        if self.instance:
            self.instance = self.update(instance=self.instance, **data)
        else:
            user_ser = UserSerializer(data=data)
            user_ser.is_valid()
            self.instance = self.create(user_ser.validated_data)
        return self.instance


class PaymentPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPage
        fields = (
            'user',
            'background_image',
            'preferable_currency',
            'minimum_donate_sum',
            'bio',
            'button_text',
            'message_max_length'
        )

        extra_kwargs = {
            'user': {'read_only': True}
        }


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('from_user', 'from_name', 'to_user', 'message', 'money')


class CashRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashRegister
        fields = ('amount',)
