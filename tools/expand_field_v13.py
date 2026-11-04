#!/usr/bin/env python3
"""Add original, conservative nature-safety field guides and schematic SVGs."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
root=Path(__file__).resolve().parents[1]
p=root/'web/assets/field-guides.json'
d=json.loads(p.read_text('utf8'))
assert len(d['guides'])==24
url='https://www.saglik.gov.tr/TR-55310/mantar-zehirlenmeleri-uzerine-yapilan-basin-aciklamasi.html'
purl='https://www.poison.org/articles/wild-mushroom-warning'
examples=[
('Yabani mantarın tehlike işaretleri değil, güvenlik kararı','Doğa güvenliği',[
 'Şekil, renk, koku veya hayvanların yiyip yememesi güvenli tüketim ölçütü değildir.',
 'Tehlikeli ve tehlikesiz türler birbirine çok benzeyebilir; telefondaki fotoğrafla teşhis ve uygulama tahmini yeterli değildir.',
 'Kaynatma, kurutma veya pişirme tüm mantar toksinlerini etkisizleştirmez.',
 'Yabani mantarı tüketme; gıda için etiketi ve son kullanma tarihi olan güvenilir kültür ürünü seç.'
],'Yabani mantarlar için KALE hiçbir tüketim tavsiyesi vermez.',url),
('Şüpheli mantar yendiyse ilk bildirim','Doğa güvenliği',[
 'Şüpheli mantar yenmişse belirti başlamasını beklemeden 112 ve 114 ile iletişime geç.',
 'Yeme zamanı, miktar, etkilenen kişi sayısı ve mevcut belirtileri not al.',
 'Kişiyi kusturmaya, evde panzehir veya bitkisel tedavi denemeye çalışma.',
 'Kalan ürün veya fotoğraf varsa güvenli biçimde sağlık ekiplerine ilet.'
],'Belirti olmaması güvenli olduğu anlamına gelmez; karaciğer ve böbrek hasarı gecikmeli görülebilir.',url),
('Çocuklar ve hayvanlar için yabani bitki önlemleri','Doğa güvenliği',[
 'Bahçe ve oyun alanındaki tanınmayan mantarları küçük çocukların erişebileceği yerde bırakma.',
 'Tanınmayan meyve, yaprak, tohum veya süs bitkilerini gıda olarak kullanma.',
 'Temas ve olası tüketim olayında bitkinin fotoğrafı veya ambalaj bilgisi varsa kaydet.',
 'Zehirlenme şüphesinde 112 veya 114 üzerinden profesyonel yardım iste.'
],'Bitki veya mantarın “doğal” olması toksik olmadığını göstermez.',purl),
('Etiketli kültür mantarını güvenli değerlendirme','Gıda',[
 'Yabani mantar yerine ambalajlı, etiketi bulunan kültür ürünlerini tercih et.',
 'Ambalaj bütünlüğü ve son kullanma tarihini kontrol et; şüpheli ürünü kullanma.',
 'Uygun saklama ve temiz gıda hazırlama kurallarına uy.',
 'Şüpheli belirti varsa tüketimi durdur ve gerekirse sağlık desteği al.'
],'Etiketli ürün bile bozulabilir; çiğ tüketim ve uygunsuz saklama gıda güvenliği riski yaratabilir.',url)
]
for title,cat,steps,warning,ref in examples:
 idx=len(d['guides'])+1;fname=f'/assets/diagrams/guide-{idx:02d}.svg'
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 280" role="img" aria-label="{escape(title)} şematik güvenlik adımları"><rect width="680" height="280" rx="16" fill="#10262d"/><path d="M0 54H680M0 245H680" stroke="#4b6167"/><text x="28" y="33" fill="#a7d2c5" font-family="Arial" font-size="14" letter-spacing="2">KALE / DOĞA GÜVENLİĞİ</text><text x="24" y="89" fill="#f2e6d3" font-family="Arial" font-size="21">{escape(title)}</text><g fill="none" stroke="#e2c28a" stroke-width="3"><rect x="35" y="112" width="180" height="111" rx="13"/><rect x="249" y="112" width="180" height="111" rx="13"/><rect x="463" y="112" width="180" height="111" rx="13"/><path d="M218 165h27m-7-6 7 6-7 6M432 165h27m-7-6 7 6-7 6"/></g><g fill="#eccd96" font-size="35" font-family="Arial" text-anchor="middle" font-weight="bold"><text x="125" y="177">01</text><text x="339" y="177">02</text><text x="553" y="177">03</text></g><g fill="#b2c9c7" font-size="11" font-family="Arial" text-anchor="middle"><text x="125" y="204">ŞÜPHEYİ TANIMA</text><text x="339" y="204">RİSKİ ÖNLEME</text><text x="553" y="204">UZMAN YARDIMI</text></g><text x="28" y="262" fill="#abbdc0" font-size="12" font-family="Arial">Şematik eğitim görseli — tür tanımlama resmi değildir</text></svg>'''
 (root/'web'/fname.lstrip('/')).write_text(svg,'utf8')
 d['guides'].append({'id':idx,'title':title,'category':cat,'diagram':fname,'steps':steps,'warning':warning,
  'sources':[{'url':ref,'title':'Sağlık Bakanlığı / Poison Control mantar zehirlenmesi bilgilendirmesi'}],
  'review_status':'EDİTORYAL TASLAK','updated':'2026-11-03'})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
print('Field guides',len(d['guides']))
