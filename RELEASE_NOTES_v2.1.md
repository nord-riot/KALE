# KALE 2.1 — Wi-Fi sohbet ve Türkiye sokak/rota altyapısı

## Çalışan kısımlar
- ThreadingHTTPServer + RAM tabanlı Wi-Fi sohbet (isim, kullanıcı listesi, gönder/al, geçici oturumlar).
- GPS, mevcut 146 rehber / 707 ilaç, ilk yardım, envanter, iki gerçek Natural Earth özet MBTiles korunur.
- Vektör Shortbread/MVT (PBF) SQLite karo API ve sade Canvas çizim motoru.
- Yerel BRouter HTTP GeoJSON rota entegrasyonu (yürüyüş `shortest`, bisiklet `fastbike`, araç `car-vario`).
- Termux tek komutla KALE ve varsa yerel BRouter çalıştırma başlatıcısı.
- Türkiye MBTiles + 10 rota RD5 dosyası ve BRouter v1.7.10 önceden indirme aracı.
- Yerel HTTP, sohbet, veri yokken düzgün hata ve vektör MVT sahte test karosu doğrulandı.

## Henüz doğrulanmayanlar / ZIP içeriğinde olmayanlar
- Gerçek BBBike Türkiye Shortbread (~570 MB), BRouter 10 segment (~232 MiB) **ZIP'de yok**; indirme ortamı dış ağa erişemedi.
- BRouter Java dağıtımı bu ortamda indirilmedi ve gerçek `.rd5` üzerinde hesaplama denenmedi.
- Android telefonda LAN, GNSS, Termux Java, pil/kapanma testi yapılmadı.
- Vektör çizici tam MapLibre değildir: basitleştirilmiş yol/yer çizimi, adres arama yok.
- Doğal afet sırasında gerçek yol güvenliği veya canlı kapanma/ trafik bilgisi yok.

Kurulum ve kullanım: `docs/TURKIYE_OFFLINE_NAVIGASYON.md`.
