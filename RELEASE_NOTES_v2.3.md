# KALE v2.3 — Saha Rehberlerini Genişletme

- 146 / 146 ana rehberin tümüne özgün başlığa özel saha uygulama notları eklendi.
- Her rehber artık temel açıklama, saha uygulama planı, hazırlık/ekipman, kontrol listesi ve kritik hata/sınır içerir.
- Ortalama rehber uzunluğu yaklaşık 253 karakterden 1102 karaktere yükseltildi; yalnız görünüş büyütülmedi, SQLite kataloğu ve arama indeksi güncellendi.
- Telefon ekranındaki modal, güvenli metin DOM API'leriyle bölümlere ayrıldı. Bu yalnızca sunumu değiştirir, HTML çalıştırmaz.
- Seçili deprem, su ve yanık rehberlerine AFAD/CDC/WHO konusal referansları eklendi.
- İlaç arşivindeki 707 kaydın doğrulama statüsü DEĞİŞMEDİ. 24 ilk yardım kartının klinik incelemesi de tamamlanmış sayılmaz.
- Android 7/24 sunucu, Wi-Fi sohbeti, GPS ve offline harita bileşenleri korundu.
- Kaynak: `data/content.json`; yeniden derleme: `python3 tools/build_db.py`.
- Yeniden üretilebilir editoryal genişletme: `python3 tools/expand_field_manual_v23.py`.

**Tıbbi içerik uyarısı:** Tüm rehberler editoryal taslaktır; hekim/eczacı/ilk yardım eğitmeni onayı yoktur. Afet sırasında tek bilgi kaynağı olarak kullanmayın.
