# KALE — Dokuz Düzenleyici Kurumdan Kaynaklı İlaç Arşivi

**7 Kasım 2026 — kaynak bağlayıcısı; cihazdaki veri aktarımı çalıştırılmadıkça arşiv boş kalır.**

KALE'nin asıl 707 ilaç kaydı ve doktor inceleme verileri **değiştirilmez**. Ayrı
`data/regulatory.sqlite3` içinde ürün adları, etken maddeler, ürün formu, ülke,
kaynak statüsü ve varsa resmî metinler saklanır. Kaynakta olmayan bir bilgi
tahmin edilmez. Kaynak etiketleri orijinal dilinde kalabilir.

## Hangi kurumdan ne alınabilir?

| Kurum | Resmî bilgi | Yerel aktarma |
| --- | --- | --- |
| **FDA (ABD)** | SPL ilaç etiketleri: endikasyon, uyarı, kontrendikasyon, yan etki, etkileşim, saklama ve diğer kaynak alanları | API ile KALE'deki jenerik adlar üzerinden; ayrıca tam openFDA indirilen JSON/ZIP paketleri |
| **TİTCK (Türkiye)** | Haftalık güncellenen *Ruhsatlı Beşeri Tıbbi Ürünler Listesi* (ürün adı, mevcut Excel sütunları) | Resmî siteden son XLSX'i bulup indirme; ayrı KÜB/KT belgeleri henüz toplu aktarılmıyor |
| **EMA (AB/AEA)** | Article 57 geçerli ruhsatlı ürünlerin ad, etken madde, uygulama yolu, ülke, ruhsat sahibi vb. kayıtları | Resmî XLSX otomatik indirme |
| **MHRA (BK)** | İlaç ürün bilgileri, SmPC, PIL ve değerlendirme raporları | Kurumun izinli CSV/XLSX dışa aktarımı verilirse yerel aktarım |
| **PMDA (Japonya)** | Elektronik prospektüs ve değerlendirme raporları (çoğunlukla Japonca) | Resmî CSV/XLSX dosyası verilirse yerel aktarım |
| **Health Canada** | Drug Product Database: ürün, DIN, etken madde, ruhsat/market statüsü | Resmî DPD API'den otomatik; yalnız `Human` sınıfı |
| **TGA (Avustralya)** | Australian Register of Therapeutic Goods, CMI ve PI bağlantıları | Resmî CSV/XLSX dışa aktarımı verilirse yerel aktarım |
| **SFDA (Suudi Arabistan)** | Drug List: ticari/bilimsel ad, form, güç, kayıt statüsü | Resmî CSV/XLSX dışa aktarımı verilirse yerel aktarım |
| **WHO / DSÖ** | Ön yeterlilik değerlendirilmiş tıbbi ürünlerin listesi (tüm dünyadaki tüm ilaçları kapsamaz) | Resmî CSV/XLSX dışa aktarımı verilirse yerel aktarım |

**Kritik ayrım:** FDA SPL kaydı FDA onayı demek değildir. WHO ön yeterlilik,
milli ilaç ruhsatı veya her hastada kullanım izni değildir. Ülke pazarlarına
özel aynı isimli ürünlerin içerikleri ve yardımcı maddeleri farklı olabilir.
KALE hiçbir veriyi otomatik "FDA/TİTCK tarafından KALE onaylandı" şeklinde
işaretlemez.

## Android/Termux tek seferlik ilk çevrimiçi aktarım

```bash
cd ~/KALE
git pull --ff-only
python3 tools/sync_all_regulators.py
python3 -c "from regulatory_core import stats; import json; print(json.dumps(stats(),ensure_ascii=False,indent=2))"
```

