# KALE v1.7 — İlk yardım merkezi için klinik inceleme planı

**Durum: Klinik onay alınmadı.** Bu sürümdeki 24 kart yalnızca editoryal/kamusal kaynak derlemesidir. Her kartta kaynak bağlantısı bulunması, adımların bir hekim/ilk yardım eğitmeni tarafından ürün/vaka bazında kontrol edildiğini göstermez.

## İnceleme ekibinden istenenler

1. Acil sağlık hekimi / yetkin ilk yardım eğitmeni, her kartı mevcut **Türkiye** uygulaması ve 2025/2026 uluslararası yönergeleriyle karşılaştırmalı.
2. Yetişkin, çocuk, bebek, gebe, travma ve bilinç bozukluğu durumları ayrıştırılmalı. Her yaş için tek bir genel teknik varmış gibi yazılmamalı.
3. Sıralama, uyarılar, ne zaman 112 aranacağı, hangi durumlarda 114'ün yalnızca danışma hattı olduğu açıkça doğrulanmalı.
4. Kurtarıcı güvenliği, hava yolu, CPR/AED, kanama, anafilaksi ve zehirlenmeler **yüksek öncelikle** gözden geçirilmeli.
5. Gerekirse kart metni düzeltilmeli; her düzeltme yeni sürüm numarası, kaynak, tarih ve inceleyen adıyla kayıt altına alınmalı.
6. Test eğitimlerinde kartlar gerçek ilk yardım becerisi yerine geçirilmemeli; eğitim maketleri ve sertifikalı eğitmen kullanılmalı.

## Alanlar

- `id`: KALE ilk yardım kayıt kimliği (`KALE-AY-01` … `KALE-AY-24`)
- `signs`: tanı koymayan farkındalık belirtileri
- `steps`: kaynaklardan derlenmiş ilk adımlar
- `avoid`: kaçınılması gereken hatalar
- `call112`: olayın acil tıbbi yardım eşiklerini özetleyen uyarı
- `sources`: başvuru kaynağı ve URL
- `review_status`: **her zaman editoryal taslak, klinik uzman onayı yok**
- `reviewed_by`: `null`, hiçbir uzman onayı iddiası yok

## Başlıca kaynaklar

- Türkiye acil hatları: https://pursaklardh.saglik.gov.tr/TR-36699/acil-durum-telefonlari.html
- Türkiye UZEM: https://www.saglik.gov.tr/TR-11518/114-uzem.html
- Resuscitation Council UK 2025: https://www.resus.org.uk/professional-library/2025-resuscitation-guidelines/adult-basic-life-support-guidelines
- AHA/Red Cross 2024 İlk Yardım: https://cpr.heart.org/en/resuscitation-science/2024-first-aid-guidelines
- American Red Cross CPR: https://www.redcross.org/take-a-class/cpr/performing-cpr/cpr-steps
- NHS yanık ve şiddetli reaksiyon: https://www.nhs.uk/conditions/burns-and-scalds/ ve https://www.nhs.uk/conditions/anaphylaxis/

Klinik kayıtlar `web/assets/first-aid.json` içindedir. Şemalar kaynak kodu olarak `web/assets/diagrams/aid-*.svg` içindedir. Metinler değiştirildiğinde Service Worker önbellek sürümü artırılarak tarayıcıların eski kritik bilgiyi saklaması önlenmelidir.
