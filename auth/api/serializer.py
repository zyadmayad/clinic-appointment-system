from django.contrib.auth.models import User
from rest_framework import serializers

from auth.models import Users

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    password = serializers.CharField(write_only=True, source='user.password')
    role = serializers.ChoiceField(choices=Users.ROLE_CHOICES, default='patient')

    class Meta:
        model = Users
        fields = ['id', 'username', 'email', 'password', 'role']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = user_data.pop('password')

        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()

        profile = Users.objects.create(user=user, role='patient')
        return profile