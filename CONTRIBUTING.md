Contributing to Egyptian
========================

Egyptian is a fork based on Mayan EDMS, maintained by mypalace.ca. Its source
code is at https://github.com/germainm/egyptian and contributions are made
with **pull requests** on that repository.

Questions and support
---------------------

- For questions, help with an installation or the extensions of
  https://egyptian-apps.mypalace.ca, use the forum:
  https://egyptian-apps.mypalace.ca/forum/
- The extensions sold or given on that site are not in this repository;
  report their problems on the forum, not here.

Issues
------

- Open a GitHub issue for a problem with the code of Egyptian, after checking
  the existing issues.
- Reproduce the problem on a separate, clean installation when you can: a
  configuration error can look like a bug.
- Give the steps that trigger the problem, the version (shown on the About
  page) and, when it helps, screenshots.
- Do not attach private or confidential files. If a file triggers the
  problem, make a dummy file with the same properties.
- **Security problems**: do not open a public issue. Write to
  germain.malenfant@mypalace.ca with the details.

Pull requests
-------------

1. Fork https://github.com/germainm/egyptian on GitHub.
1. Create a branch from `master` for your change, one subject per branch.
1. Make your change, with a test that shows the bug is fixed or the feature
   works, when the code can be tested.
1. Sign off each commit (see below), then open a pull request against
   `master`. Explain what the change does and why.
1. Keep the pull request up to date with the review. It is merged when it is
   approved; a change may also be declined, for example when it belongs in
   Mayan EDMS itself (see below).

Copyright and license
---------------------

- Egyptian is distributed under the GNU General Public License, version 2.0
  only (see `LICENSE`). By contributing, you license your contribution under
  the same terms. **You keep the copyright of your work**: there is no
  copyright assignment.
- **Sign off** every commit with your real name and email. The sign-off
  certifies that you have the right to submit the work under this license,
  as described in the Developer Certificate of Origin (`DCO`):

      Signed-off-by: Jane Doe <jane.doe@example.com>

  With `user.name` and `user.email` set in git, `git commit -s` adds it.
- Only submit work that you wrote, or that you have the right to submit
  under GPL-2.0-only. Code taken from elsewhere must be compatible with this
  license; keep its notices and give its origin and license in the pull
  request.
- **Do not remove or change** an existing copyright, license or trademark
  notice. Most of the code is the work of Roberto Rosario and the Mayan EDMS
  contributors, and their notices stay.

Trademarks
----------

"Mayan EDMS" and the Mayan EDMS logo are registered trademarks of Roberto
Rosario (see `TRADEMARK_POLICY.md`). Egyptian is not affiliated with, or
endorsed by, the Mayan EDMS project. Contributions must not present Egyptian
as Mayan EDMS: do not use that name or logo as the name or logo of the
software, in the interface, the documentation or the package metadata.
Factual references, such as "based on Mayan EDMS", are fine.

Changes for Mayan EDMS itself
-----------------------------

A fix that applies to Mayan EDMS as well is best submitted to Mayan EDMS
directly, following its own rules (https://gitlab.com/mayan-edms/mayan-edms;
Mayan EDMS asks its contributors for a copyright assignment agreement).
Egyptian picks up the Mayan EDMS releases.

Code style and translations
---------------------------

- Follow the style of the surrounding code, which is the style of Mayan
  EDMS: https://docs.mayan-edms.com/chapters/development/index.html
- The translations of the Mayan EDMS texts are made by the Mayan EDMS
  project on Transifex. For the texts specific to Egyptian, propose
  corrections or translations in an issue or a pull request.
