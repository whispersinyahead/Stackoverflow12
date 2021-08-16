from rest_framework import serializers

from account.models import CustomUser
from account.utils import send_activation_code


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    password_confirmation = serializers.CharField(min_length=8, required=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'password_confirmation')

    def validate(self, validated_data):
        password = validated_data.get('password')
        password_confirmation = validated_data.pop('password_confirmation')
        if password != password_confirmation:
            raise serializers.ValidationError('Passwords do not match')
        return validated_data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        send_activation_code(user.email, user.activation_code, status='register')
        return user


class CreateNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    activation_code = serializers.CharField(max_length=25, required=True)
    password = serializers.CharField(min_length=8, required=True)
    password_confirmation = serializers.CharField(min_length=8, required=True)

    def validated_email(self, email):
        if not CustomUser.objects.filter(email=email).exists():
            raise  serializers.ValidationError('Пользователь не найден.')
        return email

    def validated_activation_code(self, act_code):
        if not CustomUser.objects.filter(activation_code=act_code, is_active=False).exists():
            raise serializers.ValidationError('Неверный код активации.')
        return act_code

    def validate(self, validated_data):
        password = validated_data.get('password')
        password_confirmation = validated_data.pop('password_confirmation')
        if password != password_confirmation:
            raise serializers.ValidationError('Passwords do not match')
        return validated_data

    def save(self, **kwargs):
        data = self.validated_data
        email = data.get('email')
        activation_code = data.get('activation_code')
        password = data.get('password')
        try:
            user = CustomUser.objects.get(email=email, activation_code=activation_code, is_active=False)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')
        user.is_active = True
        user.activation_code = ''
        user.set_password(password)
        user.save()
        return user