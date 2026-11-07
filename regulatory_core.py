"""KALE regulatory sidecar: source-attributed product records, not medical advice.

Never modifies or rebuilds data/kale.db, the user-edited medicines catalog,
or a physician's review. Foreign-market records are NOT product equivalence.
"""
from __future__ import annotations
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "regulatory.sqlite3"
AGENCIES = {
    "FDA": ("ABD", "https://open.fda.gov/apis/drug/label/"),
    "TITCK": ("Türkiye", "https://titck.gov.tr/kubkt"),
    "EMA": ("AB/AEA", "https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/data-medicines-iso-idmp-standards-post-authorisation/public-data-article-57-database"),
    "MHRA": ("Birleşik Krallık", "https://products.mhra.gov.uk/"),
    "PMDA": ("Japonya", "https://www.pmda.go.jp/english/search_index.html"),
    "HEALTH_CANADA": ("Kanada", "https://health-products.canada.ca/api/drug/"),
    "TGA": ("Avustralya", "https://www.tga.gov.au/products/regulations-all-products/about-australian-register-therapeutic-goods-artg"),
    "SFDA": ("Suudi Arabistan", "https://sfda.gov.sa/en/eservices/19531"),
    "WHO": ("Uluslararası ön yeterlilik", "https://extranet.who.int/prequal/medicines/prequalified-lists-medicines"),
}
DOMAINS = {
    "FDA": ("fda.gov", "dailymed.nlm.nih.gov"),
    "TITCK": ("titck.gov.tr",),
    "EMA": ("ema.europa.eu",),
    "MHRA": ("mhra.gov.uk", "products.mhra.gov.uk"),
    "PMDA": ("pmda.go.jp",),
    "HEALTH_CANADA": ("canada.ca", "health-products.canada.ca"),
    "TGA": ("tga.gov.au",),
    "SFDA": ("sfda.gov.sa",),
    "WHO": ("who.int",),
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    regulator TEXT NOT NULL,
    source_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    active_substance TEXT NOT NULL DEFAULT '',
    dosage_form TEXT NOT NULL DEFAULT '',
    product_status TEXT NOT NULL DEFAULT 'DURUM BELİRTİLMEDİ',
    market TEXT NOT NULL DEFAULT '',
    source_updated TEXT NOT NULL DEFAULT '',
    imported_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT '',
    sections_json TEXT NOT NULL DEFAULT '{}',
    name_search TEXT NOT NULL,
    ingredients_search TEXT NOT NULL,
    PRIMARY KEY (regulator,source_id)
);
CREATE INDEX IF NOT EXISTS idx_reg_name ON products(name_search);
CREATE INDEX IF NOT EXISTS idx_reg_ing ON products(ingredients_search);
CREATE TABLE IF NOT EXISTS sync_runs (
    regulator TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    records_seen INTEGER NOT NULL,
    result TEXT NOT NULL
);
"""
MAX_FIELD = 14000
MAX_SOURCE_FIELDS = 24
MAX_SECTIONS_BYTES = 90000


def normalize(value):
    value = str(value or "").replace("ı", "i").replace("İ", "I")
    value = unicodedata.normalize("NFKD", value).lower()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def official_url(regulator, uri):
    allowed = DOMAINS.get(regulator, ())
    try:
        u = urlparse(str(uri or ""))
    except ValueError:
        return ""
    try:
        invalid_port = u.port not in (None,443)
    except ValueError:
        return ""
    if u.scheme != "https" or u.username or u.password or invalid_port:
        return ""
    host = (u.hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in allowed):
        return ""
    return u.geturl()[:1500]


def open_writer(db=DB):
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db), timeout=30)
    conn.executescript(SCHEMA)
    return conn


def write_record(conn, *, regulator, source_id, name, ingredients="", form="",
                 status="", market="", updated="", url="", kind="", sections=None,
                 imported_at=""):
    if regulator not in AGENCIES:
        raise ValueError("Unknown regulator")
    name = str(name or "").strip()[:300]
    source_id = str(source_id or "").strip()[:180]
    if not name or not source_id:
        return False
    src = official_url(regulator, url) or AGENCIES[regulator][1]
    sections = sections if isinstance(sections, dict) else {}
    safe = {}
    for key, val in list(sections.items())[:MAX_SOURCE_FIELDS]:
        if not re.fullmatch("[a-z][a-z_]{1,60}", str(key)):
            continue
        if isinstance(val, list):
            val = "\n\n".join(str(x) for x in val[:30])
        if not isinstance(val, str):
            continue
        safe[key] = val[:MAX_FIELD]
    packed = json.dumps(safe, ensure_ascii=False)
    if len(packed.encode("utf-8")) > MAX_SECTIONS_BYTES:
        safe = {"note": "Kaynak bölümü boyut sınırına takıldı; resmî bağlantıyı aç."}
        packed = json.dumps(safe, ensure_ascii=False)
    ingredients = str(ingredients or "").strip()[:500]
    conn.execute("""INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
       ON CONFLICT(regulator,source_id) DO UPDATE SET
       product_name=excluded.product_name, active_substance=excluded.active_substance,
       dosage_form=excluded.dosage_form, product_status=excluded.product_status,
       market=excluded.market, source_updated=excluded.source_updated,
       imported_at=excluded.imported_at, source_url=excluded.source_url,
       source_type=excluded.source_type, sections_json=excluded.sections_json,
       name_search=excluded.name_search, ingredients_search=excluded.ingredients_search
    """, (regulator, source_id, name, ingredients, str(form or "")[:160],
          str(status or "DURUM BELİRTİLMEDİ")[:160],
          str(market or AGENCIES[regulator][0])[:120],
          str(updated or "")[:60], imported_at, src, str(kind or "")[:80],
          packed, normalize(name), normalize(ingredients)))
    return True


def read_conn():
    if not DB.is_file():
        return None
    try:
        conn = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True, timeout=2)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        return None


def stats():
    out = {key: {"country": label, "portal": url, "count": 0, "last_sync": None}
           for key, (label, url) in AGENCIES.items()}
    con = read_conn()
    if con is None:
        return {"installed": False, "total": 0, "regulators": out}
    try:
        total = 0
        for row in con.execute("SELECT regulator,COUNT(*) AS n FROM products GROUP BY regulator"):
            if row["regulator"] in out:
                out[row["regulator"]]["count"] = row["n"]
                total += row["n"]
        for row in con.execute("SELECT regulator,synced_at,result FROM sync_runs"):
            if row["regulator"] in out:
                out[row["regulator"]]["last_sync"] = row["synced_at"]
                out[row["regulator"]]["sync_status"] = row["result"]
        return {"installed": True, "total": total, "regulators": out,
                "disclaimer": "Arama eşleşmesi, ürün eşdeğerliği veya tıbbi onay değildir."}
    except sqlite3.Error:
        return {"installed": False, "total": 0, "regulators": out}
    finally:
        con.close()


def search_products(query, regulator="", limit=15):
    term = normalize(query)
    if len(term) < 3:
        return []
    if regulator and regulator not in AGENCIES:
        return []
    con = read_conn()
    if con is None:
        return []
    # Exact ingredient first. Other results are only unverified search candidates.
    term = term[:100]
    esc = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    sql = """SELECT regulator,source_id,product_name,active_substance,dosage_form,
             product_status,market,source_updated,source_url,source_type,
             CASE WHEN ingredients_search=? OR name_search=? THEN 0 ELSE 1 END AS rank
             FROM products WHERE (ingredients_search LIKE ? ESCAPE '\\'
                    OR name_search LIKE ? ESCAPE '\\')"""
    args = [term,term,"%" + esc + "%","%" + esc + "%"]
    if regulator:
        sql += " AND regulator=?"
        args.append(regulator)
    sql += " ORDER BY rank,product_name COLLATE NOCASE LIMIT ?"
    args.append(max(1,min(int(limit),30)))
    try:
        return [dict(x) for x in con.execute(sql,args)]
    except sqlite3.Error:
        return []
    finally:
        con.close()


def get_product(regulator, source_id):
    if regulator not in AGENCIES or len(source_id) > 180:
        return None
    con = read_conn()
    if con is None:
        return None
    try:
        rec = con.execute("SELECT * FROM products WHERE regulator=? AND source_id=?",
                          (regulator,source_id)).fetchone()
        if rec is None:
            return None
        out = dict(rec)
        out.pop("name_search",None)
        out.pop("ingredients_search",None)
        out["sections"] = json.loads(out.pop("sections_json"))
        out["disclaimer"] = "Resmî kaynak kaydıdır; KALE veya Türkiye ruhsatı onayı değildir."
        return out
    except (sqlite3.Error,ValueError):
        return None
    finally:
        con.close()
