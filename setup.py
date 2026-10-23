#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import mayan

PACKAGE_NAME = 'mayan-edms'
PACKAGE_DIR = 'mayan'

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


def fullsplit(path, result=None):
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


def find_packages(directory):
    packages, data_files = [], []
    root_dir = os.path.dirname(__file__)
    if root_dir != '':
        os.chdir(root_dir)

    for dirpath, dirnames, filenames in os.walk(directory):
        if not dirpath.startswith('mayan/media'):
            if os.path.basename(dirpath).startswith('.'):
                continue
            if '__init__.py' in filenames:
                packages.append(
                    '.'.join(
                        fullsplit(dirpath)
                    )
                )
            elif filenames:
                data_files.append(
                    [
                        dirpath, [
                            os.path.join(dirpath, filename) for filename in filenames
                        ]
                    ]
                )

    return packages


install_requires = """
CairoSVG==2.9.0
Markdown==3.10.2
Pillow==12.3.0
PyYAML==6.0.3
Whoosh==2.7.4
boto3==1.40.24
celery==5.6.3
dateparser==1.4.0
django==5.2.17
django-activity-stream==2.0.0
django-auth-ldap==5.3.0
django-axes[ipware]==8.3.1
django-celery-beat==2.9.0
django-cors-headers==4.9.0
django-formtools==2.5.1
django-model-utils==5.0.0
django-mptt==0.18.0
django-qsstats-magic==1.1.0
django-solo==2.5.1
django-storages==1.14.6
django-widget-tweaks==1.5.1
djangorestframework==3.17.2
djangorestframework-recursive==0.1.2
drf-spectacular==0.30.0
drf-spectacular-sidecar==2026.7.1
elasticsearch==9.4.0
esprima==4.0.1
extract-msg==0.55.0
furl==2.1.4
fusepy==3.0.1
gevent==26.4.0
google-cloud-storage==3.10.1
graphviz==0.21
greenlet==3.5.0
gunicorn==26.0.0
jsonschema==4.26.0
mozilla-django-oidc==5.0.2
nh3==0.3.6
node-semver==0.9.0
ollama==0.6.2
openai==2.53.0
pycountry==26.2.16
pycryptodome==3.23.0
pyotp==2.9.0
pypdf==6.16.1
python-dateutil==2.9.0.post0
pytz==2026.2
qrcode==8.2
requests==2.33.1
sentry-sdk==2.65.0
sh==2.2.6
tinycss2==1.5.1
whitenoise==6.12.0
""".split()

with open(file='README.rst') as file_object:
    readme = file_object.read()

setup(
    author='Roberto Rosario',
    author_email='roberto.rosario@mayan-edms.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Communications :: File Sharing'
    ],
    description=mayan.__description__,
    include_package_data=True,
    install_requires=install_requires,
    license='GPL-2.0-only',
    long_description=readme,
    long_description_content_type='text/x-rst',
    name=PACKAGE_NAME,
    packages=find_packages(PACKAGE_DIR),
    platforms=['any'],
    project_urls={
        'Documentation': 'https://docs.mayan-edms.com/',
        'Forum': 'https://forum.mayan-edms.com/',
        'Changelog': 'https://docs.mayan-edms.com/chapters/releases/index.html',
        'Bug Tracker': 'https://gitlab.com/mayan-edms/mayan-edms/-/issues',
        'Source Code': 'https://gitlab.com/mayan-edms/mayan-edms',
        'Support': 'https://www.mayan-edms.com/support/'
    },
    python_requires='>=3.9',
    scripts=['mayan/bin/mayan-edms.py'],
    url=mayan.__website__,
    version=mayan.__version__,
    zip_safe=False
)
