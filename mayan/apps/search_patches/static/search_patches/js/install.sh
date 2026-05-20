#!/bin/bash

DEST=/opt/egyptian/media/static/search_patches/js

# Fichiers de langue — copie simple, pas de manifest requis
for f in search_help.fr.js search_help.en.js search_help.es.js search_help.pt.js; do
  cp $f $DEST/$f
done
#cp head.html /opt/mayan-edms/lib/python3.13/site-packages/mayan/apps/dynamic_search/templates/dynamic_search/app
# search_help.js — manifest requis (déjà en place depuis la session précédente)
cp search_help.js $DEST/search_help.js
python3 << 'PYEOF'
import json, hashlib, shutil, os
src = '/opt/egyptian/media/static/search_patches/js/search_help.js'
manifest_path = '/opt/egyptian/media/static/staticfiles.json'
with open(src, 'rb') as f: content = f.read()
md5 = hashlib.md5(content).hexdigest()[:12]
with open(manifest_path) as f: manifest = json.load(f)
old = manifest['paths'].get('search_patches/js/search_help.js', '')
if old:
    p = '/opt/egyptian/media/static/' + old
    if os.path.exists(p): os.remove(p)
hashed = 'search_patches/js/search_help.{}.js'.format(md5)
shutil.copy2(src, '/opt/egyptian/media/static/' + hashed)
manifest['paths']['search_patches/js/search_help.js'] = hashed
with open(manifest_path, 'w') as f: json.dump(manifest, f)
print('OK —', hashed)
PYEOF
