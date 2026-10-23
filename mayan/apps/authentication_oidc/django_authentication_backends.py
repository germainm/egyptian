from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class DjangoAuthenticationBackendOIDC(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super().create_user(claims=claims)

        user._event_ignore = True

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save(
            update_fields=('first_name', 'last_name')
        )

        return user

    def get_or_create_user(self, access_token, id_token, payload):
        user = super().get_or_create_user(
            access_token=access_token, id_token=id_token, payload=payload
        )

        if user and self.user_can_authenticate(user=user):
            return user

        return None

    def get_user(self, user_id):
        user = super().get_user(user_id=user_id)

        if user and self.user_can_authenticate(user=user):
            return user

        return None

    def update_user(self, user, claims):
        user = super().update_user(user=user, claims=claims)

        user._event_ignore = True

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save(
            update_fields=('first_name', 'last_name')
        )

        return user
