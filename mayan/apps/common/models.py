import uuid


def upload_to(instance, filename):
    return 'shared-file-{}'.format(
        uuid.uuid4().hex
    )
