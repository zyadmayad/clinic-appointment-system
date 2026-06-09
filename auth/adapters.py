from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import Group


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        patient_group, _ = Group.objects.get_or_create(name='patient')
        user.groups.add(patient_group)

        return user
