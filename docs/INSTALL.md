# KALE v1.8 — Kurulum Kılavuzu

> **Not:** Bu repo henüz tam kaynak arşivinin yayınlanması aşamasındadır. Aşağıdaki komutlar ancak \`server.py\`, \`data/\`, \`web/\`, \`tools/\` ve \`deploy/\` dizinleri repoya eklendikten sonra çalışır.

## Gereksinimler

- Python **3.9+** (tercihen güncel Python 3)
- Windows, Ubuntu / Debian, Raspberry Pi OS veya Docker
- Yerel makinede tarayıcı
- Temel sunucu kurulumu için **pip/Node.js gerekmiyor**
- İnternet yalnız ilk kurulum/indirme veya yeni veri için gerekli; bilgi arşivi yerel çalışır.

## Ubuntu / Debian

\`\`\`bash
sudo apt update
sudo apt install -y git python3 unzip
git clone https://github.com/nord-riot/KALE.git
cd KALE
python3 server.py --selftest
python3 -m unittest discover -s tests -q
KALE_HOST=127.0.0.1 KALE_PORT=8090 python3 server.py
\`\`\`

Tarayıcı: **http://127.0.0.1:8090/**

Yerel ağdan erişim gerekiyorsa \`KALE_HOST=0.0.0.0\` ayarlanabilir. Bunu yapmadan önce güvenilir ağ ve güvenlik duvarı kuralları uygulayın; doğrudan internete açmayın.

## Windows (PowerShell)

Python 3 kurulmuş ve PATH'te olmalı.

\`\`\`powershell
git clone https://github.com/nord-riot/KALE.git
cd KALE
python server.py --selftest
python -m unittest discover -s tests -q
$env:KALE_HOST = "127.0.0.1"
$env:KALE_PORT = "8090"
python server.py
\`\`\`

Tarayıcı: **http://127.0.0.1:8090/**

## Docker

Docker Engine / Docker Desktop ve Compose eklentisi gerektirir.

\`\`\`bash
git clone https://github.com/nord-riot/KALE.git
cd KALE
docker compose up --build -d
docker compose ps
\`\`\`

Varsayılan \`compose.yaml\` portu **127.0.0.1:8090 → konteyner 8080**. \`docker compose logs -f kale\` ile günlükleri inceleyin.

## Raspberry Pi OS / Ubuntu / Debian — systemd

> **Dikkat:** Raspberry Pi donanım testleri henüz tamamlanmadı. Kurulum \`/opt/kale\` dizinine kopyalama yapar ve orası zaten varsa üzerine yazmayı reddeder.

\`\`\`bash
sudo apt update
sudo apt install -y git python3
git clone https://github.com/nord-riot/KALE.git
cd KALE
sh deploy/install-pi.sh --dry-run
sudo sh deploy/install-pi.sh
sudo systemctl status kale.service
sudo systemctl status kale-backup.timer
\`\`\`

Kullanıcı \`kale\` sistem hesabıyla, varsayılan **127.0.0.1:8090** üzerinde çalışır. Aynı yerel ağdaki cihazlardan erişim için:

\`\`\`bash
sudo nano /etc/default/kale
# KALE_HOST=0.0.0.0
sudo systemctl restart kale.service
\`\`\`

Güvenlik duvarında yalnızca güvenilir istemcilere izin verin. Açık internete servis vermeden önce HTTPS, kimlik doğrulama ve erişim denetimleri sağlayın.

## Veri bütünlüğü, yedek ve geri yükleme

\`\`\`bash
python3 server.py --selftest
python3 tools/offline_audit.py
python3 tools/backup.py create
\`\`\`

Yedekleri sonradan doğrulayın:

\`\`\`bash
python3 tools/backup.py verify /yedek/KALE-SERVER-BACKUP-XXXX.zip
\`\`\`

Geri yüklemeden önce servisi durdurun. Ön inceleme dosya yazmaz:

\`\`\`bash
python3 tools/backup.py restore /yedek/KALE-SERVER-BACKUP-XXXX.zip
\`\`\`

Gerçek geri yükleme açık onay gerektirir:

\`\`\`bash
python3 tools/backup.py restore /yedek/KALE-SERVER-BACKUP-XXXX.zip --apply --confirm GERI_YUKLE
\`\`\`

**Yedek ZIP dosyaları şifrelenmez.** Özel dosyaları güvenli diskte tutun.

## Çevrimdışı kullanım

\`/offline.html\` sayfasından önbelleği hazırla ve kontrol et. PWA servis çalışanının kurulabilmesi için **localhost veya HTTPS** gerekir; sıradan \`http://192.168.*\` yerel ağ bağlantısı PWA için güvenli bağlam değildir. Doğrudan Python mini sunucusu, internetsiz **yerel ağda** ayrıca çalışabilir.

Raspberry Pi üzerinde **gerçek güç kaybı / offline saha testi yapılmamıştır**.

## Sayfalar

| Yol | Bölüm |
|---|---|
| \`/\` | Ana sayfa / 146 temel rehber |
| \`/ilaclar.html\` | 707 doğrulanmamış ilaç taslağı |
| \`/ilk-yardim.html\` | 24 ilk yardım kartı |
| \`/envanter.html\` | Kişisel gıda/su/ekipman stoğu |
| \`/doga.html\` | Bitki ve mantar risk farkındalığı |
| \`/barinak-su.html\` | Barınak ve su rehberleri |
| \`/gida-enerji.html\` | Gıda, enerji, kış |
| \`/harita.html\` | Yerel harita / koordinatlar |
| \`/plan.html\` | 72 saat aile hazırlığı |
| \`/aktarim.html\` | Dosyayla veri aktarımı |
| \`/offline.html\` | Çevrimdışı önbellek denetimi |

**Tıbbi bilgiler uzman onayı olmayan taslaklardır.** Acil durumlarda sağlık hizmetlerini aramayı geciktirmeyin.
