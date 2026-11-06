"""Build an image-preview artifact: python3 build_images.py image-template.html manifest.json out.html
Each item needs "file" (local image path, e.g. a browser screenshot saved under tool-results) or "img" (data URI).
Images are resized to <=1200px wide and embedded as JPEG data URIs (the artifact CSP blocks external images)."""
import base64, io, json, sys
from PIL import Image
tpl, man, out = sys.argv[1:4]
m = json.load(open(man))
for g in m['groups']:
    for it in g['items']:
        if 'file' in it:
            im = Image.open(it.pop('file')).convert('RGB')
            if im.width > 1200: im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
            b = io.BytesIO(); im.save(b, 'JPEG', quality=82, optimize=True)
            it['img'] = 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
html = open(tpl).read().replace('__TITLE__', m['title']).replace('__CONFIG__', json.dumps(m, ensure_ascii=False))
open(out, 'w').write(html); print(out, f'{len(html)/1e6:.1f} MB')
 