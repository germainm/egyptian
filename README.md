<p align="center">
  <img src="mayan/apps/appearance/static/appearance/images/egyptian-about.png"
       alt="Egyptian: a golden pyramid and the sun over the desert" width="640">
</p>

# Egyptian — a fork based on Mayan EDMS® 4.x

**Egyptian** is a production fork of [Mayan EDMS](https://gitlab.com/mayan-edms/mayan-edms) 4.x,
maintained by [mypalace.ca](https://www.mypalace.ca/).
It ships bug fixes that have not yet been merged upstream, and serves as the base for a set of
commercial extensions built and used in production.

---

## What's new — November 4, 2026

- **12-bit JPEG in DICOM files.** The *JPEG Extended* images with samples of 12 bits gave a page
  of attributes: Pillow and the GDCM plugin of pydicom refuse these samples, and the remaining
  plugin, `pylibjpeg-libjpeg`, is under the GPLv3, which cannot be combined with the
  GPL-2.0-only license of this project. They are now read by a decoder of this project, in
  Python with numpy (`mayan/apps/converter/renderers/jpeg_extended.py`), with no new dependency.
  Its values were compared with those of libjpeg-turbo 3.1.3: identical on 168 monochrome images
  of all sizes and qualities, on 8,400 color images of 8 and 12 bits with all the chroma
  samplings, from 1 to 301 pixels wide, the components with fewer samples being enlarged by the
  same filter, and on the 43 JPEG images of the test data of pydicom and pylibjpeg. Large images
  of one component are read with numpy, as lossless JPEG below: on the test server, a mammogram of
  14 megapixels takes 1.8 s at quality 90 (6.3 s with a Python loop) and 4.2 s at quality 100
  (8.1 s). The loop remains for the other images and for the streams too dense for the readers,
  such as pure noise at the highest quality, 12% slower than the loop alone; both give the same
  result on 842 files, 360 of them damaged. Images over 64 million samples or 2 minutes of
  decoding, and files too short for the size they declare, get the page of attributes with the
  reason.
- **No more `python-gdcm`.** This package is under the Apache-2.0 license and bundles OpenSSL
  1.1.1k. JPEG-LS is now read by `pyjpegls` (MIT, with CharLS under a BSD license), JPEG 2000 by
  `pylibjpeg-openjpeg` (MIT, with OpenJPEG under a BSD license) with Pillow after it, and
  lossless JPEG by a second decoder of this project
  (`mayan/apps/converter/renderers/jpeg_lossless.py`), for all the predictors, from 2 to 16 bits.
  On the real files of the test data of pydicom, the values are those of GDCM: 17 JPEG-LS files,
  30 JPEG 2000 files, 15 8-bit JPEG files; those of GDCM or libjpeg for 13 lossless JPEG files.
  The pages of 193 sample DICOM files are the same as before, except for 8 files that now have
  their image instead of a page of attributes, among them two in High-Throughput JPEG 2000 and
  one in JPEG-LS that GDCM did not read. The lossless decoder reads the Huffman codes with numpy:
  thousands of readers start along the stream, where they resynchronize by themselves, and a
  part of the stream only counts if the reader of the previous part ended exactly on its first
  bit. On the test server, a mammogram of 14 megapixels takes 0.9 s to decode (7.4 s with a
  Python loop), and 1.3 to 1.7 s for its whole page (1.6 s with GDCM). The loop remains for what
  the readers refuse: damaged data, streams that do not resynchronize, scans with several Huffman
  tables. Both give the same result on 2,453 files, 360 of them damaged, and the values are those
  of libjpeg-turbo in 1,902 comparisons. Do not install `pylibjpeg-libjpeg` (GPLv3), an optional
  extra of `pylibjpeg`.
- **No more `extract-msg`.** This package and `pcodedmp`, which it brought, are under the GPLv3,
  which cannot be combined with the license of this project. Outlook `.msg` files are
  now read by a reader of this project (`mayan/apps/storage/outlook.py`), written from the public
  specification of the format, [MS-OXMSG], on `olefile` (BSD). 13 packages leave the installation.
  On the 41 sample files of Apache POI, the text and the attachments are those of `extract-msg`,
  except that the Russian and Chinese text of 8-bit files is now readable, an attached message is
  an `.eml` file instead of an object without a name, and two damaged files that it refused are
  read. The sender has an address when the file holds one, recipients taken from the Internet
  headers keep their separators, and an address missing no longer gives `<None>`. One test file
  has a subject in the wrong encoding: it announces no code page but the one of its HTML body.
- **The pages of Outlook files are those of an email.** They only held the text of the message,
  through LibreOffice. They now show the sender, the recipients, the date, the subject and the
  names of the attachments, then the body, in HTML with its images when the file has one. The 41
  sample files of Apache POI take 6.6 s together; one of them, with thousands of recipients, gets
  26 pages to list them. Messages already stored keep the pages they have.
- **The HTML that Outlook writes stays on the page of the headers.** It puts the message in a named
  page, which started a new page: the headers were alone on the first one. This also applies to
  the `.eml` files that come from Outlook.
- **SVG drawings rendered by `rsvg-convert`.** It replaces `CairoSVG` (LGPL-3.0 or later): this
  command line program of librsvg (LGPL-2.1 or later, package `librsvg2-bin`) is started for each
  drawing. On the 1,762 test drawings of resvg, 905 are close to their reference image instead of
  656, and 3 are not rendered instead of 67. On 294 real logos and icons, none fails; the difference
  between the two is 0.12% on average, and in the largest ones, seen side by side, its image is
  that of Chrome where `CairoSVG` was wrong on three logos. A few bytes can ask for a huge drawing: 1.5 GB and
  60 seconds at the most. A drawing of 32,000 by 32,000 pixels is now refused at once, instead of
  taking 42 s and 3.9 GB before being refused. Signatures are read from `data:` URLs only:
  `CairoSVG` received their field as an address.
  Checked on a running instance: 7 drawings, among them those three logos and a `.svgz` file, and
  a signature have the right image, a remote image is not loaded, and the drawing of 32,000 pixels
  and a signature that names a file get an error instead of an image.
- **Attachments of the same name.** When an email or an Outlook message is split into documents,
  two attachments of the same name gave the first one twice, and an attachment named
  `message.txt` gave the text of an Outlook message. They are now `facture.pdf`,
  `facture (2).pdf`.
- **Text of office files: one conversion per file.** LibreOffice converted the whole file for each
  page: 4.5 s for a document of 4 pages, now 1.2 s, for the same text.
- **Checked on a running instance.** 24 files were uploaded and processed by its workers: DICOM
  images, among them the mammogram at quality 90 and a real radiograph, 11 `.msg` files and 2
  `.eml` files. A `.msg` and an `.eml` file were also split into documents. The images of the first
  pages and the text are right, the OCR ran, and no error was logged. The conversion of office
  files was only measured on the test server.
- **The text of emails is extracted.** It only came from the OCR of the page images. It is now
  read from the PDF file that gives the pages, page by page, as soon as the file is uploaded:
  headers, names of the attachments, body. Outlook `.msg` files get the text of their page the
  same way. For the emails already stored, use *Submit for parsing*.
- **More of an email on its pages.** The `Cc` header, the name and size of the attachments, the
  images that the HTML names by their Content-ID, which were not loaded. An attached message is
  no longer taken for the body of the email.
- **Markdown files load no external resource.** WeasyPrint requested the images and style sheets
  named in the file, at any address it gave. Markdown files now have the same filter as emails:
  only the images embedded in the file (`data:` URLs) are loaded, the other ones show their
  alternative text.

---

## What's new — November 3, 2026

Every file format of the converter was tested with 86 sample files found on the web (test
corpora of Apache Tika, Pillow and pydicom, raw.pixls.us, video samples). These fixes come out
of that test:

- **Transparent images are no longer black.** PNG files with transparency, SVG drawings, icons:
  the page image is a JPEG, and the transparent pixels lost their alpha channel on the way. They
  are now laid over a white background, and the barcode reader finds the codes they hold.
- **Formats recognized from their content when `file` gives a generic type:** DOCX, XLSX and
  PPTX files whose archive does not start with `[Content_Types].xml`, OpenDocument formulas
  (`application/zip`); DICOM files preceded by a TIFF header and raw photos built on TIFF —
  DNG, NEF, ARW, PEF (`image/tiff`); EMF drawings and Panasonic RW2 photos
  (`application/octet-stream`); emails that start with headers unknown to `file`, as saved by
  Thunderbird or Outlook.com (`text/plain`).
- **Raw photos at full resolution.** NEF and DNG files showed the 160 × 120 preview stored in
  their header, ARW, PEF, RW2 and X3F files had no page at all: all are now developed by rawpy.
- **More formats rendered by LibreOffice:** WMF and EMF drawings, CSV files, XML files (GPX
  tracks included) and Python scripts named `text/x-script.python` by `file` 5.41 and later.
  XML files are shown as their source: read as plain text, they cannot make LibreOffice load
  external resources. HTML files are not added: LibreOffice loads the
  images and style sheets they link to, so the server would request any address that an
  uploaded file names.
- **Photoshop files with layers** are rendered as their merged image, on one page.
- **GPS tracks on a map.** A GPX file was shown as its XML source, on 22 pages for a walk of
  5 km. Its page is now a map of its tracks, routes and named waypoints, headed by its name,
  date, distance, duration and elevation gain, which the OCR reads. The distance and the
  moving time are those of the Itinéraires app (gpxpy), with the total time when the track has
  stops. The map background comes from the tile server of the map of the Itinéraires app when
  it is installed, else from OpenStreetMap: only the zoom level and the numbers of the tiles
  of the area are sent, and the tiles are cached for 7 days. Set the `map_tile_url` entry of
  `CONVERTER_GRAPHICS_BACKEND_ARGUMENTS` to an empty value to draw the tracks without map
  background, with no request to the outside.
- **Audio files get a page.** MP3, FLAC, M4A/AAC, Ogg Vorbis and Opus, WAV, AIFF and WMA files
  had no page. Their page now shows their tags (title, artist, album, date, track, genre…),
  their cover when the file holds one, their waveform, and their duration, encoding and bit
  rate (ffprobe and ffmpeg). The OCR reads them: an audio file is found by its title or
  artist.
- **Archives get pages.** ZIP, JAR, TAR (also gzip, bzip2, xz and zstd compressed), 7z, RAR,
  ISO, CAB, LHA, DEB, RPM, CPIO, XAR and WARC files had no page. Their pages now show the
  format, the compression, the number of files and folders, the sizes, the dates, the comment
  of the archive and of its entries, the encryption (entries that need a password, or names
  that are themselves encrypted), the owners of TAR files, the manifest of JAR files, the
  header of RPM packages (name, version, summary, license, vendor, build date, signature) and
  the properties of RAR archives (version, method and dictionary, solid, locked, recovery
  record, volume, system, comment), then the list of the entries (name, size, date), up to
  2,000 on the pages. The text of the pages is extracted for the search, with the names of up
  to 20,000 entries. A single compressed file (`.gz`, `.bz2`, `.xz`, `.zst`) shows its
  uncompressed size, the start of its text and, for gzip, its original name and date. Nothing
  is extracted: only the directory of the archive is read, by the zipfile module for ZIP files
  and by libarchive (Python package `libarchive-c`, now in the production requirements) for
  the other formats, with only the formats of the file type enabled. RAR archives that
  libarchive stops reading (RAR 1.5 to 4 solid archives, RAR 1.5) are listed from their
  headers; an empty archive says so. Reading stops after 30 seconds, 4 GB decompressed or
  20,000 entries: a decompression bomb gets a page that says where the listing stopped.
  Chinese, Japanese and Korean names use an installed CJK font (Noto Sans CJK, WenQuanYi Zen
  Hei or IPA Gothic).
- **SVGZ drawings.** A compressed SVG drawing (`.svgz`, which `file` reports as
  `application/gzip`) is recognized from its content and shown as a drawing; it is
  decompressed within 64 MB.
- **exiftool metadata of RAR 5 archives and RPM packages.** exiftool 12.57 (Debian 12) cannot
  read RAR 5 archives and RPM packages: it ends with exit code 1 and the error "File format
  error". An error was logged on the document file and no metadata was kept. The tags it still
  gives (file name, size and permissions, ExifTool version) and its error message are now kept,
  as for the formats it does not know ("Unknown file type").
- **DICOM files shown as the file asks.** The pixel values were stretched between their
  minimum and their maximum. They now go through the modality LUT and the window (or VOI
  LUT) of the file, top level or functional groups of the enhanced multi-frame images;
  palette colors and MONOCHROME1 images are shown right. A multi-frame file has one page per
  frame (an ultrasound loop of 30 frames gives 30 pages). Structured reports, ECG and
  radiotherapy plans, which hold no image, get a page of their main attributes with the
  content of the report or the 12 leads of the ECG. Images smaller than 512 pixels (dose
  grids, thumbnails) are enlarged without smoothing. An image that no installed decoder
  can read gets the same page, with the reason and the missing package.
- **Raw photos in the colors of the camera.** They were developed with a daylight white
  balance, which gave a color cast (cyan with Sigma, pink with Olympus, green with Pentax);
  they now use the white balance recorded by the camera.
- **Files that LibreOffice cannot convert no longer break the upload.** When LibreOffice writes
  no PDF file, fails or times out, the error is logged on the document file and the document
  gets its version and its file metadata, like any other format the converter cannot read.
  OpenDocument formulas are in this case: LibreOffice 7.4 does not load them without its
  interface. Before, the upload stopped and left a document without version.
- **Emails on all their pages.** An email was cut to its first page; its attachments are no
  longer shown as base64 text, its plain text is escaped, and the rendering loads no external
  resource (only the images embedded in the message).

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
- Sentry: do not send personal data (user, IP address, cookies) unless `send_default_pii` is
  enabled explicitly
- Lay images with transparency over a white background before saving the page image as JPEG,
  instead of letting the transparent pixels turn black
- Refine the generic MIME types returned by `file` (`application/zip`, `image/tiff`,
  `application/octet-stream`, `text/plain`) from the content: Office Open XML and OpenDocument
  archives, DICOM files with a TIFF header, raw photos built on TIFF, EMF drawings, Panasonic
  raw photos, emails
- Generate the intermediate PDF file with the stored MIME type of the document file instead of
  detecting it again
- Render Photoshop files with layers as their merged image, on one page, instead of failing
  on frame 0
- Render the XML files and the Python scripts (`text/xml`, `text/x-script.python`) as plain
  text, and the CSV, WMF and EMF files, with LibreOffice
- Log the error and complete the upload when LibreOffice writes no PDF file, fails or times
  out, instead of leaving a document without version
- Develop raw photos with the white balance of the camera instead of a daylight balance
- Show DICOM images through their modality LUT and window instead of stretching their values,
  one page per frame
- Give archives pages (summary and list of the entries) instead of a page count error, and
  extract their text for the search
- Show SVGZ drawings, decompressed within a limit
- Keep the exiftool tags of RAR 5 archives and RPM packages, which exiftool 12.57 cannot read,
  instead of logging an error

### More file formats

The converter also renders SVG (`rsvg-convert`, package `librsvg2-bin`), RAW photo (CR2, CRW, NEF, ARW, DNG, ORF, RAF, RW2, PEF, X3F),
DXF, STL and DICOM files (images, structured reports, ECG) and HEIF/HEIC images, GPX tracks
(map), WMF and EMF drawings and CSV files (LibreOffice), ZIP and JAR archives, and, when their
tools are installed, other archives and compressed files (libarchive), videos (first frame,
FFmpeg), audio files (tags, cover and waveform, FFmpeg), DjVu (djvulibre, bundled files), EPUB
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

No image of Egyptian is published: `docker compose` builds it from this repository at the first
start, without the extensions. It keeps the paths and the `MAYAN_*` variables of the Mayan EDMS
image: the Mayan EDMS Docker Compose file and `install-custom-apps.sh` work with it.

```bash
git clone https://github.com/germainm/egyptian.git
cd egyptian/docker
docker compose up --detach
```

Before the first start, edit `docker/.env`:

- Set your own passwords before real use.
- On a machine with fewer than 6 CPUs, set `MAYAN_DOCKER_CPU_LIMIT` to its number of CPUs, for
  example `MAYAN_DOCKER_CPU_LIMIT=4.0`. Otherwise Docker refuses to start the application:
  `Range of CPUs is from 0.01 to 4.00`.

The image has the tools of all the file formats added to the converter: FFmpeg (videos, audio
files), djvulibre (DjVu), Calibre (EPUB), libarchive (archives), WeasyPrint (EML, Markdown)
librsvg (SVG) and the Python libraries of the RAW photo, DXF, STL, DICOM (with pyjpegls and
pylibjpeg-openjpeg), HEIF/HEIC
and archive formats. The GitHub Actions workflow `Docker image`, run by hand, builds it with
Docker Compose, starts it and turns one file of 11 formats into pages. It takes 7 minutes to build
and start on a GitHub runner with 4 CPUs.

### Building the image by hand

From the root of the repository:

```bash
DOCKER_BUILDKIT=1 docker build --tag egyptian:s4.12 --file docker/Dockerfile .
cd docker
docker compose up --detach
```

Docker Compose uses this image and does not build it again. The Dockerfile needs BuildKit: without
`DOCKER_BUILDKIT=1`, Docker 20.10, the version in Debian 12, stops with
`the --mount option requires BuildKit`.

The build took 16 minutes on a virtual machine with 4 vCPUs and 16 GB of memory, with Docker
20.10.24 and Docker Compose 2.32.4. With its cache and the images of the other services, it used
about 6 GB of disk.

To give the image another name, build it with that name:

```bash
DOCKER_BUILDKIT=1 docker build --tag my-egyptian:1.0 --file docker/Dockerfile .
```

and set the name in `docker/.env`:

```bash
MAYAN_DOCKER_IMAGE_NAME=my-egyptian
MAYAN_DOCKER_IMAGE_TAG=1.0
```

To use an image from your own registry, set its name the same way and add
`MAYAN_DOCKER_IMAGE_PULL_POLICY=missing`. Without this line, Docker Compose does not pull the image:
it builds one from the repository under that name.

To update, from the `docker` directory:

```bash
git stash
git pull
git stash pop
docker compose build
docker compose up --detach
```

`git stash` keeps your changes to `docker/.env` aside during the update. `docker compose build` did
not need `DOCKER_BUILDKIT=1` with these versions.

To regenerate the files of the image after a change to the workers, the queues or
`mayan/literals.py`, see `docker/generer.py`.

---

## Tests

The renderers of the formats added to the converter and the refinement of the MIME types have
unit tests (216): archives and compressed files (ZIP, JAR, TAR, gzip, RAR headers, RPM headers,
encryption, decompression bombs, pages and search text), GPS tracks, DICOM images, 12-bit and
lossless JPEG, audio files, SVG drawings and signatures, emails and Markdown files without remote resources, the text of the emails,
the Outlook `.msg` files, transparency, and the content-based MIME types. They need no database and no network: their
files are built in memory or come with pydicom. Run them from a clone of this repository, with
the Python of an Egyptian installation. The Docker image does not contain them.

```bash
MAYAN_MEDIA_ROOT=$(mktemp -d) python3 manage.py test mayan.apps.converter mayan.apps.document_parsing mayan.apps.mime_types mayan.apps.signature_captures mayan.apps.storage
```

The tests that need a tool or a library that is not installed (FFmpeg, libarchive-c,
WeasyPrint, rsvg-convert, pydicom, pyjpegls, pylibjpeg-openjpeg, gpxpy) are skipped. The Egyptian extensions have their own tests in their
repositories.

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
