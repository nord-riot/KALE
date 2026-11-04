#!/usr/bin/env python3
"""Reproducible, conservative nature hazard-awareness catalogue. No edibility labels."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'web/assets/poisonous-plants.json'
M=ROOT/'web/assets/dangerous-mushrooms.json'
health='https://www.saglik.gov.tr/TR-55310/mantar-zehirlenmeleri-uzerine-yapilan-basin-aciklamasi.html'
poison='https://www.poison.org/articles/wild-mushroom-warning'
medical='https://www.merckmanuals.com/home/injuries-and-poisoning/poisoning/plant-and-shrub-poisoning'
plants=[
 # name, Latin, broad non-specific setting, non-identifying warning
 ('Porsuk','Taxus baccata','Park / orman / süs','Özellikle bitkinin bazı parçaları ciddi kalp ritmi bozukluğuna neden olabilen toksinler içerir.'),
 ('Orman gülü','Rhododendron ponticum','Orman / süs','Bitkinin bazı kısımları toksik olabilir; grayanotoksin maruziyeti tansiyon ve kalp ritmini etkileyebilir.'),
 ('Sütleğen','Euphorbia spp.','Kır / bahçe','Sütümsü özsuyu deri ve gözlerde güçlü tahriş oluşturabilir; özellikle göz temasına dikkat.'),
 ('Yılan yastığı','Arum spp.','Kır / gölgelik','Bitkinin bazı kısımları kalsiyum oksalat kristalleriyle ciddi ağız ve boğaz tahrişine yol açabilir.'),
 ('Duvar sarmaşığı','Hedera helix','Park / bahçe / orman','Özellikle meyvelerinin tüketimi mide-bağırsak yakınmalarına yol açabilir; duyarlılık değişebilir.'),
 ('Ökse otu','Viscum album','Ağaç üzerinde / doğal alan','Özellikle meyve ve diğer parçaları toksik olabilir; ağızdan kullanım güvenli değildir.'),
 ('Defne kirazı / karayemiş','Prunus laurocerasus','Bahçe / çalı','Yaprak ve çekirdek gibi parçalarda siyanür açığa çıkarabilen bileşikler bulunabilir; meyve güvenliğiyle karıştırma.'),
 ('Sarı salkım','Laburnum anagyroides','Bahçe / süs','Tohum ve bitkinin bazı parçaları sitizin içerir; ciddi zehirlenme oluşturabilir.'),
 ('At kestanesi','Aesculus hippocastanum','Park / bahçe','Tohumları gerçek kestaneyle karıştırılmamalıdır; tüketim zehirlenmeye yol açabilir.'),
 ('İt üzümü','Solanum dulcamara','Bahçe / doğal alan','Meyve ve bitkinin bazı kısımlarının tüketimi alkaloid zehirlenmesi riski oluşturabilir.'),
 ('Dulavrat otu (Daphne)','Daphne mezereum','Bahçe / doğal alan','Meyve ve bitki kısımları kuvvetli tahriş ve zehirlenme riski taşıyabilir.'),
 ('Yabani marul sanılan yüksük türleri','Digitalis spp.','Bahçe / doğal alan','Kalp glikozitleri bakımından riskli cins; yalnız görünüme bakarak bitkiyi tanımak güvenli değildir.'),
 ('Düğün çiçeği','Ranunculus spp.','Çayır / doğal alan','Bazı türlerin taze özsuyu deri ve mukozalarda belirgin tahrişe yol açabilir.'),
 ('Çöpleme','Helleborus spp.','Bahçe / doğal alan','Bazı türlerin tüketimi ağır mide-bağırsak ve kalp belirtilerine yol açabilir; bitki güvenli gıda değildir.'),
 ('Adamotu','Mandragora spp.','Doğal alan','Tropan alkaloitleri içerebilir; ciddi sinir sistemi ve kalp etkilerine yol açabilir.'),
 ('Köpek üzümü ve benzerleri','Solanum spp.','Bahçe / doğal alan','Bu cins içinde toksik tür ve bitki bölümleri bulunur; görünen meyveyi güvenli sanma.'),
]
existing=json.loads(P.read_text('utf-8'))
assert len(existing['plants'])==12 and {x['id'] for x in existing['plants']}==set(range(1,13))
new=existing['plants'][:]
for name,latin,habitat,warning in plants:
 id=len(new)+1
 new.append({'id':id,'name':name,'latin':latin,'habitat':habitat,'warning':warning,
 'source':'Merck Manual — bitki zehirlenmesi genel başvuru','source_url':medical,'consumable':False,
 'review_status':'BOTANİK / TIBBİ KONTROL GEREKİR','group':'bitki','region':'Bölgesel dağılım doğrulanmadı','expert_verified':False})
for x in new:
 x.setdefault('group','bitki');x.setdefault('region','Bölgesel dağılım doğrulanmadı');x.setdefault('expert_verified',False)
 assert x['consumable'] is False
existing.update(format='KALE-plant-catalogue-v1.3',scope='Risk farkındalığı; hiçbir kayıt tüketim izni, bölgesel tür teyidi veya fotoğraftan teşhis sağlamaz',plants=new)
P.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n','utf-8')

# Group-level toxin effects are not species-identification tools or treatment recommendations.
mushrooms=[
 ('Ölümcül köygöçüren','Amanita phalloides','Amatoksin / ağır karaciğer hasarı ihtimali'),
 ('Ölüm meleği grubu','Amanita virosa','Amatoksin / ağır karaciğer hasarı ihtimali'),
 ('İlkbahar amanitası','Amanita verna','Amatoksin / ağır karaciğer hasarı ihtimali'),
 ('Küçük galerina','Galerina marginata','Amatoksin / ağır karaciğer hasarı ihtimali'),
 ('Küçük lepiota','Lepiota brunneoincarnata','Amatoksin / ağır karaciğer hasarı ihtimali'),
 ('Örümcek mantarı','Cortinarius orellanus','Orellanin / gecikmiş böbrek hasarı ihtimali'),
 ('Kırmızı örümcek mantarı','Cortinarius rubellus','Orellanin / gecikmiş böbrek hasarı ihtimali'),
 ('Yalancı kuzugöbeği','Gyromitra esculenta','Gyromitrin / ciddi nörolojik ve organ toksisitesi ihtimali'),
 ('Kırmızı sinek mantarı','Amanita muscaria','Merkezi sinir sistemi etkileri; güvenli tüketim veya hazırlama yöntemi yok'),
 ('Panter mantarı','Amanita pantherina','Merkezi sinir sistemi etkileri; bilinç değişikliği ve zehirlenme'),
 ('Huni mantarı grubu','Clitocybe rivulosa','Muskarinik zehirlenme / aşırı salgı, terleme, ciddi belirtiler'),
 ('Lifli mantar grubu','Inocybe spp.','Bazı türlerde muskarinik zehirlenme / ağır belirtiler'),
 ('Zeytin mantarı grubu','Omphalotus olearius','Ciddi mide-bağırsak zehirlenmesi riski'),
 ('Ağulu çıntar sanılabilen mantar','Entoloma sinuatum','Ciddi mide-bağırsak zehirlenmesi riski'),
 ('Kıvrık şapkalı mantar','Paxillus involutus','Ağır bağışıklık ilişkili reaksiyon ve hemoliz ihtimali'),
 ('Sarı lekelenen agarik','Agaricus xanthodermus','Mide-bağırsak zehirlenmesi riski'),
]
records=[]
for i,(name,latin,risk) in enumerate(mushrooms,1):
 records.append({'id':i,'name':name,'latin':latin,'group':'mantar','danger_type':risk,
  'habitat':'Doğal alanlarda karşılaşılabilen grup; türün yerel dağılımı teyit edilmedi',
  'region':'Bölgesel dağılım doğrulanmadı',
  'warning':'Doğadan toplanan mantarlarda benzer türler ciddi şekilde karıştırılabilir. '+risk+'. Yeme, deneme, tadına bakma; pişirme toksinleri güvenilir biçimde yok etmez.',
  'source':'Sağlık Bakanlığı — mantar zehirlenmeleri', 'source_url':health,
  'additional_source_url':poison,'consumable':False,'expert_verified':False,
  'review_status':'MİKOLOG / HEKİM ONAYI BEKLİYOR'})
M.write_text(json.dumps({'format':'KALE-mushroom-hazards-v1','scope':'Toksik mantar tehlike farkındalığı; yenilebilirlik sınıflandırması değildir','mushrooms':records},ensure_ascii=False,indent=2)+'\n','utf-8')
print(f'Plant alerts {len(new)} / mushroom alerts {len(records)} / total {len(new)+len(records)}')
