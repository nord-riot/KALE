# KALE — 7 Kasım 2026 içerik ayrıntı ve kapsam denetimi

## Kapsam

- **146 ana bilgi merkezi rehberi**: her biri mevcut metin korunarak ayrı `data/guide-expansions.json` kaydından ayrıntılı ek anlatım alır. Ekler şu başlıkları kapsar: konuyu anlama, hazırlık, temel adımların nedenleri, özel tehlikeler, örnek durum, bitiş kontrolü ve sınırlar.
- **28 saha rehberi**: mevcut adımlara ek, başlığa özel örnekler ve anlaşılır açıklamalar.
- **18 barınak-su rehberi**: malzemeler, her adımın amacı, örnek durum, durma koşulları, bitiş kontrolü.
- **24 gıda-enerji-kış rehberi**: işlem sırası, malzeme/enerji güvenliği, yanlış kararlar ve sınırlar.
- **24 ilk yardım kartı**: belirtiler, kaynaklı mevcut adımların ne amaçla yapıldığı, yapılmaması gerekenler, 112'ye aktarılacak bilgiler, örnek durum. Klinik uzman onayı **henüz yoktur**.
- **28 zehirli bitki + 16 tehlikeli mantar kaydı**: tehlike farkındalığı, ortam, maruziyet şüphesinde güvenli yardım çağrısı ve yanlış teşhis uyarıları. Tür teşhisi veya yenilebilirlik iddiası yapılmaz.
- **İlaç ansiklopedisi**: her ilaç kartının 11 bilgi başlığının neyi ifade ettiği, bilgi eksikliğinin ne anlama gelmediği ve ilaç kayıtlarının nasıl doğrulanacağı ayrıntılı açıklandı. **707 ilacın tamamı tek tek klinik kaynakla doğrulanmış değildir**; yeni doz, etkileşim, kontrendikasyon veya ilaç seçimi hükmü uydurulmadı.

Toplam ayrı ayrıntı bulunan rehber/doğa kaydı: **284**. İlaçlar ayrı klinik denetim kapsamındadır.

## Veritabanı korunması

KALE'nin `data/kale.db` veritabanı **yeniden yazılmadı**. `server.py`
`data/guide-expansions.json` dosyasını salt okunur yükler ve
`id + tam başlık` eşleşirse yalnız döndürülen API metnine ek yapar.
Kullanıcının SQLite içeriği ve varsa yerel metin düzenlemeleri korunur.

### Kapsamı kontrol et

```bash
cd ~/KALE
python3 tools/audit_guides.py
python3 server.py --selftest
```

Kapsam testi kart/adet/ek metin varlığını denetler. **Kaynakları, tıbbi veya
botanik gerçekliği bağımsız doğrulamaz.** İlaçlar için hekim/eczacı, ilk yardım
için eğitmen/hekim ve botanik/mikoloji için uzman incelemesi gerekir.

### Telefonda güncelle

```bash
pkg install -y curl
curl -fsSL https://raw.githubusercontent.com/nord-riot/KALE/main/deploy/bootstrap-termux.sh | bash
```

Kurulum gerekirse çevrimiçi harita/rota paketlerini de denetler. Çevrimdışı
sadece içerik kontrolü için `python3 tools/audit_guides.py` çalışır.

## Editoryal sınırlar

Bu sürümün hedefi eski kısa kartları adım adım anlaşılır kılmak ve kapsam
boşluklarını işaretlemektir. Bu dosyalar özgün metni otomatik olarak tıbbi
rehber veya AFAD onaylı bir kılavuz hâline getirmez. Konuyla ilişkili resmi
kaynaklar ve gerçek saha koşulları önceliklidir; yeni kaynak/uzman onayı
yalnız ayrıca doğrulandıktan sonra kayda eklenebilir.

Özellikle **kimyasal kirli suyu kaynatma, yabani mantarı tüketme, kapalı
alanda jeneratör/mangal kullanma, kontrolsüz ilaç deneme** gibi tehlikeli
önerilerden kaçınılır.
