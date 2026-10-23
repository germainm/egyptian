#!/usr/bin/env python3

import doctest
import sys

from packaging.version import Version as PackageVersion


class Version:
    def __eq__(self, other):
        return self._version == other._version

    def __gt__(self, other):
        return self._version > other._version

    def __lt__(self, other):
        return self._version < other._version

    def __init__(self, version_string):
        self._version_string = version_string
        self._version = PackageVersion(version=self._version_string)

    def __repr__(self):
        return 'Version: {}'.format(self._version)

    def _as_base(self, parts):
        result = '.'.join(
            map(
                str, parts
            )
        )

        return result

    def _as_add_suffixes(self, version_string):
        result = '{}'.format(version_string)

        if self._version.local:
            result = '{}+{}'.format(result, self._version.local)

        return result

    def as_major(self):
        base = self._as_base(
            parts=(self._version.major,)
        )

        return self._as_add_suffixes(version_string=base)

    def as_micro(self):
        base = self._as_base(
            parts=(
                self._version.major, self._version.minor, self._version.micro
            )
        )

        return self._as_add_suffixes(version_string=base)

    def as_minor(self):
        base = self._as_base(
            parts=(self._version.major, self._version.minor)
        )

        return self._as_add_suffixes(version_string=base)

    def as_upstream(self):
        return self._version.public

    @property
    def dev(self):
        if self._version.dev is not None:
            return str(self._version.dev)

    def get_version_string(self):
        return str(self._version)

    def increment_dev(self):
        version_string = '.'.join(
            map(str, self._version.release)
        )

        if self._version.dev is None:
            dev = -1
        else:
            dev = self._version.dev or 0

        version_string = '{}.dev{}'.format(version_string, dev + 1)

        if self._version.local:
            version_string = '{}+{}'.format(
                version_string, self._version.local
            )

        self._version = PackageVersion(
            version=version_string
        )
        return self

    def increment_major(self):
        version_string = '{}'.format(
            self._version.major + 1
        )

        if self._version.local:
            version_string = '{}+{}'.format(
                version_string, self._version.local
            )

        self._version = PackageVersion(
            version=version_string
        )
        return self

    def increment_micro(self):
        version_string = '{}.{}.{}'.format(
            self._version.major, self._version.minor, self._version.micro + 1
        )

        if self._version.local:
            version_string = '{}+{}'.format(
                version_string, self._version.local
            )

        self._version = PackageVersion(
            version=version_string
        )
        return self

    def increment_minor(self):
        version_string = '{}.{}'.format(
            self._version.major, self._version.minor + 1
        )

        if self._version.local:
            version_string = '{}+{}'.format(
                version_string, self._version.local
            )

        self._version = PackageVersion(
            version=version_string
        )
        return self

    def increment_pre(self):
        version_string = '.'.join(
            map(str, self._version.release)
        )

        if self._version.pre is None:
            pre = ('a', -1)
        else:
            pre = self._version.pre

        version_string = '{}{}{}'.format(version_string, pre[0], pre[1] + 1)

        if self._version.local:
            version_string = '{}+{}'.format(
                version_string, self._version.local
            )

        self._version = PackageVersion(
            version=version_string
        )
        return self

    def increment_post(self):
        version_string = '.'.join(
            map(str, self._version.release)
        )

        if self._version.pre is not None:
            version_string = '{}{}{}'.format(
                version_string, self._version.pre[0], self._version.pre[1]
            )

        if self._version.post is None:
            post = -1
        else:
            post = self._version.post or 0

        version_string = '{}.post{}'.format(version_string, post + 1)

        if self._version.local:
            version_string = '{}+{}'.format(
                version_string, self._version.local
            )

        self._version = PackageVersion(
            version=version_string
        )
        return self

    @property
    def major(self):
        return self._version.major

    @property
    def micro(self):
        return self._version.micro

    @property
    def minor(self):
        return self._version.minor

    @property
    def post(self):
        if self._version.post is not None:
            return str(self._version.post)

    @property
    def pre(self):
        if self._version.pre:
            return ''.join(
                map(
                    str, self._version.pre
                )
            )


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '-test':
        doctest.testmod()
        exit(0)

    if len(sys.argv) == 1:
        print(
            'usage: [version] <part to retrieve [major, minor, micro, upstream]> <-test>'
        )
        exit(0)

    if len(sys.argv) < 3:
        print('Insufficient arguments')
        exit(1)

    version_string = sys.argv[1]
    if version_string == '-':
        version_string = sys.stdin.read().replace('\n', '')

    version = Version(version_string=version_string)
    part = sys.argv[2].lower()

    if part == 'major':
        output = version.as_major()
    elif part == 'minor':
        output = version.as_minor() or ''
    elif part == 'micro':
        output = version.as_micro() or ''
    elif part == 'upstream':
        output = version.as_upstream() or ''
    else:
        print('Unknown part')
        exit(1)

    print(output)
