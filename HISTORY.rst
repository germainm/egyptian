4.12.2 (2026-09-14)
===================

Added
-----

- Added a configurable OpenID Connect session renewal interval. Existing
  sessions keep their current deadline and use a changed interval after their
  next successful renewal.
- Added a formatted trademark policy page, accessible from the About page and
  System menu and available without an internet connection.
- Added the project website and trademark and copyright registration details
  to the About page.

Changed
-------

- Clarified the trademark policy and licensing FAQ, distinguishing software
  license permissions from conditions on using the project's name and logo.
- Updated documentation links and rendered references to retired issue and
  forum pages as text.

Fixed
-----

- Fixed OpenID Connect return destinations under URL prefixes and across
  abandoned or concurrent login attempts. Renewal responses must match the
  configured provider endpoint and a pending authorization state.
- Fixed a failed OpenID Connect attempt sending the browser outside an
  installation served under a URL prefix. The failure destination is now
  resolved, and defaults to the login view rather than the site root.
- Fixed document images failing to load when an OpenID Connect session expires.
  Concurrent background requests now initiate only one session renewal
  navigation.
- Fixed service worker registration for visitors who are not logged in, and
  prevented expired OpenID Connect sessions from redirecting requests for the
  worker script or service unavailable page to the identity provider.
- Fixed form widgets, including file upload drop areas, not initializing on
  initial page loads or in modal dialogs.
- Fixed appending a document file when the document has no active version.
  The new file's pages now form the complete version.
- Fixed bookmarked, pasted, and refreshed links redirecting outside the
  application when it is installed under a URL sub-path.
- Restored usable heights for add/remove selection lists and read-only
  license, message, OCR, and parsed-text panes.
- Fixed checkbox and select styling in table-based forms, including the
  upload wizard and document download form.
- Fixed list action menus being clipped or expanding the page on small
  screens while preserving horizontal table scrolling.
- Fixed the reload content animation rotating its label or spinning
  indefinitely.
- Fixed translations of access control and error log view titles, storage
  and metadata error messages, smart link errors, and download message
  template help text.
- Fixed link attributes containing filenames with spaces being truncated.
- Fixed user accounts carrying the staff or super user flag not appearing in
  the user list of a group and not being removable from it, individually or
  with the "Remove all" button. The member list now resolves its users
  against the requester, matching the list of available users shown beside
  it.
- Fixed the REST API user list, user detail, user group list, and group user
  add and remove endpoints hiding accounts carrying the staff or super user
  flag from every requester, including a privileged one, while the
  equivalent interface views showed them. Changing the password of such an
  account through the user detail endpoint remains reserved for
  administration tools, as it is in the interface.
- Restored the fallback display for unavailable document thumbnails and fixed
  server errors from the template list API endpoint.
- Fixed fuzzy searches failing with the Django search backend and excessive
  memory use for long search terms.
- Fixed `search_index_objects` reporting the requested identifier range size
  instead of the number of objects actually queued.
- Fixed ClamAV and EXIF metadata driver timeouts not taking effect when
  supplied as template-rendered values.
- Corrected the release version reported to Sentry.
- Corrected the license identifier and version in the citation metadata.
- Restored the public changelog in source distributions, corrected the PyPI
  changelog link, and fixed broken images on the package description page.

Security
--------

- Disabled accounts can no longer resume existing OpenID Connect sessions or
  authenticate with OpenID Connect Bearer tokens. A refused reauthentication
  attempt also revokes the existing session.
- Validated request-supplied redirect destinations after form submissions and
  actions, using a local fallback for destinations outside the installation.
- The REST API current user endpoint now rejects unauthenticated requests
  instead of returning anonymous user details or failing on write requests.
- The REST API group user list endpoint no longer returns members carrying
  the staff or super user flag to requesters that carry neither.
- Added validation for inverted percentage-based rectangle transformations,
  including redactions, so invalid coordinates are rejected when saved.
- Updated security dependencies to address vulnerabilities in Django and
  Django REST framework.


4.12.1 (2026-08-21)
===================

Changed
-------

- Added configurable timeouts to OCR, SANE scanning, MIME type detection,
  EXIF metadata extraction, ClamAV scanning, GPG operations, document parsing,
  and document conversion commands. Commands that stop responding now fail
  with an error instead of holding a worker indefinitely.
- Document parsing now reads `pdftotext` output while the command runs,
  preventing large pages from deadlocking the parser.

Fixed
-----

- Improved card entry ordering in right-to-left interfaces.
- Reload the interface after the current user changes languages so the correct
  left-to-right or right-to-left styles are applied.
- Reinforced object permission checks for REST API views that calculate
  permissions dynamically.
- Added the missing trailing slash to workflow transition field and trigger
  detail API endpoints.

Security
--------

