> **v2.4 GÜNCEL KURULUM:** Tek satır Android kurulumu için [KALE v2.4 — Tek Kurulum](TEK-KURULUM-ANDROID.md) dosyasını kullan. Önceki çok-adımlı yönergeler eski sürümler içindir. 7/24 başlatıcı artık uygun rota verisi varsa BRouter'ı da başlatır; güç tasarrufu için `KALE_ENABLE_BROUTER=0` mümkündür.

# KALE v2.1 — Tüm Türkiye sokak haritası ve offline BRouter

**İlk indirme için internet gerekir.** Sonrasında Termux KALE sunucusu, yerel
vektör sokak haritası ve BRouter Java rota servisi internetten veri istemez.

## Gereken disk ve RAM

- Sokak haritası: BBBike **Shortbread PBF vektör MBTiles**, yaklaşık 567–571 MB (sürümle değişir). ZIP dosyası saklanırsa kurulum sırasında **ek geçici disk alanı** gerekir.
- Rota bölgeleri: **10 `.rd5` dosyası**, sunucudaki doğrulanmış örnek dosya listesi toplamı **243.207.400 bayt (~232 MiB)**; haftalık güncellemelerde değişir.
- BRouter Java JAR/profilleri: yaklaşık birkaç MB; çalışma sırasında Java RAM gerektirir. Telefonda en az 2 GB **boş depolama** bırakılması önerilir.
- Program kaynaklarıyla beraber harita ve rota için yaklaşık **1 GB kalıcı alan** makul, ama indirme/eski ZIP/yedeklerle 2–3 GB boş yer daha rahattır.

## Android / Termux ilk kurulum

[Termux'u F-Droid'den yükle](https://f-droid.org/packages/com.termux/). Ardından:

```bash
pkg update
pkg install -y python unzip openjdk-17
termux-setup-storage
cd ~/storage/downloads
unzip KALE-Server-v2.1-Turkiye-Rota-WiFi.zip -d ~
cd ~/KALE-v2.1
python3 server.py --selftest
bash deploy/install-termux.sh install
```

**Tüm Türkiye harita ve rota verisini indirmek (internet ve güç varken):**

```bash
python3 tools/turkiye_full.py all --dry-run
python3 tools/turkiye_full.py all
python3 tools/turkiye_full.py check
```

Ayrı ayrı kurmak istersen:

```bash
python3 tools/turkiye_full.py map
python3 tools/turkiye_full.py segments --region all
python3 tools/turkiye_full.py engine
```

İndirmeler büyük; kararlı Wi-Fi ve şarj kullan. Bir kesilme sonrasında yeniden
çalıştırıldığında tamamlanmış hedef dosyalar yeniden indirilmez; yarım `.part`
dosyaları güvenlik için **sıfırdan** indirilir. İndirdikten sonra sağlayıcının
ayrıca yayınladığı checksum varsa onunla da doğrula. Dosyalar lisanslarıyla
birlikte saklanmalıdır.

**Çalıştır:**

```bash
~/bin/kale
```

Bu tek komut, BRouter veri ve Java kurulmuşsa arka planda sadece
`127.0.0.1:17777` üzerinde BRouter başlatır ve KALE'yi Wi-Fi'da **8090**
portunda açar. BRouter kurulmamışsa KALE yine normal açılır, ama gerçek yol
rotası hesaplayamaz. Sunucuyu kapatmak için Ctrl+C.

## Cihazlardan erişim ve ortak sohbet

- KALE'yi kuran telefon: `http://127.0.0.1:8090/`
- Aynı Wi-Fi/hotspot'taki diğer telefonlar: `http://KALE_TELEFON_IP:8090/`
- Giriş ve sohbet: `/sohbet.html` (isimle giriş; RAM'de geçici mesajlar).
- Rota ve GPS: `/harita.html` veya `/rota.html`.
- Aynı Wi-Fi'da olmak yetmeyebilir: yönlendiricinin **AP/client isolation** özelliği kapalı olmalı.
- Android'de **root olmadan HTTP 80. port** açılamadığı için cihazlar LAN IP'sine `:8090` eklemeli; QR bağlantısını kullanabilirler.
- QR için Python `qrcode` modülü ayrıca gerekir: `python3 -m pip install qrcode`.
- Bu sohbet kimlik doğrulamalı veya uçtan uca şifreli değildir. Güvenilmeyen Wi-Fi üzerinde kullanma.

## Tamamen internetsiz navigasyonun sınırları

1. KALE **BBBike Shortbread** vektör karolarını yerel SQLite MBTiles'den okur ve hafif Canvas motoruyla temel yolları, su alanlarını ve bina konturlarını çizer. Harita stili sadeleştirilmiştir: tam MapLibre/Google Maps görsel özelliklerinin veya adres/kapı numarası aramasının yerini tutmaz.
2. BRouter, OpenStreetMap `.rd5` yol ağıyla yürüyüş/bisiklet/araç için rota üretebilir. KALE, **çalışan yerel motorun gerçek GeoJSON yol çizgisini** gösterir. Motor veya veri yoksa yanlış rota üretmez.
3. **Canlı trafik, yol kapalı bilgisi, sel/yangın, köprü hasarı, askerî bölge erişimi ve güvenli tahliye garantisi yoktur.** Rota, tehlikeleri değerlendirmeden kullanılmamalı.
4. Android tarayıcısında LAN HTTP erişiminde cihaz konumu için güvenli bağlam şartı nedeniyle **tarayıcı GPS çalışmayabilir**. Sunucu telefonun kendisinde `127.0.0.1` üzerinden Termux:API tek seferlik GPS alabilir; diğer cihazlarda kendi telefonlarının HTTPS/konum koşulları geçerlidir.
5. Kendi cihazındaki harita/rota verileri server'da yüklüyse aynı Wi-Fi'daki tüm cihazlar bu harita ve rota uç noktalarını kullanabilir. Kullanıcı envanterleri ve koordinat notları tarayıcıya özeldir; paylaşım bilinçli yapılmalıdır.

## Doğrulanmış kaynaklar

- [BBBike Türkiye Shortbread vector MBTiles](https://data.bbbike.org/osm/region/europe/turkey/)
- [BRouter `.rd5` segment indirme](https://brouter.de/brouter/segments4/)
- [BRouter standalone sürümü](https://github.com/abrensch/brouter/releases/tag/v1.7.10)
- [BRouter HTTP sunucusu](https://zod.github.io/brouter/developers/http_server.html)

Harita/veri telifi: © OpenStreetMap contributors — [ODbL 1.0](https://www.openstreetmap.org/copyright). BRouter ayrı açık kaynak lisanslarına tabidir. Harita dosyalarının **kendileri bu kaynak ZIP'e dahil değildir**; internetin erişilebilir olduğu dönemde indirip KALE telefonuna koymak gerekir.
