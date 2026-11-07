#!/usr/bin/env python3
"""KALE: offline, read-only, sqlite-powered Turkish survival reference.
No user data storage, analytics, account system, or outbound requests.
"""
import json
import ipaddress
import shutil
import subprocess
import mimetypes
import os
import sqlite3
import sys
import socket
import io
import threading
from chat_core import CHAT, ChatError
from device_monitor import MONITOR
from routing import inspect_street_map,read_vector_tile,get_routing_status,calculate_route,RoutingError
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

mimetypes.add_type('application/manifest+json', '.webmanifest')
BASE = Path(__file__).resolve().parent
WEB = BASE / 'web'
DB = BASE / 'data' / 'kale.db'
REVIEWS_DB = BASE / 'data' / 'doctor_reviews.sqlite3'
MAP_DB = Path(os.environ.get('KALE_MAP_PATH', str(BASE / 'data' / 'maps' / 'turkiye.mbtiles')))
VERSION = '2.4.0'
PORT = int(os.environ.get('KALE_PORT','8090'))
HOST = os.environ.get('KALE_HOST','127.0.0.1')
ROUTE_SLOTS=threading.BoundedSemaphore(2)

# Same normalization as the database compiler, does not depend on system locale.
def normalize(value):
    from unicodedata import normalize as unorm, combining
    txt = str(value or '').replace('İ','I').replace('ı','i').lower()
    return ''.join(c for c in unorm('NFKD',txt) if not combining(c))


def connection():
    # Immutable read-only URI supports a read-only Docker filesystem and avoids journal writes.
    conn = sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1', uri=True, timeout=3)
    conn.row_factory = sqlite3.Row
    return conn


# Supplement-only handbook text. Does not modify DB rows or override a locally
# edited guide. Match both stable ID and exact title before appending.
GUIDE_EXPANSIONS_PATH = BASE / 'data' / 'guide-expansions.json'
def load_guide_expansions():
    try:
        with GUIDE_EXPANSIONS_PATH.open('r', encoding='utf-8') as source:
            payload=json.load(source)
        if payload.get('format')!='KALE-GUIDE-EXPANSIONS-1':
            return {}
        entries=payload.get('items', [])
        if not isinstance(entries,list) or len(entries)>1000:
            return {}
        return {item['id']:(item['title'],item['extra']) for item in entries
                if isinstance(item,dict) and isinstance(item.get('id'),int)
                and isinstance(item.get('title'),str) and isinstance(item.get('extra'),str)
                and 500<len(item['extra'])<20000}
    except (OSError,ValueError,TypeError,KeyError):
        return {}

GUIDE_EXPANSIONS=load_guide_expansions()

def parse_entry(row):
    d = dict(row)
    d.pop('search_text',None)
    d['sources'] = json.loads(d.pop('sources_json'))
    d['regions'] = json.loads(d.pop('regions_json'))
    supplement=GUIDE_EXPANSIONS.get(d.get('id'))
    if supplement and d.get('title')==supplement[0]:
        extra=supplement[1]
        # Keep the source DB text, including user edits, intact.
        # A distinct marker prevents duplicate insertions.
        if 'AYRINTILI KONU ANLATIMI — KALE' not in (d.get('body') or ''):
            d['body']=(d.get('body') or '').rstrip()+'\\n\\nAYRINTILI KONU ANLATIMI — KALE\\n'+extra
    return d


def metadata(conn):
    return {r['key']: json.loads(r['value']) for r in conn.execute('SELECT key,value FROM metadata')}


def catalog():
    with connection() as conn:
        d=metadata(conn)
        d['entries'] = [parse_entry(x) for x in conn.execute('SELECT * FROM entries ORDER BY id')]
        return d


def search(query, category, limit, offset):
    terms = normalize(query).split()[:8]
    sql = ' FROM entries WHERE 1=1'
    params=[]
    if category and category != 'TÜMÜ':
        sql += ' AND category=?'
        params.append(category)
    for term in terms:
        escaped = term.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        sql += " AND search_text LIKE ? ESCAPE '\\'"
        params.append('%'+escaped+'%')
    with connection() as conn:
        total=conn.execute('SELECT COUNT(*)'+sql,params).fetchone()[0]
        rows=conn.execute('SELECT *'+sql+' ORDER BY id LIMIT ? OFFSET ?',params+[limit,offset]).fetchall()
        return {'entries':[parse_entry(r) for r in rows],'total':total,'limit':limit,'offset':offset}


