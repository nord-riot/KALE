# KALE v2.4 — Tek Komutla Türkiye Offline Sokak + Rota Kurulumu

**Redmi Note 14 Pro, Termux (Android korunur).** Root, Ubuntu proot, Docker ve APK gerekmiyor. Bu modül KALE'nin Python/SQLite sunucusudur; Raspberry Pi kurulumu da kullanılabilir.

## 1. Sadece bir kere Termux uygulamasını kur

- Termux'u **F-Droid** üzerinden kur. Android'in paket yüklemesi için internet gereklidir.
- 7/24 açılış için aynı kaynaktan **Termux:Boot** kur ve bir defa çalıştır.
- Termux:API pil/GPS ölçümleri için isteğe bağlıdır; bu modül olmadan sohbet/harita çalışır.
- HyperOS ayarlarında Termux ve Termux:Boot için pil kısıtlamalarını kaldır. Android erişim noktası (hotspot) adını KALE-OFFLINE yap, güçlü parola koy ve otomatik kapatma ayarını kapat. Root olmadan hotspot'un otomatik açılması garanti edilemez.

## 2. Tek satır kurulum

Termux içine **bir kez** şu satırı yapıştır:

```bash
pkg install -y curl && curl -fsSL https://raw.githubusercontent.com/nord-riot/KALE/main/deploy/bootstrap-termux.sh | bash
```

Betik sırasıyla Python, Git, Java 17 ve Termux:API komut paketini kurar; git kaynağını indirir veya mevcut ~/KALE klasörünü güvenli `git pull --ff-only` ile günceller; **gerçek Türkiye Shortbread MBTiles sokak haritasını**, Türkiye için **10 BRouter `.rd5` rota bölgesini** ve BRouter motorunu indirir; geçerli veri varlığını denetler; KALE'nin öz testini çalıştırır; 7/24 başlatıcıyı oluşturur ve yerel sunucuyu başlatır.

> **İlk kurulum internete ihtiyaç duyar.** Yaklaşık 570 MB vektör harita arşivi + yaklaşık 230 MiB rota dosyaları + Java/araçlar indirilir. İndirme/çıkarma sırasında **en az 3 GiB boş disk** tavsiye edilir. Bu dosyalar GitHub'daki küçük kaynak ZIP'ine gömülü değildir; kullanıcı ayrı komut girmeden yukarıdaki satır indirir.

Harita sağlayıcısı: [BBBike Türkiye Shortbread MBTiles](https://data.bbbike.org/osm/region/europe/turkey/) · Rota sağlayıcısı: [BRouter 5° × 5° bölgeler](https://brouter.de/brouter/segments4/). Harita © OpenStreetMap katkıcıları, ODbL. Kaynaklar zamanla güncellenebilir; boyutlar değişebilir. Veri erişimi kesilirse kurulum hata verir, yarım pakete "hazır" demez. Aynı satırı yeniden çalıştırarak tekrar deneyebilirsin.

## 3. İnternet kapatıldıktan sonra

- Sunucu telefon: `http://127.0.0.1:8090/harita.html`
- Diğer telefonlar ve bilgisayarlar: `http://TELEFON_HOTSPOT_IP:8090/` (`localhost` ve `127.0.0.1` karşı cihazdan **çalışmaz**).
- Hotspot IP'sini telefondaki `/baglan.html` sayfasında gör; PC'nin Wi-Fi ağ geçidi genellikle telefonun adresidir.
- Harita: `/harita.html` → **TÜRKİYE SOKAKLAR (OSM)** otomatik seçilir.
- Rota: `/rota.html` → yürüyüş, bisiklet, araç güzergâhı (BRouter Java motoru kurulup açıldıysa).
- Sohbet: `/sohbet.html` → Wi-Fi kullanıcıları isimle giriş yapar; mesajlar RAM'de saklanır.
- İzleme: `/yonetim.html` → yalnız **sunucu telefonunun localhost bağlantısından** açılır.

**Sokak verisi kurulduğunu denetle:**

```bash
cd ~/KALE
python3 tools/turkiye_full.py check
```

Harita `installed: true`, rota `segments_found: 10` olmalı. Rota motorunun `engine_online: true` olması için 7/24 sunucunun başlatılmış olması gerekir. 7/24 başlatıcı rota motorunu da başlatır (Java daha fazla RAM/pil kullanır); enerji tasarrufu için `KALE_ENABLE_BROUTER=0 ~/bin/kale-24x7` ile rota motorunu kapatabilirsin.

## 4. Kısıtlar ve güvenlik

- Termux:Boot yeniden başlatmadan sonra KALE'yi çalıştırabilir; **hotspot kendiliğinden açılmayabilir**. Bu Android/HyperOS kısıtıdır.
- 7/24 çalışmaya uygunluk ve Redmi Note 14 Pro pil tüketimi **gerçek cihazda 24/48/72 saat denenmedi**.
- İnternet olmadan yol hesaplaması, yalnız indirildiği tarihte OSM'de bilinen yolları gösterir; kapalı yol, heyelan, sel, yangın, enkaz, çatışma, yürüyüş güvenliği veya canlı trafik garantisi yoktur.
- KALE sohbetini internete port yönlendirmesiyle açma; şifrelenmiş kullanıcı kimlik doğrulaması yoktur.
- KALE'deki ilaç ve klinik taslaklar tıbbi uzman onayı bekler; sistem tıbbi karar mekanizması değildir.

## Test ayrımı

KALE'nin Python testleri ve örnek Shortbread `streets`/`street_labels` karo çizimi yerel testlerde doğrulanmıştır. **Gerçek 570 MB BBBike verisi, gerçek Türkiye .rd5 seti ve Redmi Note 14 Pro ile uçtan uca kurulum/rota testi bu geliştirme ortamında yapılmamıştır.** Kurulumu başarılı kabul etmek için gerçek cihazda önce çevrimdışı harita ve rota denemesini yap.
