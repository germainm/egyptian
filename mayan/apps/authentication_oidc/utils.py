import unicodedata
from urllib.parse import parse_qs, urlsplit

from .literals import (
    SESSION_KEY_RENEWAL_NEXT, SESSION_KEY_STATES, SESSION_KEY_UPSTREAM_NEXT,
    STATE_KEY_NEXT
)


def generate_username_from_email(email):
    return unicodedata.normalize('NFKC', email)[:150]


def store_authorization_destination(request, authorization_url, destination):
    session = getattr(request, 'session', None)

    if session is None:
        return False

    query = urlsplit(url=authorization_url).query
    state_list = parse_qs(qs=query).get('state', ())

    if len(state_list) != 1:
        return False

    state = state_list[0]
    state_dict = session.get(SESSION_KEY_STATES, {})

    if state not in state_dict:
        return False

    if STATE_KEY_NEXT in state_dict[state]:
        return False

    state_dict[state][STATE_KEY_NEXT] = destination

    session[SESSION_KEY_STATES] = state_dict

    session.pop(SESSION_KEY_RENEWAL_NEXT, None)
    session.pop(SESSION_KEY_UPSTREAM_NEXT, None)

    return True
