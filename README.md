<p align="center">
  <img src="docs/img/kale-logo.svg" alt="KALE — Kapsamlı Afet ve Yaşam Envanteri" width="860">
</p>

<h1 align="center">KALE — Offline Afet ve Yaşam Bilgi Sistemi</h1>
<p align="center"><strong>Python 3 · SQLite · PWA · Raspberry Pi · Türkçe · Çevrimdışı öncelikli</strong></p>

> **Yayında — 4 Kasım 2026:** KALE v1.8'in **tam kaynak kodu, SQLite veri arşivi, web varlıkları, orijinal SVG rehber şemaları ve gerçek ekran görüntüleri** GitHub deposunda yer alıyor. GitHub Actions üzerinde öz test ve Python testleri başarıyla çalıştı. **Klinik içeriklerin uzman onayı ve gerçek Raspberry Pi saha testi tamamlanmadı.**

KALE (**Kapsamlı Afet ve Yaşam Envanteri**), internet bağlantısı olmasa da yerel sunucuda çalışabilen Türkçe bir afet hazırlığı ve bilgi merkezidir. Uygulama kişisel stok takibi, barınma ve su güvenliği, hazırlık planı, doğa farkındalığı, harita ve ilk yardım rehberlerini bir araya getirir.

![KALE modül tanıtımı](docs/img/modules.svg)

## Özellikler — KALE v1.8

| Bölüm | Kapsam |
|---|---|
| Afet ansiklopedisi | 146 temel Türkçe rehber, arama ve kategori |
| Görselli rehberler | Barınak, su, gıda, enerji, kış ve saha kılavuzları |
| İlk yardım | 24 kaynak bağlantılı, uzman incelemesi bekleyen konu kartı |
| İlaç arşivi | 707 **klinik onayı olmayan** Türkçe taslak kaydı |
| Doğa güvenliği | Zehirli bitki ve mantar farkındalığı |
| Envanter | Gıda, su, ilaç, ekipman, TETT/SKT ve miktar takibi |
| Aile afet planı | 72 saat, kontrol listesi, su hesabı |
| Offline harita | Yerel özet coğrafya, koordinatlar ve isteğe bağlı raster MBTiles |
| Cihazlar arası aktarım | Yerel JSON dışa/içe aktarma; otomatik senkronizasyon değil |
| Yedekleme | SHA-256 kontrollü ZIP, geri yükleme doğrulaması, systemd timer |
| Raspberry Pi | Raspberry Pi OS/Debian için kurulum betiği |

## Görseller

**Mimari**

![KALE sistem mimarisi](docs/img/architecture.svg)

**Modüller**

![KALE modülleri](docs/img/modules.svg)

> Yukarıdaki SVG'ler şematik tanıtımlardır. Aşağıdakiler ise uygulamanın **gerçek Chromium ekran önizlemeleridir**.

### Gerçek ekran görüntüleri

**Stok envanteri**

![KALE Stok Envanteri ekranı](docs/img/screenshots/stok-envanter.png)

**İlk yardım merkezi**

![KALE İlk Yardım Merkezi ekranı](docs/img/screenshots/ilk-yardim.png)

**Yedekleme ve cihazlar arası veri aktarımı**

![KALE yedekleme ve aktarım ekranı](docs/img/screenshots/yedekleme-aktarim.png)


## Hızlı kurulum

**Ubuntu / Debian / Raspberry Pi OS**

\`\`\`bash
sudo apt update
sudo apt install -y git python3
git clone https://github.com/nord-riot/KALE.git
cd KALE
python3 server.py --selftest
KALE_HOST=127.0.0.1 KALE_PORT=8090 python3 server.py
\`\`\`

Tarayıcı: [http://127.0.0.1:8090/](http://127.0.0.1:8090/)

**Docker**

\`\`\`bash
docker compose up -d --build
\`\`\`

**Raspberry Pi — systemd servis kurulumu**

\`\`\`bash
sh deploy/install-pi.sh --dry-run
sudo sh deploy/install-pi.sh
sudo systemctl status kale.service
sudo systemctl status kale-backup.timer
\`\`\`

> Pi kurulumunun gerçek donanım testi henüz yapılmadı. Betik \`/opt/kale\` zaten varsa kurulum yapmayı reddeder.

Tam adımlar: **[Kurulum kılavuzu](docs/INSTALL.md)** · **[Güvenlik ve sınırlamalar](docs/SECURITY.md)**

## Testler

\`\`\`bash
python3 server.py --selftest
python3 -m unittest discover -s tests -q
python3 tools/offline_audit.py
\`\`\`

**95 Python otomatik testi** GitHub Actions üzerindeki kaynak açma/yayınlama iş akışında başarıyla çalıştırıldı. Gerçek Raspberry Pi, güç kesintisi ve saha testleri henüz yapılmadı. [Test çalışmasını gör](https://github.com/nord-riot/KALE/actions/runs/41779929488).

## Güvenlik uyarısı

**KALE, tıbbi teşhis, reçeteleme veya profesyonel acil müdahale sistemi değildir.** İlaç ve ilk yardım taslaklarının klinik uzman kontrolü tamamlanmamıştır. Bitki/mantar kayıtları güvenli tüketim kararı verdirmez. Acil durumda **112**'yi aramayı geciktirmeyin. Özel JSON yedekleri, doktor inceleme verilerini ve konum bilgilerini herkese açık repoya yüklemeyin.

## Lisans ve katkı

Kaynak paketinde lisans belgesi bulunur; üçüncü taraf içerik ve veri kaynaklarının koşulları ayrıca değerlendirilmelidir. Saha, içerik ve donanım testleri tamamlanmadan gerçek acil durumlarda tek bilgi kaynağı olarak kullanılmamalıdır.

---

**Proje:** [github.com/nord-riot/KALE](https://github.com/nord-riot/KALE) · **Yayınlanan sürüm:** v1.8