def review_connection():
    # No web mutation path. Review records are imported through a separate, local CLI.
    if not REVIEWS_DB.is_file():return None
    try:
        c=sqlite3.connect('file:'+str(REVIEWS_DB)+'?mode=ro',uri=True,timeout=2)
        c.row_factory=sqlite3.Row
        return c
    except sqlite3.Error:return None


def review_stats():
    default={'reviewed':0,'approved_by_reviewer':0,'needs_correction':0,'rejected':0,
             'catalog_status':'Klinik veriler editoryal taslaktır; onay kaydı kişisel beyana dayanır.'}
    c=review_connection()
    if c is None:return default
    try:
        with c:
            rows=c.execute('SELECT decision,COUNT(*) as n FROM doctor_reviews GROUP BY decision').fetchall()
        counts={r['decision']:r['n'] for r in rows}
        default.update(reviewed=sum(counts.values()),approved_by_reviewer=counts.get('ONAYLA',0),
                       needs_correction=counts.get('DÜZELT',0),rejected=counts.get('REDDET',0))
    except sqlite3.Error:pass
    finally:c.close()
    return default


def public_review(med_id):
    c=review_connection()
    if c is None:return {'review_record':'YOK','verified_clinical_safety':False}
    try:
        with c:
            row=c.execute('SELECT decision,reviewed_on FROM doctor_reviews WHERE medicine_id=?',(med_id,)).fetchone()
        if row is None:return {'review_record':'YOK','verified_clinical_safety':False}
        return {'review_record':'İŞLENDİ','decision':row['decision'],
                'reviewed_on':row['reviewed_on'],'verified_clinical_safety':False,
                'note':'Excel içe aktarım beyanıdır; ilaç güvenliğine ilişkin bağımsız doğrulama değildir.'}
    except sqlite3.Error:return {'review_record':'ERİŞİLEMİYOR','verified_clinical_safety':False}
    finally:c.close()


def map_details(map_id="turkiye"):
    """Inspect an optional LOCAL raster MBTiles archive (no external requests)."""
    selected=get_map_path(map_id)
    if selected is None or not selected.is_file():
        return {'installed':False,'message':'Raster MBTiles yüklenmedi. Harita görüntüsü için yerel dosya gerekir.'}
    try:
        with sqlite3.connect('file:'+str(selected)+'?mode=ro&immutable=1',uri=True,timeout=2) as c:
            values=dict(c.execute('SELECT name,value FROM metadata'))
            fmt=values.get('format','').lower()
            if fmt not in ('png','jpg','jpeg','webp'):
                return {'installed':False,'message':'Yalnız raster PNG/JPEG/WebP MBTiles desteklenir. Vektör haritalar desteklenmez.'}
            row=c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiles'").fetchone()
            if not row: return {'installed':False,'message':'MBTiles tiles tablosu yok.'}
            return {'installed':True,'name':values.get('name','Yerel raster harita')[:100],
                    'format':fmt,'minzoom':int(values.get('minzoom','0')),
                    'maxzoom':int(values.get('maxzoom','18')),
                    'bounds':values.get('bounds',''),'size_bytes':selected.stat().st_size,'id':map_id}
    except (sqlite3.Error,ValueError,OSError):
        return {'installed':False,'message':'MBTiles dosyası okunamadı veya bozuk.'}


