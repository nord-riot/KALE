# KALE — İçerik denetimi ve anlaşılır rehber genişletmesi
Tarih: 7 Kasım 2026

## Yapılan değişikliklerin kapsamı

| Alan | Kayıt |
| --- | ---: |
| Ana bilgi merkezi rehber açıklamaları | 146 |
| Görselli saha rehberleri | 28 |
| Barınak / su | 18 |
| Gıda / enerji / kış | 24 |
| İlk yardım | 24 |
| Zehirli bitki farkındalık kayıtları | 28 |
| Tehlikeli mantar farkındalık kayıtları | 16 |
| **Toplam** | **284** |

- 146 ana katalog girdisinin **472 adım açıklaması**, önceki alakasız/genel “Neden böyle?” metinlerinden konuya uyumlu, güvenlik öncelikli açıklamalara dönüştürüldü.
- Diğer dört uygulamalı modülde **373 adım** için “Ne demek?” / “Nasıl kontrol ederim?” başlıkları, uygulama provası, durma kriteri ve bitiş kontrolü eklendi.
- Saha sayfasının `field.js` dosyası daha önce JSON içindeki `details` alanını göstermiyordu; artık tüm açıklamaları modalda gösteriyor.
- Bitki ve mantar kayıtlarında günlük karşılaşma, yutmadan/temastan korunma, 114 ve 112, yanlış teşhis ve halk inanışları başlıkları genişletildi.
- Kaynak alanı boş iki saha kartına GPS.gov ve CDC kaynakları eklendi.
- `tools/audit_content.py` şema, ID, kaynak alanı, detay doluluğu ve klinik taslak uyarılarını denetler.
- Çevrimdışı önbellek sürümü yenilendi, eski metinlerin PWA önbelleğinde kalmasının önüne geçilmesi hedeflendi.

## İlaç ansiklopedisi için önemli sınır

**707 ilaç kaydının farmakolojik, klinik veya reçete verileri burada tek tek
uzman doğrulamasından geçirilmedi ve değiştirilmedi.** İlaçların doz,
etkileşim, kontrendikasyon, gebelik ve özel hasta risklerini topluca tahmin
ederek üretmek güvensiz olur. Mevcut ilaç modülündeki açıklamalar uzman
tarafından doğrulanmadıkça bireysel kullanım kararı için kullanılmamalıdır.
Bu alan ayrıca eczacı/hekim incelemesine ihtiyaç duyar.

## Kayıtlar neden otomatik “uzman onaylı” değil?

Metinlerin genişletilmesi klinik uygunluk veya gerçek afet saha doğrulaması
anlamına gelmez. Tüm tıbbi/ilk yardım/bitki/mantar kayıtları uzman denetimi
bekleyen editoryal içeriktir. Yeni açıklamalar mevcut kaynakların yerini
almaz; internet yokken bile okunması için yerelde saklanır.

## İçerik testi

```bash
cd ~/KALE
git pull --ff-only
python3 tools/audit_content.py
python3 server.py --selftest
```

Başarılı şema/doluluk testi, kaynak bağlantılarının güncel olması, resmî
kurumların tüm önerileriyle birebir uyumluluk veya gerçek cihaz üzerinde
görsel test yapıldığı anlamına gelmez.

Referans çerçevesi:
- [AFAD — Deprem öncesi, anı ve sonrası](https://afad.gov.tr/deprem-oncesi-ani-ve-sonrasi-alabileceginiz-onlemleri-biliyor-musunuz)
- [CDC — Acil durumda su güvenliği](https://www.cdc.gov/water-emergency/about/)
- [CDC — Elektrik kesintisinde gıda güvenliği](https://www.cdc.gov/food-safety/foods/keep-food-safe-after-emergency.html)
- [CDC — Karbonmonoksit güvenliği](https://www.cdc.gov/carbon-monoxide/about/index.html)
- [IFRC — 2025 Uluslararası İlk Yardım Rehberi](https://www.ifrc.org/sites/default/files/2026-03/IFRC%20International%20First%20Aid%2C%20Resuscitation%20and%20Education%20Guidelines%202025.pdf)