- Updated Django, Pillow, pypdf, and setuptools to address published security
  vulnerabilities. Also updated pip.


4.12 (2026-08-16)
=================

Added
-----

- Added the sequences app for generating persistent, atomic arithmetic or
  symbolic values. Sequences support document type restrictions, workflow
  actions, permissions, events, reset actions, and REST API access.
- Added authentication attempt tracking and configurable account lockouts,
  including automatic cool-off, administrator reset actions, and audit events.
- Added access control lists and a view permission for dashboards.
- Move document favorites out of the documents app.
- Added the server-side events app to deliver in-app toast messages without
  polling.
- Added an optional service worker that presents a branded, retryable service
  unavailable page for connection failures and HTTP 502, 503, and 504 errors.
- Added light and dark color modes, theme and color mode selectors, and
  right-to-left interface support for bidirectional languages.
- Added automatic, high-contrast tag colors derived from tag labels and
  optional automatic color fields through `FORMS_COLOR_AUTO_ENABLED`.
- Added configurable thumbnail click behavior. Thumbnails can open an image
  preview or navigate directly to the document.
- Added absolute and percentage-based "Draw text" image transformations.
- Added configurable REST API throttling. The authenticated-user default is
  20 requests per second.
- Added OpenAPI 3 REST API documentation using drf-spectacular.
- Added source expansion modes that can keep empty containers or retain both
  a container and its extracted files.
- Added a raw-file ClamAV metadata driver and configurable maximum lengths for
  stored file metadata values.
- Added background task deduplication for document indexing and search
  indexing work.
- Added worker F and a separate `ocr_slow` queue for long-running per-file and
  per-page processing.
- Added a consumed default Celery queue so incorrectly routed tasks no longer
  disappear into an unconsumed queue.
- Added configurable global and per-worker container resource limits.
- Added file cache eviction protection for recently created files and stricter
  least-recently-used eviction.
- Added the `storage_shard_files` management command.
- Added initialization step isolation and preconditions so setup and upgrade
  failures are collected and reported clearly.

Changed
-------

- Improved support for hosting static and media files under
  `ORGANIZATIONS_URL_BASE_PATH`.
- Migrated the interface from Bootstrap 3 to Bootstrap 5 and rebuilt the
  responsive, mobile, toolbar, form, pager, offcanvas, and error-page layouts.
- Table rows and card headers can now be clicked to select list items. Links,
  buttons, text selection, and range selection retain their normal behavior.
- Improved list and dashboard empty states, card labels, boolean indicators,
  date columns, accessibility text, and dark-mode contrast.
- Modernized create, edit, action, and confirmation button labels. Create
  forms can now save an item and immediately open a blank form for another.
- Reworked icons around Font Awesome 6 and replaced ambiguous symbols with
  clearer ones.
- Redesigned the Dropzone uploader. Upload failures now return structured
  errors and useful messages instead of raw intermediary HTML.
- Document image viewers now load nearby pages on demand, limit concurrent
  requests, retry rate limits, release distant images, and recover individual
  thumbnails or pages from server errors.
- Exposed document image request concurrency, rate, and retry behavior as
  converter settings.
- Improved resize transformation quality and made LibreOffice arguments and
  environment variables configurable.
- Document files and versions are now printed as a single PDF using the
  browser's PDF viewer and print controls.
- Exports are completed before their download entry is created. Failed exports
  and mail attachments no longer leave incomplete downloads or send partial
  messages, and failures are recorded on the relevant object.
- Mailing body templates now accept template tag syntax.
- OCR avoids unnecessary image conversion, discovers Tesseract languages only
  when needed, uses longer processing locks, and retrieves version text in one
  query.
- File metadata replacement is atomic. Metadata lists, driver validation,
  command errors, falsy arguments, and OpenAI and Ollama integrations were
  improved.
- ClamAV is disabled by default for newly created document types. Existing
  document type configuration is retained.
- Search indexing now avoids work when relevant fields did not change.
  Elasticsearch transient errors and rate limits are retried, while Whoosh
  locking, cleanup, error reporting, and write speed were improved.
- Increased `SEARCH_INDEXING_CHUNK_SIZE` from 25 to 500.
- Malformed page and identifier ranges are validated before work is queued.
- Rebalanced background queues and raised worker B and D concurrency. Cache
  pruning and stale marker cleanup now run as background maintenance tasks.
- Celery shares one result backend per process and uses exclusive event and
  remote-control queues.
- Redis now uses the `noeviction` policy and four databases so memory pressure
  is reported rather than silently discarding locks, task results, or events.
- Archive creation streams file content instead of loading every member into
  memory. Passthrough, encrypted, sharded, and temporary-file storage behavior
  was improved.
- The REST API now publishes identifiers for file metadata driver
  configurations, notifications, document file signatures, and resolved smart
  links, and includes transformation arguments in page image URLs.
