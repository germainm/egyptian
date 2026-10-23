from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models

from .settings import setting_favorite_count


class FavoriteDocumentManager(models.Manager):
    def get_by_natural_key(
        self, datetime_accessed, document_natural_key, user_natural_key
    ):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        User = get_user_model()
        try:
            document = Document.objects.get_by_natural_key(
                *document_natural_key
            )
        except Document.DoesNotExist:
            raise self.model.DoesNotExist
        else:
            try:
                user = User.objects.get_by_natural_key(*user_natural_key)
            except User.DoesNotExist:
                raise self.model.DoesNotExist

        return self.get(document__pk=document.pk, user__pk=user.pk)


class ValidFavoriteDocumentManager(models.Manager):
    def add_for_user(self, user, document):
        favorite_document, created = self.model.objects.get_or_create(
            user=user, document=document
        )

        queryset_favorites_to_delete = self.filter(
            user=user
        ).only('id').values_list('id', flat=True).order_by('-datetime_added')[
            setting_favorite_count.value:
        ]
        self.filter(pk__in=queryset_favorites_to_delete).delete()

        return favorite_document

    def get_for_user(self, user):
        FavoriteDocumentProxy = apps.get_model(
            app_label='document_favorites', model_name='FavoriteDocumentProxy'
        )

        if user.is_authenticated:
            return FavoriteDocumentProxy.valid.filter(favorites__user=user)
        else:
            return FavoriteDocumentProxy.valid.none()

    def get_queryset(self):
        return super().get_queryset().filter(
            document__in_trash=False
        )

    def remove_for_user(self, user, document):
        self.get(user=user, document=document).delete()


class ValidFavoriteDocumentProxyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            in_trash=False
        )