def read_map_tile(z,x,y,map_id="turkiye"):
    """XYZ client y => TMS MBTiles row; no path/file interpolation."""
    if not map_details(map_id).get('installed'):return None
    if not (0<=z<=18 and 0<=x<2**z and 0<=y<2**z):return None
    tms_row=2**z-1-y
    try:
        with sqlite3.connect('file:'+str(get_map_path(map_id))+'?mode=ro&immutable=1',uri=True,timeout=2) as conn:
            row=conn.execute('SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?',
                             (z,x,tms_row)).fetchone()
        if not row:return None
        blob=bytes(row[0])
        if len(blob)>2_000_000:return None
        if blob.startswith(b'\x89PNG\r\n\x1a\n'):mime='image/png'
        elif blob.startswith(b'\xff\xd8\xff'):mime='image/jpeg'
        elif blob.startswith(b'RIFF') and blob[8:12]==b'WEBP':mime='image/webp'
        else:return None
        return mime,blob
    except (sqlite3.Error,OSError):return None


def gps_from_termux(client_host, runner=subprocess.run, finder=shutil.which):
    """Explicit, one-shot GNSS request. Never exposes GPS to non-loopback clients."""
    try:
        if not ipaddress.ip_address(client_host).is_loopback:
            return {'error':'GPS sadece telefondaki 127.0.0.1 bağlantısına açıktır.'},403
    except ValueError:
        return {'error':'Yerel istemci gerekli.'},403
    cmd=finder('termux-location')
    if not cmd:
        return {'error':'Termux:API kurulu değil. Tarayıcı konumunu dene veya F-Droid Termux:API ve pkg install termux-api yükle.'},503
    try:
        result=runner([cmd,'-p','gps','-r','once'],capture_output=True,text=True,timeout=18,check=False)
        if result.returncode != 0:
            return {'error':'Termux GPS yanıt vermedi. Konum iznini, açık gökyüzünü ve Android GPS ayarını kontrol et.'},503
        obj=json.loads(result.stdout)
        lat=float(obj['latitude']); lon=float(obj['longitude'])
        accuracy=float(obj.get('accuracy',0))
        if not (-85<=lat<=85 and -180<=lon<=180 and 0<=accuracy<=100000 and all(__import__('math').isfinite(x) for x in (lat,lon,accuracy))):
            raise ValueError('Geçersiz GNSS koordinatı')
        return {'latitude':lat,'longitude':lon,'accuracy':accuracy,'provider':'Termux GPS (tek ölçüm)','cached':False},200
    except (subprocess.TimeoutExpired, OSError, ValueError, KeyError, TypeError):
        return {'error':'GPS ölçümü alınamadı. Konum iznini ve GNSS sinyalini kontrol et.'},503


def lan_addresses():
    """Best effort LAN address display; never performs an external network request."""
    found=set()
    try:
        names=socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET)
        for row in names:
            found.add(row[4][0])
    except OSError:pass
    try:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:
            sock.connect(('192.0.2.1',9))  # UDP connect sets local source, sends no packet.
            found.add(sock.getsockname()[0])
        finally:sock.close()
    except OSError:pass
    return sorted(addr for addr in found if ipaddress.ip_address(addr).is_private and not ipaddress.ip_address(addr).is_loopback)


def admin_allowed(remote, host):
    """Only physical loopback socket peer + literal localhost Host; never X-Forwarded-For.

    Blocks remote Wi-Fi users from the local device management page/API and avoids
    DNS-rebinding via attacker-controlled Host headers.
    """
    try:
        if not ipaddress.ip_address(remote).is_loopback:return False
    except ValueError:return False
    return host in (f'127.0.0.1:{PORT}',f'localhost:{PORT}',f'[::1]:{PORT}')


def local_maps():
    """Allow only known map filenames. Other MBTiles files remain private."""
    return {'turkiye':MAP_DB,'ege':BASE/'data/maps/ege.mbtiles'}


def get_map_path(map_id):
    return local_maps().get(map_id)


def network_info():
    addresses=lan_addresses()
    return {'addresses':addresses,'port':PORT,'version':VERSION,
            'urls':[f'http://{addr}:{PORT}/' for addr in addresses],
            'localhost':f'http://127.0.0.1:{PORT}/',
            'note':'LAN erişimi için cihazlar aynı Wi-Fi/hotspot ağında ve istemci izolasyonu kapalı olmalıdır. Android rootsuz 80 portu dinlenemez.'}


