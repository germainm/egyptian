from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import BinaryDependency, PythonDependency
from mayan.apps.dependencies.environments import (
    environment_development, environment_production
)

from .literals import DEFAULT_TX_PATH

BinaryDependency(
    environments=(environment_development,), help_text=_(
        message='Transifex Client'
    ), label=_(message='Transifex Client'), module=__name__, name='tx',
    path=DEFAULT_TX_PATH
)

PythonDependency(
    environments=(environment_production,),
    legal_text='''
        Copyright (c) 2003-2005 Stuart Bishop <stuart@stuartbishop.net>

        Permission is hereby granted, free of charge, to any person obtaining a
        copy of this software and associated documentation files (the "Software"),
        to deal in the Software without restriction, including without limitation
        the rights to use, copy, modify, merge, publish, distribute, sublicense,
        and/or sell copies of the Software, and to permit persons to whom the
        Software is furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in
        all copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
        THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
        FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
        DEALINGS IN THE SOFTWARE.
    ''', module=__name__, name='pytz', version_string='==2026.2'
)
