from .events import event_user_logged_in, event_user_logged_out


def handler_user_logged_in(sender, user, request=None, **kwargs):
    event_user_logged_in.commit(actor=user, target=user)


def handler_user_logged_out(sender, **kwargs):
    event_user_logged_out.commit(
        actor=kwargs['user'], target=kwargs['user']
    )
