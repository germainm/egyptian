from django.contrib.auth import get_user_model


class LoginAttemptBusinessLogicMixin:
    @staticmethod
    def get_user_for_username(username):
        if not username:
            return None

        User = get_user_model()

        return User.objects.filter(
            **{User.USERNAME_FIELD: username}
        ).first()
