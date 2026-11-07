> **v2.4 GÜNCEL KURULUM:** Tek satır Android kurulumu için [KALE v2.4 — Tek Kurulum](TEK-KURULUM-ANDROID.md) dosyasını kullan. Önceki çok-adımlı yönergeler eski sürümler içindir. 7/24 başlatıcı artık uygun rota verisi varsa BRouter'ı da başlatır; güç tasarrufu için `KALE_ENABLE_BROUTER=0` mümkündür.

# KALE v2.2 — Android/Termux 7/24 Offline Hotspot Sunucusu

**Hedef:** Redmi Note 14 Pro (HyperOS), Android korunarak; Termux üzerinde Python, Wi-Fi hotspot ile internetsiz bilgi sunucusu. **Gerçek Redmi testi yapılmadı.** Root, APK ve proot Ubuntu zorunlu değildir.

## 1) Telefonu hazırla (internet yalnız ilk kurulumda)

1. F-Droid'den **Termux**, **Termux:Boot** ve **Termux:API** yükle. Üçünün aynı imza kaynağından geldiğini kontrol et (F-Droid + başka kaynak karıştırma).
2. **Termux:Boot uygulamasını bir kez aç.** Açılmadan BOOT_COMPLETED tetikleyicisi işlemeyebilir.
3. Termux'u açıp şu komutları uygula:

```sh
pkg update && pkg upgrade -y
pkg install -y python git termux-api
# Sadece offline rota motorunu da kullanmak istiyorsan: pkg install openjdk-17
termux-setup-storage
git clone https://github.com/nord-riot/KALE.git
cd KALE
python3 server.py --selftest
bash deploy/install-termux.sh install
bash deploy/install-24x7.sh --dry-run
bash deploy/install-24x7.sh install
```

Termux 7/24 gözetimini elle başlat (aynı portta ikinci `~/bin/kale` çalıştırma):

```sh
~/bin/kale-24x7
```

Gözetim `server.py` kapanırsa 3–60 saniye arası gecikmeyle yeniden başlatır. Log ve geçici durum dosyaları `~/.cache/kale/` altındadır; servis/API hiçbir mesaj metnini veya kişisel veriyi loglamaz. Log üst sınırı yaklaşık 1 MiB'dir; sunucu erişim kaydı varsayılan **kapalı**.

> `termux-wake-lock` CPU'nun uykuya geçmesini engeller; **batarya tüketimini artırabilir**. Düşük pil hedefiyle 7/24 erişim hedefi birbirine zıt olabilir. Bu yüzden 24/48/72 saat gerçek ölçüm şart.

## 2) HyperOS (Redmi Note 14 Pro) ayarları — manuel

Telefonun sürümüne göre menülerin yerleri değişebilir.

- **Termux** ve **Termux:Boot** uygulamalarında pil optimizasyonunu **Kısıtlama yok / Unrestricted** olarak ayarla. Destekleniyorsa **otomatik başlatma** iznini aç ve uygulamaları son uygulamalar listesinde kilitle.
- Wi-Fi Hotspot / Taşınabilir Erişim Noktası: **KALE-OFFLINE** SSID, güçlü WPA2/WPA3 parolası. Boşta veya bağlı cihaz yokken otomatik kapanmayı **kapat** (varsa).
- **Mobil veri ve LTE'yi kapat**; hotspot ağının internetsiz çalıştığını doğrula. Bazı HyperOS sürümleri mobil veri yokken hotspot'u açmayabilir veya yeniden kapatabilir.
- Ekranı kapatıp farklı cihazlardan KALE'ye bağlan. Başlangıç hedefi eşzamanlı **3–5 cihaz**. AP/client isolation açık olmamalı.
- Android cihaz yeniden başlayınca Termux:Boot sayesinde **sunucu otomatik açılabilir**; **hotspot'u root olmadan otomatik açma garantisi yoktur**. Yeniden başlatma sonrası AP'nin de açık olduğunu ayrı doğrula.

## 3) Erişim

Telefonun kendi tarayıcısı:

- **KALE:** `http://127.0.0.1:8090`
- **Yönetim (yalnız sunucu telefonunda):** `http://127.0.0.1:8090/yonetim.html`
- **Bağlantı/QR:** `http://127.0.0.1:8090/baglan.html`

Diğer telefonlar **KALE-OFFLINE** ağına bağlanıp sunucu telefonun hotspot IP adresini ve portunu açar. Örnek: `http://192.168.43.1:8090`. Bu örnek IP garanti değildir; gerçek IP'yi bağlantı ekranından/hotspot ayarından doğrula. `localhost` her cihazın **kendi** adresidir. **Root olmadan 8090 portunu kaldıramayız**; `kale.local` adı ayrıca mDNS/DNS gerektirir.

