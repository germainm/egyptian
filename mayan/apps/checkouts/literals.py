from django.utils.translation import gettext_lazy as _

CHECKOUT_EXPIRATION_LOCK_EXPIRE = 50
CHECK_EXPIRED_CHECK_OUTS_INTERVAL = 60

STATE_CHECKED_IN = 'checkedin'
STATE_CHECKED_OUT = 'checkedout'

STATE_LABELS = {
    STATE_CHECKED_OUT: _(message='Checked out'),
    STATE_CHECKED_IN: _(message='Checked in/available'),
}