- The REST API source upload action now accepts `expand_mode` and no longer
  applies interactive wizard cabinet, tag, or metadata steps as side effects.
- Settings now validate common list, password validator, boolean, proxy, and
  image size values more consistently and report rejected edits correctly.
- Exposed `SERVER_EMAIL`; improved `MAYAN_ALLOWED_HOSTS`,
  `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`, and
  `USE_X_FORWARDED_PORT` overrides.
- Improved the settings detail and namespace views and made configuration
  writes atomic.
- Updated the Docker deployment to Traefik 3.7.9, increased the default CPU
  limit to six, and made Gunicorn and Celery log levels follow the main Mayan
  logging level unless explicitly overridden.
- Improved documentation navigation, getting-started instructions, feature
  descriptions, and light/dark presentation.
- Updated djangorestframework, Elasticsearch, Gunicorn, OpenAI, Ollama, pytz,
  Sentry SDK, and other dependencies.

Fixed
-----

- Fixed card, pager, action dropdown, checkbox, toolbar, Select2, Dropzone,
  external link, AJAX redirect, and partial navigation behavior.
- Fixed stale toast messages being replayed and menu refreshes interrupting
  users interacting with controls.
- Fixed the favorite document, recently accessed and recently created document
  count settings not always accepting overrides.
- Fixed the document file, document page image cache, document version page
  image cache, and source cache storage settings not always accepting
  overrides.
- Fixed office document page image and OCR generation, concurrent intermediate
  file creation, missing or empty `pdfinfo` output, and transformation error
  reporting.
- Fixed image cache collisions, duplicate generation, failure recovery, and
  file, version, and page deletion errors.
- Fixed document signature identifiers generated with python-gnupg 0.5.x.
  Run "Refresh all signatures" to update existing signatures.
- Fixed compressed source validation, decompression reporting, unexpected
  source task error reporting, and IMAP destination mailbox moves.
- Fixed downloading multiple document files as an archive from object storage
  backends such as S3.
- Fixed encrypted storage writes and seeking in passthrough storage backends.
- Fixed Tesseract error formatting and OCR work continuing after a document
  version is deleted.
- Fixed file metadata driver result loss, driver argument handling, and ClamAV
  and ExifTool command error reporting.
- Fixed empty search queries, preserved query strings in filtered lists, and
  improved Elasticsearch and Whoosh index cleanup and status reporting.
- Fixed workflow action secondary permission enforcement, workflow initial
  state logging, role recipients for the send-message action, and unnecessary
  workflow launch tasks.
- Fixed access control enforcement when creating ACLs and marking messages as
  read.
- Fixed the API version root and login exemptions when installed under complex
  organization base paths.
- Fixed smart setting defaults, pending values, cache races, environment and
  configuration overrides, and invalid values shown as successfully saved.
- Fixed source, favorite, cache, proxy, password validator, and display-size
  settings that were sometimes ignored.
- Fixed container worker startup, Gunicorn bind and request-line settings,
  logging levels, and configuration parsing.
- Fixed historical data migrations for document latest files, duplicate
  documents, OCR content, document languages, workflow names, states and
  triggers, announcements, SANE scanner sources, source metadata, and stored
  credentials. Multi-database migration writes now use the selected database.
- Fixed indexing of deleted or unchanged objects, index node counts and
  pruning, and workflow trash-state retention checks.

Security
--------

- Added proactive limits against archive bombs, oversized compressed inputs,
  oversized members, and excessive compression ratios.
- Hardened message, cabinet tree, template, Dropzone, referer, redirect, and
  external-link handling against injection and unsafe navigation.
- Strengthened access control checks to deny access by default for unsupported
  objects and emit events when permissions change.
- Added validation for organization installation URLs, base paths, allowed
  hosts, trusted origins, authentication backends, and password validators.

Upgrade notes
-------------

- Manual deployments must add worker F and the `ocr_slow` queue. Deployments
  using the supplied Docker Compose or supervisor configuration are updated
  automatically.
- REST API uploads no longer apply cabinet, tag, or metadata wizard steps.
  Upload in immediate mode and use the dedicated endpoints instead.
- Enable the ClamAV driver explicitly for new document types if malware
  scanning is required. Existing document types keep their current setting.
- Download the latest Docker Compose file for the worker layout, Redis policy,
  database count, CPU defaults, and Traefik 3 image.
- Review Redis memory limits, REST API request rates, worker resource limits,
  sub-path static and media URLs, and OpenAPI client generation.

Deprecated
----------

- Deprecated `POST /documents/upload/` in favor of the sources app document
  upload action. Removal is planned for Mayan EDMS 5.0.
- The source upload `expand` Boolean is superseded by `expand_mode` but remains
  available for compatibility.
