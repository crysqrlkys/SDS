from rest_framework import serializers

from donutsender.core.models import User, CashRegister, Payment, PaymentPage, Withdrawal, Settings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = (
            'id',
            'username',
            'email',
            'avatar',
            'balance',
            'password'
        )

        extra_kwargs = {
            'password': {'write_only': True},
            'balance': {'read_only': True},
            'id': {'read_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        settings = Settings.objects.create(user=user)
        settings.save()
        payment_page = PaymentPage.objects.create(user=user)
        payment_page.save()
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


class UserPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = (
            'username',
            'avatar',
        )
        extra_kwargs = {
            'avatar': {'read_only': True},
        }


class PaymentPageSerializer(serializers.ModelSerializer):
    user = UserPageSerializer(read_only=True)

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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            'id',
            'from_user',
            'from_name',
            'to_user',
            'to_name',
            'message',
            'money',
            'currency',
            'created_at'
        )
        extra_kwargs = {
            'from_user': {'required': False},
            'to_user': {'required': False},
            'to_name': {'required': False},
            'created_at': {'read_only': True}
        }


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = (
            'id',
            'money',
            'method',
            'additional_info',
            'user'
        )


class CashRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashRegister
        fields = ('amount',)


class SettingsSerializer(serializers.ModelSerializer):
    user = UserPageSerializer()

    class Meta:
        model = Settings
        fields = ('id', 'email_is_enabled', 'pop_up_is_enabled', 'auto_withdraw_is_enabled', 'user',)
        extra_kwargs = {
            'user': {'read_only': True},
            'id': {'read_only': True},
        }
