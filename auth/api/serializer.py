from django.contrib.auth.models import Group, User
from rest_framework import serializers

ROLE_CHOICES = ['admin', 'doctor', 'patient', 'receptionist']


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    set_role = serializers.ChoiceField(
        choices=ROLE_CHOICES, write_only=True, required=False, default='patient'
    )
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'set_role']

    def get_role(self, obj):
        group = obj.groups.filter(name__in=ROLE_CHOICES).first()
        return group.name if group else None

    def create(self, validated_data):
        role = validated_data.pop('set_role', 'patient')
        password = validated_data.pop('password', None)

        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()

        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        return user

    def update(self, instance, validated_data):
        role = validated_data.pop('set_role', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        if role:
            instance.groups.remove(*instance.groups.filter(name__in=ROLE_CHOICES))
            group, _ = Group.objects.get_or_create(name=role)
            instance.groups.add(group)

        return instance


# Keep the old name as an alias so any existing imports still work.
RegisterSerializer = UserSerializer
