# KALE v1.9 — Android/Termux kurulumu

**Android APK, root, proot Ubuntu veya yapay zekâ gerekmez.** Termux telefonun mevcut Linux/Android çekirdeğini kullanır; tam sistem çekirdeğinin değiştirilmesi veya root erişimi anlamına gelmez. İnternet ilk kurulum ve harita/kitap indirmek için gerekir, KALE verisi yerelde çalışır.

## Kurulum

1. [Termux](https://f-droid.org/en/packages/com.termux/) uygulamasını F-Droid'den kur. GPS alternatifini istersen [Termux:API](https://f-droid.org/en/packages/com.termux.api/) uygulamasını **aynı F-Droid kaynağından** yükle. Farklı kaynaklardan gelen Termux ve eklenti imzaları çakışabilir.
2. Telefonda Termux aç ve çalıştır:

```bash
pkg update && pkg upgrade -y
pkg install -y python git
# Yalnız Termux:API eklentisini kullanmak isteyenler:
pkg install -y termux-api

git clone https://github.com/nord-riot/KALE.git
cd KALE
python3 server.py --selftest
bash deploy/install-termux.sh install
~/bin/kale
```

3. Aynı telefondaki tarayıcıda **`http://127.0.0.1:8090/harita.html`** aç. Android'de konum hizmetini ve tarayıcının konum iznini aç. `Konumumu Bul` düğmesi bir tek ölçüm alır. Başarısızsa Termux:API uygulaması konum iznine sahipken `Termux GPS` düğmesini dene. Bu API sadece **127.0.0.1 / localhost** bağlantısına izin verir.
4. Bir noktayı **HEDEF** seçerek GPS konumundan kuş uçuşu mesafe ve başlangıç açısını bul. Bu **güvenli yol navigasyonu** değildir.

Sonradan başlatma: `~/bin/kale`. Durdurma: `Ctrl+C`. `bash deploy/install-termux.sh --check` ile temel dosya durumunu kontrol et. Terminali sistem öldürürse sunucu kesilir: **Android'de sürekli arka plan çalışma garantisi yoktur**. Sürekli GPS ve otomatik wake-lock yoktur.

## Harita paketi

İndirilmiş raster `.mbtiles` dosyasını telefonun Downloads klasörüne koy. Termux'ta:

```bash
termux-setup-storage
python3 tools/map_pack.py "$HOME/storage/downloads/turkiye.mbtiles"
python3 tools/map_pack.py "$HOME/storage/downloads/turkiye.mbtiles" --install
```

Bu araç mevcut haritayı varsayılan olarak korur; yeni haritayla değiştirmek için **sunucuyu durdurup** `--install --replace` kullan. Yeterli boş disk alanı ve harita sağlayıcısının lisansı gerekir. Detaylar: [Türkiye harita paketi](MAPS-OFFLINE.md).

## Gerçek saha kontrolü

- İnternet kapalıyken `http://127.0.0.1:8090/api/health` erişiliyor mu?
- Haritada daha önce kopyalanmış gerçek sokak/yol karoları açılıyor mu?
- Android GPS açık gökyüzünde konum, doğruluk ve hedef hesabını gösteriyor mu?
- Telefon uyku/ekran kapanınca Termux ne kadar çalışıyor?
- `aktarim.html` üzerinden kişisel kayıtları JSON olarak ayrı medyaya yedekledin mi?

**Gerçek Android cihazda bu sürümün GPS/Termux kurulumu henüz doğrulanmadı.** Hazırlık için kağıt harita, güç kaynağı, pusula ve çevrimdışı yedeği ayrı bulundur. İlaçlar hâlâ doktor onayı bekleyen taslaktır.

## 7/24 otomatik başlatma

Bkz. **[Android 7/24 sunucu kurulumu](ANDROID-24X7.md)**. Yeni gözetim komutu: `bash deploy/install-24x7.sh install`.