**Güvenlik:** `yonetim.html` ve `/api/device/*` yalnız gerçek loopback TCP bağlantısıyla erişilebilir. Diğer Wi-Fi kullanıcıları sohbet ve kaynaklara ulaşabilir, ama pil/CPU/servis paneline ulaşamaz. `X-Forwarded-For` başlığı dikkate alınmaz. Herkese açık Wi-Fi veya internete yönlendirme yapma.

## 4) Yönetim paneli

- **Pil:** Termux:API `termux-battery-status` kurulu ve izinli ise yüzde/şarj durumu/batarya sıcaklığı. `temperature` CPU sıcaklığı **değildir**.
- **Kalan süre:** Yalnız cihazın verdiği `charge_counter` ve `current` tutarlıysa kaba bir saat hesabı; boşsa **bilinmiyor**.
- **CPU/RAM:** Android `/proc/stat` ve `/proc/meminfo` erişilebilirse ölçülür, aksi hâlde bilinmiyor.
- **Çalışma süresi:** Son KALE sunucu açılışından itibaren. Android'in uptime'ı değildir.
- **İstemciler:** KALE sohbetinin aktif kullanıcı sayısı gösterilir. Android hotspot'a bağlı cihazların sayısı izin yoksa **bilinmiyor**.
- **Olaylar:** Bellekteki son 50 uygulama olayı ve gözetimin yeniden başlatma sayısı.
- **Enerji tasarrufu:** Panelin pil/CPU ölçümünü 12 saniye yerine 35 saniyede bir alır, tarayıcı güncellemelerini 15 yerine 45 saniyeye çıkarır. **Hotspot'u veya Android CPU hızını değiştirmez.**

## 5) 24/48/72 saat kabul testi

| Deneme | Beklenti | Test durumu |
| --- | --- | --- |
| Mobil veri kapalı + AP açık | En az 3 cihaz web ve sohbeti açar | **Redmi üzerinde yapılmadı** |
| Ekran kapalı 24 saat | Sunucu/hotspot kesilmeden erişilebilir | **Yapılmadı** |
| 48 ve 72 saat | Çökme, ısınma, hotspot kapanma yok | **Yapılmadı** |
| Termux:Boot sonrası reboot | Sunucu otomatik açılır | **Yapılmadı** |
| Sunucu sürecini öldürme | Supervisor birkaç saniye sonra tekrar açar | Linux üzerinde sınanabilir; Android süreç öldürme farklıdır |
| Ölçüm | Günlük Wh ve şarjdan düşen % kayıt altına alınır | **Yapılmadı** |

Örnek hedef **25–30 Wh/gün** yalnız kullanıcı planıdır; doğrulanmış tüketim değildir. 7/24 CPU wake lock ile bu hedefin tutup tutmayacağı Redmi üzerinde ölçülmelidir. Bataryanın aşırı ısınması veya şişmesi durumunda sistemi güvenli biçimde kapat.

## 6) Kurtarma ve sorun giderme

```sh
# Loglar (Termux)
tail -n 80 ~/.cache/kale/supervisor.log
cat ~/.cache/kale/supervisor.json
# Sunucu sağlık kontrolü
python3 -c 'import urllib.request;print(urllib.request.urlopen("http://127.0.0.1:8090/api/health",timeout=5).read().decode())'
```

- **Sunucu açık, hotspot yok:** Android/HyperOS ayarını manuel kontrol et; KALE hotspot kontrolü yapamaz.
- **Web açılmıyor:** KALE supervisor, doğru IP/port, Android AP isolation ve istemci ağını kontrol et.
- **Pil bilgisi yok:** `pkg install termux-api`, F-Droid Termux:API uygulaması, izinleri kontrol et.
- **Termux:Boot çalışmıyor:** Eklentiyi uygulama ikonundan bir kez açtığını ve pil kısıtlamalarını kaldırdığını doğrula.
- **BRouter pil tüketiyor:** 7/24 süreç varsayılan olarak BRouter'ı başlatmaz; açıkça `KALE_ENABLE_BROUTER=1` ayarlandığında başlar. Harita görüntülemesi ve KALE sohbeti rota motoru olmadan çalışır.

## Resmî kaynaklar

- [Termux:Boot](https://github.com/termux/termux-boot)
- [Termux:API](https://github.com/termux/termux-api)
- [Android hotspot belge ve sınırlamalar](https://support.google.com/android/answer/14993633)
