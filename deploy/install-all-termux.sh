#!/data/data/com.termux/files/usr/bin/bash
# Works only on Termux; will download the full legal offline vector map and routing data.
set -Eeuo pipefail
trap 'echo "HATA: Kurulum bu aşamada durdu. Veriler silinmedi; komutu yeniden çalıştırabilirsin." >&2' ERR
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ "${PREFIX:-}" != */com.termux/files/usr ]]; then
  echo 'Bu kurulum Android Termux içindir.' >&2;exit 2
fi
command -v python3 >/dev/null || { echo 'Python eksik. Önce pkg install python';exit 2; }
command -v java >/dev/null || { echo 'Java eksik. Önce pkg install openjdk-17';exit 2; }
if [[ ! -f data/maps/turkiye-street.mbtiles ]]; then
  python3 - <<'PY'
import shutil,sys
free=shutil.disk_usage('.').free
print(f'Boş alan: {free/2**30:.1f} GiB')
if free<3*2**30:
    sys.exit('En az 3 GiB boş alan aç: harita ZIP + açılmış harita + rota dosyaları için gerekli.')
PY
fi
printf '\n[1/5] GERÇEK TÜRKİYE SOKAK HARİTASI (MBTiles) indiriliyor/doğrulanıyor...\n'
# Street map is independent of BRouter routing. A route download failure
# must never hide a successfully installed offline street map.
python3 tools/turkiye_full.py map
python3 - <<'PY'
from routing import inspect_street_map
m=inspect_street_map()
if not m.get('installed'):
    raise SystemExit('SOKAK HARİTASI EKSİK: ' + m.get('message','Türkiye OSM paketi kurulamadı.'))
print('OK: GERÇEK SOKAK HARİTASI',round(m['size_bytes']/2**20),'MiB')
PY
printf '\n[2/5] Offline rota motoru kurulumu deneniyor (haritadan bağımsız)...\n'
route_deps=1
python3 tools/turkiye_full.py segments || route_deps=0
python3 tools/turkiye_full.py engine || route_deps=0
if [[ "$route_deps" = 0 ]]; then
  echo 'UYARI: Rota verileri eksik ama SOKAK HARİTASI HAZIR. Harita çalışacak.'
fi
python3 tools/turkiye_full.py check || true
printf '\n[2b/5] Kamu malı USGS güvenlik görselleri yerel cihaza alınıyor...\n'
python3 tools/install_open_images.py || echo 'UYARI: Bazı görseller indirilemedi; yerel SVG çizimleri kullanılacak.'
printf '\n[3/5] KALE web uygulaması kontrol ediliyor...\n'
python3 tools/audit_guides.py
python3 server.py --selftest
printf '\n[4/5] Android 7/24 başlatıcı ve yeniden başlatma desteği kuruluyor...\n'
bash deploy/install-termux.sh install
bash deploy/install-24x7.sh install
printf '\n[5/5] Önceki KALE kapatılıyor ve yeni sürüm başlatılıyor...\n'
python3 tools/stop_own_server.py || { echo 'HATA: Eski KALE kapanmadı. Termux oturumlarında Ctrl+C yap, kurulumu tekrar çalıştır.' >&2; exit 1; }
mkdir -p "$HOME/.cache/kale"
# Do not launch a second instance over an existing healthy service.
if python3 - <<'PY'
from urllib.request import urlopen
import json
try:
    with urlopen('http://127.0.0.1:8090/api/health',timeout=2) as r:
        d=json.load(r)
    print('8090 portunda uygulama var:',d)
except Exception:raise SystemExit(1)
PY
then
  # Another KALE copy can still be on this port (e.g. from an older ZIP folder).
  if ! python3 - <<'PY'
import json
from urllib.request import urlopen
with urlopen('http://127.0.0.1:8090/api/health',timeout=3) as response:d=json.load(response)
if d.get('app')!='KALE' or d.get('version')!='2.4.0':
    raise SystemExit('Eski/baska sunucu 8090 portunda! Eski KALE oturumunda Ctrl+C yap ve kurulumu tekrar calistir.')
PY
  then exit 1;fi
else
  nohup "$HOME/bin/kale-24x7" >> "$HOME/.cache/kale/boot.log" 2>&1 < /dev/null &
  started=0
  for attempt in $(seq 1 15);do
    if python3 - <<'PY' 2>/dev/null
from urllib.request import urlopen
import json
with urlopen('http://127.0.0.1:8090/api/health',timeout=1) as r:d=json.load(r)
assert d['app']=='KALE' and d['version']=='2.4.0'
PY
    then started=1;break;fi
    sleep 1
  done
  if [[ "$started" != 1 ]];then
    echo 'KALE 8090 adresinde başlayamadı. Hatalar: tail -n 70 ~/.cache/kale/supervisor.log' >&2
    exit 1
  fi
fi
# The routing backend is a separate local Java process and may need startup time.
router=0
for attempt in $(seq 1 20);do
  if python3 - <<'PY' 2>/dev/null
from urllib.request import urlopen
import json
with urlopen('http://127.0.0.1:8090/api/route/status',timeout=2) as response: data=json.load(response)
assert data.get('ready') is True
PY
  then router=1;break;fi
  sleep 1
done
if [[ "$router" != 1 ]];then
  echo 'UYARI: Sokak haritası hazır; BRouter rota servisi bu cihazda henüz aktif değil.' >&2
  echo 'Harita: http://127.0.0.1:8090/harita.html' >&2
  echo 'Rota logu: tail -n 80 ~/.cache/kale/supervisor.log' >&2
fi
printf '\n*** KALE KURULDU ***\n'
printf 'TELEFON: http://127.0.0.1:8090/harita.html\n'
printf 'Wi-Fi bagli cihazlar: http://TELEFON_HOTSPOT_IP:8090/\n'
printf 'Bağlantı ekranı: http://127.0.0.1:8090/baglan.html\n'
printf 'Hotspot adı ve şifre Android ayarlarından MANUEL ayarlanır.\n'
printf 'Termux:Boot ayrı F-Droid uygulamasıdır; bir kez aç ve pil kısıtlamasını kaldır.\n'
printf 'İnternet ilk kurulum dışında gerekmez; yeni harita verilerini çevrimdışı kullanırsın.\n'
