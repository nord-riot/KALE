# KALE v2.2 — Android/Termux 7/24 Sunucu

- Termux:Boot ile otomatik başlatma dosyası: `deploy/install-24x7.sh`.
- Otomatik yeniden başlatma, log rotasyonu, tek örnek kilidi, wake-lock: `tools/kale_supervisor.py`.
- Yalnız yerel cihazdan erişilebilen `/yonetim.html` paneli; `/api/device/status` ve `/api/device/eco`.
- `device_monitor.py`: Termux:API batarya, Android CPU/RAM; öznel pil süresi uydurmaz.
- 7/24 ve HyperOS sınırlamalarını anlatan `docs/ANDROID-24X7.md`.
- Mevcut offline rehberler, ilaç taslakları, Wi-Fi sohbeti, Türkiye haritası ve BRouter entegrasyonu korunmuştur.
- **Açık:** Gerçek Redmi Note 14 Pro'da 24/48/72 saat test; hotspot reboot sonrası yeniden açılma (Android iznine bağlı), 3–5 client testi.
