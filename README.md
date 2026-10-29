# Egyptian — a fork based on Mayan EDMS® 4.x

**Egyptian** is a production fork of [Mayan EDMS](https://gitlab.com/mayan-edms/mayan-edms) 4.x,
maintained by [mypalace.ca](https://egyptian-apps.mypalace.ca).
It ships bug fixes that have not yet been merged upstream, and serves as the base for a set of
commercial extensions built and used in production.

---

## Free bug fixes included in this fork

All fixes below are available to anyone who runs this fork, at no cost. The list only keeps
what still differs from Mayan EDMS 4.12.2: fixes that Mayan EDMS has made since then are not
listed.

### Security and core fixes

#### OIDC

- Add cross-origin SSO logout support (the logout URL is escaped in the page script)
- Add missing OIDC parameters (token expiry, logout endpoint, id token storage)
- Add ModelBackend fallback for OIDC-down scenarios

#### Encrypted storage

- Migrate AES-256-CBC to AES-256-GCM (authenticated encryption)
- Replace fixed salt with per-file random salt (32 bytes)
- Add per-file random nonce (12 bytes)
- Increase PBKDF2 iterations: 100k to 600k (OWASP 2024)
- Switch from pycryptodome to cryptography (PyCA)

#### Elasticsearch search

- Fix partial search on text fields (wildcard to match)
- Add shared Point-in-Time for multi-scope queries
- Cap page size to SEARCH_RESULTS_LIMIT
- Tolerate deleted objects in index/deindex tasks

#### Core

- Retry the OCR task on FileNotFoundError

### More file formats

The converter also renders SVG, RAW photo, DXF, STL and DICOM files and HEIF/HEIC images,
and, when their tools are installed, videos (first frame, FFmpeg), DjVu (djvulibre), EPUB
(Calibre), EML and Markdown (WeasyPrint).

---

## Extensions

The following applications extend Mayan EDMS with AI, workflow, and productivity features.
Access is granted per GitHub account via private repository; the free ones need an account
on the site.
All prices are in USD.

| Application | What it does | Price |
|---|---|---|
| [Approvals](https://egyptian-apps.mypalace.ca/apps/approvals/) | Document approval workflows with SLA and notifications | from $999 / yr |
| [ACL Explorer](https://egyptian-apps.mypalace.ca/apps/acl-explorer/) | Audit tool — see exactly what any user can access and why | $99 one-time |
| [Workflow UI](https://egyptian-apps.mypalace.ca/apps/workflow-ui/) | Visual drag-and-drop workflow editor | $499 one-time |
| [Document Q&A](https://egyptian-apps.mypalace.ca/apps/document-qa/) | Ask your documents in natural language — answers based on their text | $299 one-time |
| [Document Embedding](https://egyptian-apps.mypalace.ca/apps/document-embedding/) | Semantic search — find what you don't know how to search for | free with an account |
| [Document NER](https://egyptian-apps.mypalace.ca/apps/document-ner/) | Automatically extract persons, organizations, places and more from your documents | free with an account |
| [Autotag](https://egyptian-apps.mypalace.ca/apps/document-autotag/) | Zero-shot automatic tagging — your existing tags applied intelligently | free with an account |
| [Activity Report](https://egyptian-apps.mypalace.ca/apps/activity-report/) | Exportable audit reports: who did what, when, on which document | $149 one-time |
| [Barcode Extract](https://egyptian-apps.mypalace.ca/apps/image-barcode-extract/) | Automatically detect and index all barcodes in your documents | $149 one-time |
| [Document Health](https://egyptian-apps.mypalace.ca/apps/document-health/) | Quality dashboard — spot the documents that need attention | $149 one-time |
| [Version Diff](https://egyptian-apps.mypalace.ca/apps/document-version-diff/) | Compare two versions of a document — highlighted differences in one click | $149 one-time |
| [OCR Viewer](https://egyptian-apps.mypalace.ca/apps/ocr-viewer/) | Read, search and copy the OCR text of your scanned documents | $99 one-time |
| [Themes](https://egyptian-apps.mypalace.ca/apps/themes/) | 13 themes for Mayan EDMS 4.12, with the menus in the colors of the theme | $4.99 one-time |

Browse all apps and purchase access: **[egyptian-apps.mypalace.ca](https://egyptian-apps.mypalace.ca)**

---

## Docker image

A public image of Egyptian, without the extensions, is published on Docker Hub:
**[mypalace/egyptian](https://hub.docker.com/r/mypalace/egyptian)**. It is built from this
repository (`docker/`, GitHub Actions) and keeps the paths and the `MAYAN_*` variables of the
Mayan EDMS image: the Mayan EDMS Docker Compose file and `install-custom-apps.sh` work with it.

```bash
cd docker
docker compose up --detach
```

`docker/docker-compose.yml` uses `mypalace/egyptian:s4.12` (`MAYAN_DOCKER_IMAGE_NAME`,
`MAYAN_DOCKER_IMAGE_TAG`). Set your own passwords in `docker/.env` before real use.

The image renders the added formats that only need Python libraries (SVG, RAW photos, DXF,
STL, DICOM, HEIF/HEIC). Videos, DjVu, EPUB, EML and Markdown need tools that are not in the
image yet (FFmpeg, djvulibre, Calibre, WeasyPrint); the `MAYAN_APT_INSTALLS` and
`MAYAN_PIP_INSTALLS` variables of the image install packages at start up.

To regenerate the files of the image after a change to the workers, the queues or
`mayan/literals.py`, see `docker/generer.py`.

---

## Community forum

Questions, feedback, and discussion about Egyptian and its extensions:

**[egyptian-apps.mypalace.ca/forum/](https://egyptian-apps.mypalace.ca/forum/)**

---

## About Mayan EDMS

Mayan EDMS is a free, open source document management system written in Python / Django.
It provides document storage, OCR, workflows, metadata, access control, and much more,
and is designed for self-hosted enterprise deployments.

- **Source code**: [gitlab.com/mayan-edms/mayan-edms](https://gitlab.com/mayan-edms/mayan-edms)
- **Documentation**: [docs.mayan-edms.com](https://docs.mayan-edms.com)
- **License**: GNU General Public License, version 2.0 (GPL-2.0-only)

Egyptian tracks the Mayan EDMS 4.x branch. Changes in this fork that are generic enough
are submitted upstream when possible.

"Mayan EDMS" is a registered trademark of Roberto Rosario. Egyptian and its extensions are
not affiliated with, or endorsed by, the Mayan EDMS project or its trademark holder.
