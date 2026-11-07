# KALE — Yerel açık lisanslı / kamu malı görseller

Bu görseller **USGS'nin Public Domain (kamu malı)** olarak işaretlediği
kaynaklardan seçilmiştir. Teknik olarak hepsi 'açık kaynak' lisansı değil,
kamu malı görsel malzemedir. Fotoğraflar KALE şemalarının yerini almaz;
kaynak belirtilerek ek referans olarak gösterilir.

| KALE rehberi | Dosya (ilk kurulumda cihaza indirilir) | Orijinal ve lisans açıklaması |
| --- | --- | --- |
| Deprem sonrası ilk kontrol / sarsıntı sırasında korunma | `web/assets/public-domain/drop-cover-holdon.png` | [USGS — Drop, Cover, and Hold On](https://www.usgs.gov/media/images/drop-cover-and-hold) (Public Domain) |
| Deprem sonrası hasarlı bina kontrolü | `web/assets/public-domain/earthquake-damage.jpg` | [USGS — Earthquake-damaged building](https://www.usgs.gov/media/images/earthquake-damaged-building) (Public Domain) |
| Geçici barınak yeri / heyelan riski | `web/assets/public-domain/landslide.jpg` | [USGS — Landslide](https://www.usgs.gov/media/images/landslide), fotoğraf: Jim Bowers (Public Domain) |

## İndirme (bir kez internet varken)

```bash
cd ~/KALE
python3 tools/install_open_images.py
```

Termux `deploy/install-all-termux.sh` de bu indirmeyi otomatik dener.
İndirmede hata olması asıl KALE şemalarını bozmaz; eksik fotoğraflar
gizlenir, uygulamada saklanan özgün SVG şemalar görünür. Fotoğraf
kaynak bağlantıları internet olmadan açılmaz.

## Harita

Gerçek Türkiye OSM sokak haritası **kodla birlikte GitHub'a konmaz**.
İlk kurulum sırasında indirilen `data/maps/turkiye-street.mbtiles`
gereklidir. Örnek `base-map.json` ülke/coğrafya özeti verir, sokak göstermez.

```bash
cd ~/KALE
python3 tools/turkiye_full.py check
# Kurulum eksikse internet varken:
python3 tools/turkiye_full.py map
```

Telefon tarayıcısında `http://127.0.0.1:8090/harita.html` adresini aç.
Aynı ağdaki başka cihazda `http://TELEFON_IP:8090/harita.html`
kullan. Vektör çizim veya yol rotası için gerçek veri ve BRouter
kurulumunun tamamlanmış olması gerekir. Harita gerçek zamanlı güvenli
tahliye yolunu garanti etmez.
