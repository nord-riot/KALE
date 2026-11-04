# Güvenlik, mahremiyet ve kapsam sınırları

**KALE v1.8**, yerel öncelikli afet bilgi ve hazırlık arayüzüdür.

- İlaç kayıtlarının **707'si de doğrulanmamış editoryal taslaktır**; bunlardan tedavi, doz veya ilaç seçimi çıkarılmamalıdır. Hekim / eczacı doğrulama süreçleri ayrıdır.
- İlk yardım kartları da uzman incelemesi gerektirir. Gerçek acilde **112** aranmalıdır. Zehirlenme şüphesinde Türkiye'de **114** Ulusal Zehir Danışma Merkezi bilgilendirme kaynağıdır.
- Doğa kataloğu tür teşhisi veya yenilebilirlik garanti etmez. Özellikle yabani mantarlar fotoğrafla güvenli tüketim için teşhis edilemez.
- Tarayıcıda saklanan stok, plan ve konum bilgileri cihazda yerel tutulur. JSON dosyaları **şifreli değildir**; herkese açık depolarda paylaşılmamalıdır.
- Sunucu yedekleri doktor inceleme dosyalarını ve kaynak verileri içerebilir; **backups/**, **doctor_reviews.sqlite3**, özel imzalı onay dosyaları GitHub'a yüklenmemelidir.
- Açık internete **TLS/HTTPS ve kimlik doğrulaması olmadan** yayımlamayın. \`0.0.0.0\` kullanıldığında hizmet yerel ağa açılır ve firewall gerekir.
- Harita/veri/lisans şartları ayrıca gözden geçirilmelidir.
- Raspberry Pi OS, gerçek offline ve güç kesintisi sahada henüz doğrulanmadı.

**Kaynak ve görseller:** \`docs/img/*.svg\` şematik tanıtım görselleridir; birebir uygulama ekran görüntüsü değildir. Uygulamanın gerçek ekran görüntüleri tam yayın paketinde \`docs/img/screenshots/\` altına eklenecektir.

Bu belge güvenlik denetimi veya klinik onay raporu değildir.
