#!/usr/bin/env python3
"""Reproducible compilation of editorial JSON into a read-only SQLite catalog."""
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data' / 'content.json'
DEST = ROOT / 'data' / 'kale.db'


def normalize(value):
    txt = str(value or '').replace('İ','I').replace('ı','i').lower()
    return ''.join(ch for ch in unicodedata.normalize('NFKD', txt) if not unicodedata.combining(ch))


def build():
    catalog = json.loads(SRC.read_text(encoding='utf-8'))
    entries = catalog['entries']
    ids = [x['id'] for x in entries]
    assert len(ids) == len(set(ids)) and len(entries) >= 37
    for x in entries:
        for key in ('id','category','title','body','tags','review_status','sources'):
            assert key in x, (x.get('id'), key)
        assert isinstance(x['id'], int) and x['id'] > 0
        assert isinstance(x['sources'], list)
    temp = DEST.with_suffix('.tmp')
    if temp.exists(): temp.unlink()
    conn = sqlite3.connect(str(temp))
    try:
        conn.executescript('''
          CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE entries (
            id INTEGER PRIMARY KEY, category TEXT NOT NULL, title TEXT NOT NULL,
            body TEXT NOT NULL, tags TEXT NOT NULL, warning TEXT NOT NULL,
            diagram TEXT NOT NULL, review_status TEXT NOT NULL, last_reviewed TEXT,
            sources_json TEXT NOT NULL, regions_json TEXT NOT NULL,
            priority TEXT NOT NULL, origin TEXT NOT NULL, search_text TEXT NOT NULL
          );
          CREATE INDEX idx_entries_category ON entries(category);
        ''')
        for x in entries:
            conn.execute('''INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                x['id'],x['category'],x['title'],x['body'],x['tags'],x.get('warning',''),
                x.get('diagram',''),x['review_status'],x.get('last_reviewed'),
                json.dumps(x['sources'],ensure_ascii=False),json.dumps(x.get('regions',[]),ensure_ascii=False),
                x.get('priority','normal'),x.get('origin',''),normalize(' '.join((x['title'],x['category'],x['body'],x['tags'])))
            ))
        for k in ('version','build_date','title','notice','content_policy'):
            conn.execute('INSERT INTO metadata VALUES (?,?)', (k,json.dumps(catalog.get(k),ensure_ascii=False)))
        from medicines_core import initialize, seed, sourced_summaries
        initialize(conn)
        new_med=seed(conn)
        sourced_med=sourced_summaries(conn)
        # Legacy source summaries have unknown product-specific fields. Explicitly
        # indicate missing verification instead of inventing clinical details.
        placeholders={
          'pregnancy':'Gebelik, emzirme ve çocuklarda ilaca/ürüne özgü güvenlik bilgisi bu kayıtta henüz doğrulanmadı; güvenli kullanım çıkarımı yapılamaz.',
          'inactive_ingredients':'Marka/form bilgisi eksik: gerçek yardımcı maddeler ve alerjenler doğrulanmadı; ürün KÜB/KT ve ambalajına bakılmalı.',
          'storage':'Saklama sıcaklığı, soğuk zincir, nem/ışık ve son kullanma koşulları ürüne göre doğrulanmalı.'
        }
        for field,message in placeholders.items():
            conn.execute(f"UPDATE medicines SET {field}=? WHERE TRIM({field})='' OR {field} IS NULL",(message,))
        conn.commit()
        assert conn.execute('SELECT count(*) FROM medicines').fetchone()[0] >= new_med
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert conn.execute('SELECT count(*) FROM entries').fetchone()[0] == len(entries)
    finally:
        conn.close()
    temp.replace(DEST)
    with sqlite3.connect(str(DEST)) as check:
        total_medicines=check.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]
        explained=check.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%TASLAK%' OR review_status LIKE '%ÖZET%'").fetchone()[0]
    print(f'KALE DB OK: {len(entries)} rehber, {total_medicines} toplam ilaç adı, {explained} benzersiz Türkçe açıklama, {DEST.stat().st_size} bytes')

if __name__ == '__main__':
    build()
