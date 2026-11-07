# KALE v2.4 — Türkiye Sokakları / Tek Kurulum

- **Shortbread renderer düzeltildi:** `streets`, `street_labels`, `water_polygons`, `buildings`, `place_labels` ve benzeri katmanlar doğru işlenir. OpenMapTiles mevcut geriye dönük destek korundu.
- **Tek komut Termux kurulum:** `deploy/bootstrap-termux.sh` + `deploy/install-all-termux.sh` otomatik paket, kaynak, harita, rota, başlatıcı ve uygulama kurulumu; yarım indirme/eksik veri başarısız sayılır.
- **Güvenli indirici:** HTTP Content-Length kontrolü, uyumlu Range/ETag doğrulamasıyla kaldığı yerden devam etme; yeniden indirme idempotent, geçerli harita ZIP'i açıldıktan sonra disk alanı geri alınır.
- **BRouter ZIP:** Sürüm numarası içeren `brouter-*.jar` adını da destekler.
- **Android rota:** 7/24 gözetim başlatıcısı BRouter verisi ve Java bulunduğunda motoru da açar. Enerji için `KALE_ENABLE_BROUTER=0` ile kapatılabilir.
- **Cihazlar:** Servis erişimi telefon `127.0.0.1:8090`, diğer cihazlar `telefon-hotspot-IP:8090`.

**Sınırlar:** Gerçek Türkiye büyük veri indirme/Redmi donanım testi burada yapılmadı; yalnız sentetik Shortbread karo ve sistem testleri doğrulandı. İlk kurulum için internet gereklidir; sonrasında yerel kullanım internetsizdir. Harita © OpenStreetMap katkıcıları, ODbL.
