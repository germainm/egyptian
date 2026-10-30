# Egyptian — a fork based on Mayan EDMS® 4.x

**Egyptian** is a production fork of [Mayan EDMS](https://gitlab.com/mayan-edms/mayan-edms) 4.x,
maintained by [mypalace.ca](https://www.mypalace.ca/).
It ships bug fixes that have not yet been merged upstream, and serves as the base for a set of
commercial extensions built and used in production.

---

## What's new — October 30, 2026

Fixes for large imports, tested in production on October 29 and 30 with more than 380
documents and 18,000 pages (PDF files, office documents, EPUB books):

- **No more copy of the whole PDF file for every page.** Mayan EDMS 4.12.2 copies the entire
  PDF file to the temporary directory each time it renders a page (pdftoppm) or extracts its
  text (pdftotext): with 7 workers on a 223 MB file, 1.6 GB of copies at once, enough to fill
  the disk during an import. Egyptian now reads the stored file in place. The files of the
  encrypted and compressed storages are still copied, since their file on disk does not hold
  the content as read.
- **Oversized pages are rendered instead of failing.** Very tall pages, such as captures of
  whole web pages (1,626 × 8,138 points), stopped with a decompression bomb error. They are now
  rendered at the resolution that fits the pixel limit of Pillow.
- **Office documents and EPUB books are OCRed to the last page.** All their pages are rendered
  from the same intermediate file: each page now waits for its lock (up to 30 seconds) instead
  of failing at once — on the test bench, 68 of 70 attempts failed with 7 workers before the
  fix — and the OCR retries are spread over 5 to 60 seconds, up to 20 times. An EPUB book is
  converted once, not once per page.
- **RTF files and file metadata.** LibreOffice gets the extension of RTF files, which it did
  not always recognize without one, and the NUL characters that PostgreSQL rejects are removed
  from file metadata (PDF files made by old versions of Acrobat).

Also new: the **System** menu of Egyptian opens the [documentation wiki](https://wiki.mypalace.ca/en/home)
and a page of the Egyptian applications, installed or not, with the documentation, the forum
and the store page of each one.

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
- Let the readers of a cached file wait for its lock (up to 30 s) instead of failing at once:
  all the pages of an office document are rendered from the same intermediate file
- Spread the retries of the OCR task on lock errors, and allow more of them
- Give LibreOffice the extension of RTF files, which it did not always recognize without one
- Remove NUL characters from file metadata, which PostgreSQL rejects
- Read PDF files stored as plain files in place to render their pages (pdftoppm) and to
  extract their text (pdftotext), instead of copying the whole file to the temporary
  directory for each page
- Render oversized PDF pages (captures of whole web pages) at the resolution that fits the
  pixel limit of Pillow, instead of failing with a decompression bomb error

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

The image has the tools of all the file formats added to the converter: FFmpeg (videos),
djvulibre (DjVu), Calibre (EPUB), WeasyPrint (EML, Markdown) and the Python libraries of the
SVG, RAW photo, DXF, STL, DICOM and HEIF/HEIC formats.

To regenerate the files of the image after a change to the workers, the queues or
`mayan/literals.py`, see `docker/generer.py`.

---

## Documentation

**[wiki.mypalace.ca](https://wiki.mypalace.ca/en/home)** — installation, operations, reference
guides, development, and one page per Egyptian application, in English and in French.

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
