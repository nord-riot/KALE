# KALE offline Türkiye haritası — raster MBTiles

**ZIP küçük kalsın diye ayrıntılı yol/sokak haritası dahil değil.** Gömülü `base-map.json`, kamu malı Natural Earth özet ülke haritasıdır; detaylı yol ve gerçek rota içermez. Kullanıcı önceden edindiği lisansı uygun raster MBTiles dosyasını ekler:

```bash
# Haritayı doğrula; dosya değişmez
python3 tools/map_pack.py /dosya/turkiye.mbtiles
# Üretici gerçek SHA-256 sağladıysa ayrıca doğrula
python3 tools/map_pack.py /dosya/turkiye.mbtiles --sha256 GERCEK_64_HANELI_SHA256
# Kur (varsa önceki dosya üzerine yazılmaz)
python3 tools/map_pack.py /dosya/turkiye.mbtiles --install
```

**Yalnız raster PNG/JPEG/WebP**, zoom 0-18 desteklenir; PBF vektör paketleri desteklenmez. `--install --replace` mevcut haritayı `turkiye.mbtiles.previous` yedeğine taşıyarak değiştirir. Araç SQLite bütünlük, tablo/kolon, karo imzası ve zoom kontrollerini yapar; **harita coğrafi doğruluğunu, güncelliğini, lisansını** garanti etmez. `--sha256` yalnız güvenilir veri sağlayıcısının yayınladığı değerle doğrulanabilir.

Hazır offline paket seçeneği için [Geofabrik tile packages](https://www.geofabrik.de/maps/tile-packages.html) incelenebilir; **satın alma/indirme koşulları, biçim, bölge ve lisans sağlayıcıya bağlıdır**. OpenStreetMap Foundation'ın standart `tile.openstreetmap.org` sunucusundan **toplu karo indirerek offline harita oluşturmak yasaktır:** https://operations.osmfoundation.org/policies/tiles/ . Verinin gerektiği atıfları (ör. © OpenStreetMap contributors) kullanıcının kaynak/lisans koşullarına göre koru.

Kayıtlı noktalara kuş uçuşu açısı ve mesafe hesabı, internetsiz çalışır; **yol güzergâhı, arazi güvenliği, patika uygunluğu ve dönüş tarifleri sağlamaz**. Afet sonrası yol ve köprüler değişebilir.
