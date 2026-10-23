from django.apps import apps

from .exceptions import DocumentNotCheckedOut, NewDocumentFileNotAllowed


def hook_is_new_file_allowed(instance, kwargs=None):
    DocumentCheckout = apps.get_model(
        app_label='checkouts', model_name='DocumentCheckout'
    )

    document = kwargs.get('document', None)
    if not document:
        if not instance:
            return
        else:
            document = instance.document

    try:
        checkout_information = DocumentCheckout.objects.get_check_out_info(
            document=document
        )
    except DocumentNotCheckedOut:
        """Document is not checked out, do nothing"""
    else:
        if checkout_information.user != kwargs['user'] and checkout_information.block_new_file:
            raise NewDocumentFileNotAllowed
