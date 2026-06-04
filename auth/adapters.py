from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from auth.models import Users


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        email = user.email or sociallogin.account.extra_data.get("email", "")
        profile, _ = Users.objects.get_or_create(
            user=user,
            defaults={
                "role": "patient",
                "username": user.username,
                "email": email,
            },
        )

        profile.username = user.username
        profile.email = email
        profile.save(update_fields=["username", "email"])

        return user