class Handler(SimpleHTTPRequestHandler):
    server_version = 'KALE/2.3.0'
    sys_version = ''
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(WEB),**kwargs)

    def log_message(self, fmt,*args):
        # Never log URL paths, search terms, query parameters, or symptom text.
        if os.environ.get('KALE_ACCESS_LOG','0')=='1':
            print(f'{self.log_date_time_string()} | KALE request',flush=True)

    def end_headers(self):
        for k,v in (
            ('X-Content-Type-Options','nosniff'),('X-Frame-Options','DENY'),
            ('Referrer-Policy','no-referrer'),('Cross-Origin-Resource-Policy','same-origin'),
            ('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; worker-src 'self'; manifest-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'"),
            ('Permissions-Policy','camera=(), microphone=(), geolocation=(self)'),
        ): self.send_header(k,v)
        super().end_headers()

    def json_response(self,obj,code=200):
        body=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path=urlsplit(self.path).path
        if path=='/api/device/eco':
            if not admin_allowed(self.client_address[0],self.headers.get('Host','')):
                return self.json_response({'error':'Yalnız cihaz üzerindeki localhost erişebilir.'},403)
            if self.headers.get('Origin')!=f'http://{self.headers.get("Host","")}' or self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
                return self.json_response({'error':'Yerel uygulama üzerinden JSON gerekli.'},403)
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=256:return self.json_response({'error':'İstek boyutu geçersiz.'},413)
                payload=json.loads(self.rfile.read(n))
                if not isinstance(payload,dict):raise ValueError('Invalid')
                mode=MONITOR.set_eco(payload.get('enabled'))
                return self.json_response({'enabled':mode})
            except (TypeError,ValueError):return self.json_response({'error':'Tasarruf ayarı true/false olmalı.'},400)
        if not path.startswith('/api/chat/') or path not in ('/api/chat/join','/api/chat/poll','/api/chat/send','/api/chat/leave'):
            return self.json_response({'error':'İşlem desteklenmiyor.'},404)
        # Same-origin required for browser clients; do not let another webpage impersonate users.
        origin=self.headers.get('Origin','')
        if not origin or origin!=f'http://{self.headers.get("Host","")}' or self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
            return self.json_response({'error':'Aynı site üzerinden JSON isteği gerekli.'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=4096:return self.json_response({'error':'İstek çok büyük veya boş.'},413)
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict):raise ChatError('Geçersiz istek.')
            token=payload.get('token')
            if path=='/api/chat/join':return self.json_response(CHAT.join(payload.get('name')))
            if path=='/api/chat/poll':
                raw=payload.get('after',0)
                if type(raw) is not int or raw<0 or raw>2**53:raise ChatError('Geçersiz mesaj sırası.')
                return self.json_response(CHAT.snapshot(token,raw))
            if path=='/api/chat/send':return self.json_response(CHAT.send(token,payload.get('text')))
            if path=='/api/chat/leave':return self.json_response(CHAT.leave(token))
        except ChatError as e:return self.json_response({'error':str(e)},e.status)
        except (ValueError,TypeError,UnicodeError):return self.json_response({'error':'Geçersiz JSON.'},400)

    def send_svg(self,content):
        body=content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type','image/svg+xml; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        return self.wfile.write(body)

    def medicine_query(self, url):
        q=parse_qs(url.query,keep_blank_values=True)
        raw=q.get('q',[''])[0][:100]
        terms=normalize(raw).split()[:6]
        try:
            limit=max(1,min(100,int(q.get('limit',['40'])[0])))
            offset=max(0,min(1000000,int(q.get('offset',['0'])[0])))
        except ValueError:return self.json_response({'error':'Geçersiz sayfa parametresi'},400)
        sourced=q.get('sourced',['0'])[0]=='1'
        wheres=[];params=[]
        if sourced:wheres.append("review_status != 'SADECE İSİM DİZİNİ'")
        for term in terms:
            escaped=term.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
            wheres.append("search_text LIKE ? ESCAPE '\\'")
            params.append('%'+escaped+'%')
        where=' WHERE '+' AND '.join(wheres) if wheres else ''
        with connection() as conn:
            n=conn.execute('SELECT COUNT(*) FROM medicines'+where,params).fetchone()[0]
            fields='id,name,generic_name,brand_names,active_ingredients,category,source,source_updated,locale,review_status'
            rows=conn.execute('SELECT '+fields+' FROM medicines'+where+" ORDER BY CASE WHEN review_status LIKE '%TASLAK%' OR review_status LIKE '%ÖZET%' THEN 0 WHEN source LIKE 'openFDA%' THEN 1 ELSE 2 END, name COLLATE NOCASE, id LIMIT ? OFFSET ?",params+[limit,offset]).fetchall()
        return self.json_response({'total':n,'offset':offset,'limit':limit,'items':[dict(x) for x in rows]})

    def do_GET(self):
        url=urlsplit(self.path)
        path=url.path
        try:
            if path in ('/api/device/status','/yonetim.html'):
                if not admin_allowed(self.client_address[0],self.headers.get('Host','')):
                    return self.json_response({'error':'Bu sayfa sadece KALE cihazındaki localhost adresinden açılabilir.'},403)
                if path=='/api/device/status':
                    with CHAT.lock:
                        CHAT._purge(__import__('time').monotonic())
                        online=len(CHAT.sessions)
                    return self.json_response(MONITOR.snapshot(chat_users=online,status_path=os.environ.get('KALE_SUPERVISOR_STATUS')))
            if path=='/api/gps/once':
                payload,code=gps_from_termux(self.client_address[0])
                return self.json_response(payload,code)
            if path=='/api/network':
                return self.json_response(network_info())
            if path=='/api/network/qr.svg':
                raw=parse_qs(url.query).get('ip',[''])[0]
                if raw not in lan_addresses():return self.json_response({'error':'Bu adres sunucuya ait değil.'},403)
                try:import qrcode
                except ImportError:return self.json_response({'error':'QR modülü yüklü değil; bağlantıyı metin olarak paylaş.'},503)
                qr=qrcode.QRCode(border=3,box_size=6,error_correction=qrcode.constants.ERROR_CORRECT_M)
                qr.add_data(f'http://{raw}:{PORT}/sohbet.html');qr.make(fit=True)
                matr=qr.get_matrix();count=len(matr);pieces=[]
                for row,line in enumerate(matr):
                    for col,enabled in enumerate(line):
                        if enabled:pieces.append(f'<rect x="{col}" y="{row}" width="1" height="1"/>')
                return self.send_svg(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {count} {count}" shape-rendering="crispEdges"><rect width="100%" height="100%" fill="white"/><g fill="#102c29">'+''.join(pieces)+'</g></svg>')
            if path=='/api/street/status':
                return self.json_response(inspect_street_map())
            if path=='/api/route/status':
                return self.json_response(get_routing_status(probe=True))
            if path=='/api/route':
                q=parse_qs(url.query)
                try:
                    vals=[float(q[key][0]) for key in ('start_lat','start_lon','end_lat','end_lon')]
                    mode=q.get('mode',['walk'])[0]
                    if not ROUTE_SLOTS.acquire(blocking=False):
                        return self.json_response({'error':'Rota motoru meşgul; tekrar dene.'},429)
                    try:result=calculate_route(*vals,mode=mode)
                    finally:ROUTE_SLOTS.release()
                    return self.json_response(result)
                except RoutingError as e:
                    return self.json_response({'error':str(e)},e.status)
                except (KeyError,IndexError,ValueError) as e:
                    return self.json_response({'error':'Geçersiz rota koordinatları veya türü.'},400)
            if path.startswith('/api/street/tiles/'):
                parts=path.split('/')
                if len(parts)!=7 or not all(v.isdecimal() for v in parts[4:]):
                    return self.json_response({'error':'Geçersiz vektör karo adresi'},400)
                z,x,y=map(int,parts[4:]);tile=read_vector_tile(z,x,y)
                if tile is None:return self.send_error(404,'Sokak vektör karosu yok')
                mime,payload=tile
                self.send_response(200)
                self.send_header('Content-Type',mime)
                self.send_header('Content-Length',str(len(payload)))
                self.send_header('Cache-Control','public, max-age=86400')
                self.end_headers()
                return self.wfile.write(payload)
            if path=='/api/maps/list':
                return self.json_response({'maps':[map_details(mid) for mid in ('turkiye','ege')]})
            if path=='/api/maps/status':
                mid=parse_qs(url.query).get('map',['turkiye'])[0]
                return self.json_response(map_details(mid))
            if path.startswith('/api/tiles/'):
                parts=path.split('/')
                if len(parts)!=6 or not all(v.isdigit() for v in parts[3:]):
                    return self.json_response({'error':'Geçersiz karo koordinatı'},400)
                z,x,y=map(int,parts[3:])
                map_id=parse_qs(url.query).get('map',['turkiye'])[0]
                tile=read_map_tile(z,x,y,map_id)
                if tile is None:return self.send_error(404,'Yerel harita karosu yok')
                mime,payload=tile
                self.send_response(200)
                self.send_header('Content-Type',mime)
                self.send_header('Content-Length',str(len(payload)))
                self.send_header('Cache-Control','public, max-age=86400')
                self.end_headers()
                return self.wfile.write(payload)
            if path=='/api/health':
                return self.json_response({'status':'ok','app':'KALE','version':VERSION,'time':datetime.now(timezone.utc).isoformat()})
            if path=='/api/medicines':
                return self.medicine_query(url)
            if path=='/api/reviews/stats':
                return self.json_response(review_stats())
            if path=='/api/medicines/stats':
                with connection() as conn:
                    n=conn.execute('SELECT count(*) FROM medicines').fetchone()[0]
                    labeled=conn.execute("SELECT count(*) FROM medicines WHERE source LIKE 'openFDA%'").fetchone()[0]
                    summaries=conn.execute("SELECT count(*) FROM medicines WHERE review_status LIKE '%ÖZET%' OR review_status LIKE '%TASLAK%'").fetchone()[0]
                    rxnorm=conn.execute("SELECT count(*) FROM medicines WHERE source LIKE 'NLM RxNorm%'").fetchone()[0]
                return self.json_response({'total':n,'official_label_records':labeled,'turkish_summaries':summaries,'name_only_records':n-labeled-summaries,'rxnorm_names':rxnorm,'source_region':'ABD etiketleri ve onaysız Türkçe editoryal taslaklar','medical_review_approved':0})
            if path.startswith('/api/medicines/'):
                key=path[len('/api/medicines/'):]
                if not key or len(key)>90 or not key.replace('_','').isalnum():
                    return self.json_response({'error':'Geçersiz ilaç kimliği'},400)
                with connection() as conn:
                    row=conn.execute('SELECT * FROM medicines WHERE id=?',(key,)).fetchone()
                if row is None:return self.json_response({'error':'İlaç kaydı bulunamadı'},404)
                out=dict(row);out.pop('search_text',None)
                out['doctor_review']=public_review(key)
                return self.json_response(out)
            if path=='/api/catalog':
                return self.json_response(catalog())
            if path=='/api/stats':
                with connection() as conn:
                    total=conn.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
                    groups=conn.execute('SELECT COUNT(DISTINCT category) FROM entries').fetchone()[0]
                
                with connection() as conn:
                    drugs=conn.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]
                return self.json_response({'entries':total,'categories':groups,'medicines':drugs,'database_bytes':DB.stat().st_size,'version':VERSION})
            if path=='/api/categories':
                with connection() as conn:
                    rows=conn.execute('SELECT category,COUNT(*) AS count FROM entries GROUP BY category ORDER BY category').fetchall()
                return self.json_response({'categories':[dict(x) for x in rows]})
            if path=='/api/search':
                q=parse_qs(url.query,keep_blank_values=True)
                text=q.get('q',[''])[0][:160]
                cat=q.get('category',[''])[0][:40]
                try:
                    limit=max(1,min(200,int(q.get('limit',['30'])[0])))
                    offset=max(0,min(100000,int(q.get('offset',['0'])[0])))
                except ValueError:
                    return self.json_response({'error':'Geçersiz sayfa parametresi'},400)
                return self.json_response(search(text,cat,limit,offset))
            if path.startswith('/api/entry/'):
                try: eid=int(path.rsplit('/',1)[1])
                except ValueError: return self.json_response({'error':'Geçersiz kayıt'},400)
                with connection() as conn:
                    row=conn.execute('SELECT * FROM entries WHERE id=?',(eid,)).fetchone()
                if row is None:return self.json_response({'error':'Kayıt bulunamadı'},404)
                return self.json_response(parse_entry(row))
        except (sqlite3.Error,OSError,ValueError):
            return self.json_response({'error':'Veritabanına erişilemiyor'},503)
        if path.startswith('/api/'):
            return self.json_response({'error':'Endpoint bulunamadı'},404)
        if path in ('/','/index.html'):
            self.path='/index.html'
        elif not (path.startswith('/assets/') or path in ('/favicon.svg','/manifest.webmanifest','/service-worker.js','/sw.js','/ilaclar.html','/doktor.html','/saha.html','/doga.html','/harita.html','/plan.html','/offline.html','/atolye.html','/barinak-su.html','/gida-enerji.html','/envanter.html','/ilk-yardim.html','/aktarim.html','/sohbet.html','/baglan.html','/rota.html','/yonetim.html')):
            self.send_error(404)
            return
        return super().do_GET()


def self_test():
    assert DB.is_file(),'kale.db bulunamadı; python3 tools/build_db.py çalıştırın'
    with connection() as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        n=conn.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
        categories=conn.execute('SELECT COUNT(DISTINCT category) FROM entries').fetchone()[0]
    for f in ('index.html','assets/app.js','assets/style.css','favicon.svg','manifest.webmanifest','sw.js'):
        assert (WEB/f).is_file(),f
    with connection() as conn:
        meds=conn.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]
    assert meds>=180
    assert (WEB/'ilaclar.html').is_file()
    assert (WEB/'doktor.html').is_file()
    assert (WEB/'saha.html').is_file()
    assert (WEB/'doga.html').is_file()
    assert (WEB/'harita.html').is_file()
    assert (WEB/'plan.html').is_file()
    assert (WEB/'offline.html').is_file()
    assert (WEB/'atolye.html').is_file()
    assert (WEB/'barinak-su.html').is_file()
    assert (WEB/'gida-enerji.html').is_file()
    assert (WEB/'envanter.html').is_file()
    assert (WEB/'ilk-yardim.html').is_file()
    assert (WEB/'aktarim.html').is_file()
    assert (WEB/'sohbet.html').is_file()
    assert (WEB/'baglan.html').is_file()
    assert (WEB/'assets/vector-tile.js').is_file()
    assert (WEB/'assets/route.js').is_file()
    assert (WEB/'rota.html').is_file()
    assert (WEB/'yonetim.html').is_file()
    assert (WEB/'assets/device.js').is_file()
    assert (WEB/'assets/sync-core.js').is_file()
    assert (WEB/'assets/first-aid.json').is_file()
    assert (WEB/'assets/first-aid.js').is_file()
    assert (WEB/'assets/inventory-core.js').is_file()
    assert (WEB/'assets/inventory.js').is_file()
    assert (WEB/'assets/food-energy-winter.json').is_file()
    assert (WEB/'assets/shelter-water.json').is_file()
    assert (WEB/'assets'/'editor.js').is_file()
    assert (WEB/'assets'/'field-guides.json').is_file()
    assert (WEB/'assets'/'dangerous-mushrooms.json').is_file()
    assert (WEB/'assets'/'medicines-offline.json').is_file()
    assert n>=37
    print(f'KALE {VERSION} SELFTEST OK: {n} rehber, {categories} kategori, {meds} ilaç kaydı')

if __name__=='__main__':
    if '--selftest' in sys.argv:
        self_test();sys.exit(0)
    self_test()
    server=ThreadingHTTPServer((HOST,PORT),Handler)
    print(f'KALE {VERSION} -> http://127.0.0.1:{PORT}',flush=True)
    if HOST in ('0.0.0.0','::'):
        for url in network_info()['urls']: print('Wi-Fi bağlantısı: '+url+'sohbet.html',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