- **Otomatik**: FDA (KALE'de adı bulunan ürünler için kaynak adayları),
  Health Canada DPD, TİTCK'nin son resmî ruhsatlı ürün XLSX'i ve EMA Article 57
  XLSX'i denenir.
- **Diğer beş kaynak**: Resmî siteden indirilen dosyayı
  `~/storage/downloads/KALE-KAYNAKLAR` klasörüne
  `MHRA.csv`, `PMDA.xlsx`, `TGA.xlsx`, `SFDA.csv`, `WHO.csv`
  gibi bir adla koy. Yeniden aynı komutu çalıştır. Desteklenen uzantılar CSV
  ve XLSX; her dosyada ürün adı sütunu bulunmalıdır. Kurum kendi toplu dosyasını
  sağlamıyorsa manuel belge incelemesi gerekir.
- Yalnız bir kurumu güncelleme:
  `python3 tools/regulatory_sync.py ema` veya
  `python3 tools/regulatory_sync.py titck`.
- Tek kaynak dosyasını aktarma:
  `python3 tools/regulatory_sync.py import --regulator WHO --file /tam/yol/WHO.csv`.
- Bütün FDA etiketlerini elle indirip kullanma:
  `python3 tools/regulatory_sync.py fda-json --file /tam/yol/fda-zip-klasoru`.
  FDA verileri birçok ZIP dosyasına bölünmüştür; **tam veri** için hepsi gerekir.
- FDA API ücretsiz erişim kotasına tabidir; `OPENFDA_API_KEY` varsa Termux
  ortam değişkeninden kullanılır. Ana ilaca ait klinik onayı asla değiştirmez.

**İlk aktarım için internet gerekir.** Çalışma zamanında kaynak arşivi ve
KALE arama ekranı, telefonun kendi sunucusundan internetsiz okunur.
Resmî dış bağlantıların açılması ise internet gerektirir. Veri dosyaları
boyutlu olabilir; boş depolama alanını önceden kontrol et.

## Kaynaklar

- [FDA openFDA etiket API](https://open.fda.gov/apis/drug/label/)
- [FDA indirilebilir tam veri](https://open.fda.gov/data/downloads/)
- [TİTCK ruhsatlı ürünler listesi](https://titck.gov.tr/dinamikmodul/85)
- [TİTCK KÜB/KT arama](https://titck.gov.tr/kubkt)
- [EMA Article 57 ürün verisi](https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/data-medicines-iso-idmp-standards-post-authorisation/public-data-article-57-database)
- [MHRA ürünler](https://products.mhra.gov.uk/)
- [PMDA prospektüs ve arama](https://www.pmda.go.jp/english/search_index.html)
- [Health Canada DPD API](https://health-products.canada.ca/api/documentation/dpd-documentation-en.html)
- [TGA ARTG](https://www.tga.gov.au/products/regulations-all-products/about-australian-register-therapeutic-goods-artg)
- [SFDA ilaç listesi](https://sfda.gov.sa/en/eservices/19531)
- [WHO ön yeterlilik listesi](https://extranet.who.int/prequal/medicines/prequalified-lists-medicines)

## Sağlık ve lisans notları

Bu uygulama, resmî kurumların **kendilerini** değil, belirli ürün verilerini
kaynaklı biçimde gösterir. Kaynak ve sürüm tarihi saklanır. Farklı statüler
(ruhsatlı, pazarlanan, askıda, iptal, yalnız etiket mevcut) birleştirilmez.
Kurumların veri yeniden kullanım şartları ayrıdır; başka ülke düzenleyici
verisini ticari/promosyon amaçlı yeniden yayınlamadan önce şartlarını kontrol et.
WHO listesi tüm ilaçları kapsamadığı gibi, WHO'nun ticari/promosyon kullanım
kısıtlaması da ayrıca dikkate alınmalıdır.

TİTCK ürün listesi bir KÜB/KT prospektüsünün yerini tutmaz. İngilizce/diğer
dillerdeki kaynaklar otomatik Türkçeye dönüştürülüp reçete kararına bağlanmaz.

**Doktor incelemeleri:** Hekimin onay verdiği mevcut KALE sürümünün kayıtları,
ilgili sürüm, tarih ve imzalı değerlendirme ile ilişkilendirilmeli. Dış kurum
kaynaklarının daha sonra eklenmesi, hekim onayının kapsamına otomatik girmez.
