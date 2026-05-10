# Egyptian — Mayan EDMS 4.x Fork

**Egyptian** is a production fork of [Mayan EDMS](https://gitlab.com/mayan-edms/mayan-edms) 4.x,
maintained by [mypalace.ca](https://mayan.mypalace.ca).
It ships bug fixes that have not yet been merged upstream, and serves as the base for a set of
commercial extensions built and used in production.

---

## Free bug fixes included in this fork

All fixes below are available to anyone who runs this fork, at no cost.

### Security and core fixes

#### OIDC

- Fix JavaScript injection in logout view
- Add cross-origin SSO logout support
- Add missing OIDC parameters (token expiry, logout endpoint, id token storage)
- Add HTTP timeout on OIDC discovery requests
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

- Fix intermediate file cache race condition
- Fix file cache eviction order (oldest first)
- Fix Redis lock blocking with timeout (30s)
- Fix OCR task FileNotFoundError retry
- Fix GPG signature_id from sig_info fallback
- Fix default search model to DocumentFilePage
- Fix setting migrations value preservation
- Fix appearance checkbox label attribute

---

## Paid extensions

The following applications extend Mayan EDMS with AI, workflow, and productivity features.
Access is granted per GitHub account via private repository.
All prices are in USD.

| Application | What it does | Price |
|---|---|---|
| [Approvals](https://mayan.mypalace.ca/apps/approvals/) | Document approval workflows with SLA tracking and notifications | from $999 / yr |
| [Workflow UI](https://mayan.mypalace.ca/apps/workflow-ui/) | Visual drag-and-drop workflow editor — no code required | $499 one-time |
| [Document Q&A](https://mayan.mypalace.ca/apps/document-qa/) | Ask your documents in natural language — answers with citations | $299 one-time |
| [Document Embedding](https://mayan.mypalace.ca/apps/document-embedding/) | Semantic search — find documents even when you don't know the exact words | $299 one-time |
| [Document NER](https://mayan.mypalace.ca/apps/document-ner/) | Automatically extract persons, organizations, and dates from your documents | $249 one-time |
| [Autotag](https://mayan.mypalace.ca/apps/autotag/) | Zero-shot automatic tagging using your existing Mayan tags | $199 one-time |
| [Activity Report](https://mayan.mypalace.ca/apps/activity-report/) | Exportable audit reports — who did what, when, on which document | $149 one-time |
| [Barcode Extract](https://mayan.mypalace.ca/apps/barcode-extract/) | Automatically detect and index all barcodes found in your documents | $149 one-time |
| [Document Health](https://mayan.mypalace.ca/apps/document-health/) | Quality dashboard — identify and fix problematic documents | $149 one-time |
| [Version Diff](https://mayan.mypalace.ca/apps/version-diff/) | Compare two document versions with highlighted differences in one click | $149 one-time |
| [OCR Viewer](https://mayan.mypalace.ca/apps/ocr-viewer/) | Select and copy text directly from scanned document pages | $99 one-time |

Browse all apps and purchase access: **[mayan.mypalace.ca](https://mayan.mypalace.ca)**

---

## Community forum

Questions, feedback, and discussion about Egyptian and its extensions:

**[mayan.mypalace.ca/forum/](https://mayan.mypalace.ca/forum/)**

---

## About Mayan EDMS

Mayan EDMS is a free, open source document management system written in Python / Django.
It provides document storage, OCR, workflows, metadata, access control, and much more,
and is designed for self-hosted enterprise deployments.

- **Source code**: [gitlab.com/mayan-edms/mayan-edms](https://gitlab.com/mayan-edms/mayan-edms)
- **Documentation**: [docs.mayan-edms.com](https://docs.mayan-edms.com)
- **License**: Apache 2.0

Egyptian tracks the Mayan EDMS 4.x branch. Changes in this fork that are generic enough
are submitted upstream when possible.
