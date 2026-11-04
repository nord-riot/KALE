#!/usr/bin/env python3
"""Regenerate the complete offline drug catalog after medical source updates."""
from pathlib import Path
import json
import sqlite3

root=Path(__file__).resolve().parents[1]
db=root/'data/kale.db'
out=root/'web/assets/medicines-offline.json'
with sqlite3.connect(db) as c:
    c.row_factory=sqlite3.Row
    medicines=[dict(r) for r in c.execute('SELECT * FROM medicines ORDER BY name')]
for m in medicines:m.pop('search_text',None)
out.write_text(json.dumps({'format':1,'version':'0.9.0','medicines':medicines},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'{len(medicines)} ilaç; çevrimdışı paket: {out.stat().st_size} byte')
print('Önemli: Güncellemeden sonra web/sw.js CACHE sürümünü artırın, istemciler eski paketi tutmasın.')
