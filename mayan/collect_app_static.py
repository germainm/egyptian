#!/usr/bin/env python3
"""
Collect static files for a single Egyptian / Mayan EDMS custom app.

Use this when the standard collectstatic command fails (known dev-build bug).
The script copies all files from <app_dir>/static/ to <media_dir>/static/,
creates the hashed copies, and updates staticfiles.json in place.

Usage:
    python collect_app_static.py <app_dir> <media_dir>

Example:
    python collect_app_static.py /opt/mayan-edms/lib/python3.13/site-packages/mayan/apps/workflow_ui \
                                 /opt/mayan-edms/media
"""

import argparse
import hashlib
import json
import os
import shutil
import sys


def md5_file(path):
    """Return first 12 hex chars of the MD5 of a file's content."""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:12]


def hashed_name(rel_path, hash_str):
    """foo/bar.js -> foo/bar.<hash>.js"""
    root, ext = os.path.splitext(rel_path)
    return f"{root}.{hash_str}{ext}"


def main():
    parser = argparse.ArgumentParser(
        description='Add a custom app\'s static files to staticfiles.json.'
    )
    parser.add_argument('app_dir',   help='App directory (must contain a static/ subdirectory)')
    parser.add_argument('media_dir', help='Mayan media directory (contains static/staticfiles.json)')
    args = parser.parse_args()

    app_dir   = os.path.abspath(args.app_dir)
    media_dir = os.path.abspath(args.media_dir)
    static_src = os.path.join(app_dir, 'static')
    static_dst = os.path.join(media_dir, 'static')
    manifest_path = os.path.join(static_dst, 'staticfiles.json')

    if not os.path.isdir(static_src):
        print(f"Error: no static/ directory found in {app_dir}", file=sys.stderr)
        sys.exit(1)

    # Load existing manifest (or start fresh)
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding='utf-8') as f:
            manifest = json.load(f)
        print(f"Loaded manifest: {manifest_path}")
    else:
        manifest = {'version': '1.1', 'paths': {}, 'hash': ''}
        print(f"No manifest found — will create: {manifest_path}")

    paths = manifest.setdefault('paths', {})
    added = 0

    for dirpath, _dirs, filenames in os.walk(static_src):
        for filename in sorted(filenames):
            src_file = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(src_file, static_src).replace(os.sep, '/')

            h = md5_file(src_file)
            hashed_rel = hashed_name(rel_path, h)

            # Copy original
            dst_orig = os.path.join(static_dst, rel_path)
            os.makedirs(os.path.dirname(dst_orig), exist_ok=True)
            shutil.copy2(src_file, dst_orig)

            # Copy hashed version
            dst_hashed = os.path.join(static_dst, hashed_rel)
            shutil.copy2(src_file, dst_hashed)

            paths[rel_path] = hashed_rel
            print(f"  {rel_path}  ->  {hashed_rel}")
            added += 1

    # Recompute manifest hash (same algorithm as Django ManifestStaticFilesStorage)
    manifest['hash'] = hashlib.md5(
        json.dumps(sorted(paths.items())).encode('utf-8')
    ).hexdigest()[:12]

    os.makedirs(static_dst, exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=None, separators=(', ', ': '))

    print(f"\n{added} file(s) added. Manifest hash: {manifest['hash']}")
    print(f"Manifest updated: {manifest_path}")


if __name__ == '__main__':
    main()
