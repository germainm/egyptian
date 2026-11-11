# Changelog

The changes made by Egyptian, newest first. For what Egyptian adds to Mayan EDMS as a whole, see
the [README](README.md). The release notes of Mayan EDMS itself are in [HISTORY.rst](HISTORY.rst).

---

## November 11, 2026

- **Finance: the total and the supplier are read from the right line.** On invoices with taxes, the
  stored amount was the subtotal, because "Total" also matched the end of "Sous-total". The supplier
  could be any text after "de" or "from", even inside a word: "Imprimerie Lavande inc." gave "inc.".
  The supplier now needs a label ("Fournisseur :", "Supplier:", "De :"…), otherwise the field stays
  empty. In English, "1,234.56" was cut to "1,23", and "Invoice #:" and "Invoice Number:" were not
  recognized; "Date d'émission" is now read as the invoice date. Checked on four demo invoices from
  Quebec: the number, the total, the invoice date and the due date are right on all four. The
  patterns are stored in the workflow action: run `finance_init` again after updating the app.

- **Q&A: answers shown formatted.** The language models answer in Markdown, and the history of a
  document showed the `**`, the dashes and the numbers as raw text, all on one line. Bold, italic,
  code, headings, lists and tables are now displayed formatted, also for the answers already saved.
  The text is escaped first, so an answer cannot inject HTML. Checked on two DeepSeek answers.

- **French: 1,368 missing translations added.** The French catalogs of Mayan EDMS left 1,368 texts
  in English in 60 apps, such as "Sort by column", "Do not expand", "Active state" or "Search
  results for:", and many help texts of the settings, tasks, sequences and searches. Each one was
  checked against the existing French terms (classeur, type de document, flux de travail…) and
  keeps its placeholders. The existing translations are unchanged.

- **Workflows and approvals: no more "None".** The log entry created by the launch of a workflow has
  neither user, origin state nor transition, and these columns showed the raw value `None`, in the
  workflows of a document and in the detail of a workflow. An approval request without a deadline or
  made by the system showed it too, like a transition approver without an escalation delay. These
  empty values now show "—".

- **French: the "Required" column and the approval comments.** The metadata of a document showed a
  column "Is required" in English. When an approval moved a workflow, the comment of the step,
  "Approved via approval workflow", stayed in English, like the other comments written by Approvals
  and four of its task names: their French translations had been dropped from the catalog, because
  the extraction of the messages did not see them. They are now in French.

---

## November 5, 2026

- **Separate containers work like the all-in-one container.** With the `multi_container` profile,
  the `celery_beat` service restarted in a loop (`run_beat: not found`) and no periodic task ran. In
  a separate container, the `MAYAN_WORKER_X_*` variables were ignored: each worker took every
  processor, with no memory or task limit and a nice level of 0. Mayan EDMS 4.12.1 removed the files
  of its image from its repository, and they had been recreated here from an earlier version. They
  now do what those of the `mayanedms/mayanedms:s4.12` image do. Checked with the `multi_container`
  profile: the 6 workers have their limits, each of the 40 queues has one consumer, the periodic
  tasks run and documents are converted. An option given to the command of a service takes
  precedence over the variable.
- **`MAYAN_ALLOWED_HOSTS` and `MAYAN_GUNICORN_BIND_CONTAINER_IP_ONLY` work.** `docker/.env` documents
  them, but the first was overwritten and the second had no effect. Checked: an allowed host name
  gets 200 and another one 400, and Gunicorn only listens on the address of the container.
- **The health check works with these two options.** It asked `127.0.0.1` for the home page, which
  they refuse, and the check failed although the site worked. It now asks the
  address of the container for the login page, and accepts any answer below 500.
- **Smaller fixes in the image.** The log levels follow `MAYAN_LOGGING_LEVEL`, the frontend container
  uses the bind address and the log level, the directory of large uploads is created on the media
  volume, and `wait.py` reads the port of the database. The `run_tests` command is removed: its script
  is not in this image.
- **The workflow checks separate containers.** It also starts the `multi_container` profile and checks
  Celery Beat, the limits of the workers and the consumers of the queues.
- **Memory limit of the workers in the right unit.** The list of the workers showed `488.3 KB` for a
  limit of 488.3 MB: the value is in KiB and was displayed as bytes. Checked on a running instance.
- **`manage.py test` works in a clone.** It stopped with `ModuleNotFoundError`, because Mayan EDMS
  4.12.1 removed `mayan.apps.testing` from its repository. The command given in the README could not
  work either: the installed package has no tests.

---

## November 4, 2026

- **12-bit JPEG in DICOM files.** The *JPEG Extended* images with samples of 12 bits gave a page
  of attributes: Pillow and the GDCM plugin of pydicom refuse these samples, and the remaining
  plugin, `pylibjpeg-libjpeg`, is under the GPLv3. They are now read by a decoder of this project, in
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
- **No more `extract-msg`.** This package and `pcodedmp`, which it brought, are under the GPLv3. Outlook `.msg` files are
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

## November 3, 2026

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

## October 30, 2026

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

Earlier changes are only in the Git history.
