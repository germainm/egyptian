from django.utils.translation import gettext


class DocumentCheckoutError(Exception):
    pass


class DocumentNotCheckedOut(DocumentCheckoutError):
    def __str__(self):
        return gettext('Document not checked out.')


class DocumentAlreadyCheckedOut(DocumentCheckoutError):
    def __str__(self):
        return gettext(message='Document already checked out.')


class NewDocumentFileNotAllowed(DocumentCheckoutError):
    pass
