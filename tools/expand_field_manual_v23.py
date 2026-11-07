#!/usr/bin/env python3
"""KALE v2.3 editorial expansion of 146 guides.
Idempotent: expanding an already expanded record is a no-op. Source content
remains editorial/unreviewed. Edit FOCUS and CATEGORY, then run this script;
then run tools/build_db.py to regenerate the SQLite search catalog.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'data/content.json'

# Per-area practical context. Applied alongside *topic-specific* instructions below.
CATEGORY={
'ACİL':(
'ÖNCELİK VE EKİPMAN',
'Yakın tehlike değerlendirmesi yap; güvenliyse sağlam ayakkabı, el feneri, düdük, küçük ilk yardım çantası ve suyu yanına al. Telefonun fenerini sürekli kullanmak yerine bağımsız ışık kaynağı bulundur. Tek başına tehlikeli yapıya girme.',
'5 DAKİKALIK KONTROL',
'Çıkış güvenli mi? Elektrik/gaz/su kaynaklı risk var mı? Yanında çocuk, yaşlı veya yardıma muhtaç kişi var mı? Telefon şarjı, alternatif buluşma yeri ve en yakın güvenli açık alan belli mi?',
'Yalnız başına enkaz kaldırma, gaz kaçağına yakın elektrik düğmesine dokunma, güvenli olduğundan emin olmadığın binaya geri dönme.'),
'BARINAK':(
'MALZEME VE ALAN',
'Branda veya su geçirmez örtü, ip, sağlam bağlantı noktası, yer yalıtımı için mat ve kuru yedek kıyafet hazırla. Önce düşen dal, sel yatağı, gevşek taş, devrilme riski ve rüzgâr yönünü kontrol et. Çıkış kapatılmamalı.',
'GECE KONTROLÜ',
'Zemin kuru mu? Su akışı barınağın altına yöneliyor mu? Bağlar rüzgârla gevşedi mi? Havalandırma korunuyor mu? Islak malzemeler uyku alanından uzak mı?',
'Kapalı barınakta ocak, mangal veya kömür yakma; karbonmonoksit fark edilmeden öldürebilir. Ağaç altına yıldırım veya dal düşmesi riski varken yerleşme.'),
'SU':(
'HAZIRLIK VE AYIRMA',
'Gıdaya uygun kap, temiz kapak, ölçü kabı ve mümkünse iki ayrı bidon kullan: “işlenmemiş” ve “içilebilir”. Bulanık suyu dinlendirip temiz bezden geçirmek yalnız ön işlem sayılır; tek başına dezenfeksiyon değildir.',
'İÇMEDEN ÖNCE KONTROL',
'Kaynağın yakınında yakıt, kimyasal, kanalizasyon veya sel bulaşması var mı? Arıtılmış su temiz ve kapalı kapta mı? İşleme tarihi belli mi? Kaynatmak kimyasal ve radyoaktif kirliliği gidermez.',
'Şüpheli dere, sel veya endüstriyel çevredeki suyu tadına/kokusuna bakarak güvenli ilan etme. Güvenli su yoksa sağlık otoritelerinin yönlendirmesine öncelik ver.'),
'ATEŞ':(
'GÜVENLİ ISI PLANI',
'Önce kuru katman, rüzgâr kesici, mat/yer yalıtımı ve sıcak yiyeceği değerlendir; açık ateş son seçenek olmalı. Yakıt, ateş kaynağı ve söndürme malzemesini birbirinden ayrı düzenle.',
'KULLANIM SONRASI',
'Ateş veya ısıtıcı tamamen sönmüş mü, çevre sıcak kül içeriyor mu, yanıcı malzeme kaldı mı? Uykuya geçmeden ısı kaynağını söndür; bir kişi ısıdan etkilenmişse bilincini ve solunumunu kontrol et.',
'Kapalı oda, çadır, araç içinde mangal, kömür veya kamp ocağı kullanma. Karbonmonoksit alarmı olsa bile havalandırma eksikliği güvenli kabul edilemez.'),
'GIDA':(
'MALZEME VE STOK KONTROLÜ',
'Ellerin ve hazırlama yüzeylerinin temizliğini sağla. Hazır yenebilir gıdaları çiğ et/balıktan ayır; temiz su ve ayrı kesme yüzeyi bulundur. Envanterde ürün, miktar, son tüketim ve açılma tarihini yaz.',
'TÜKETMEDEN ÖNCE',
'Ambalaj sağlam mı, saklama sıcaklığı biliniyor mu, küflenme/şişme/sızıntı var mı? Şüpheli gıdayı tatma; bozulmuş gıdayı ısıtmanın her riski gidereceğini varsayma.',
'Bilinmeyen yabani bitki, mantar veya hayvan ürününü deneme. Gıda kıtlığı, zehirlenme riskini göze almak için güvenli neden değildir.'),
'BÖLGE':(
'BÖLGESEL HAZIRLIK',
'Bulunduğun yerde sel yatağı, orman yangını yaklaşım hattı, toplanma alanı, arazi yüksekliği ve ana/alternatif yol seçeneklerini önceden çevrimdışı haritada işaretle. Mevsim ile gündüz/gece sıcaklığını birlikte değerlendir.',
'YEREL DURUM KONTROLÜ',
'Yağış, rüzgâr, yükselti, dere seviyeleri ve ulaşım engelleri değişebilir. Sabit harita bilgi verir ama yeni heyelanı, çöken köprüyü veya kapalı yolu kendiliğinden bilemez.',
'Bölge adından tek başına güvenlik sonucu çıkarma; güncel yerel koşulları ve yetkili uyarılarını dikkate al.'),
'HİJYEN':(
'TEMİZ-KİRLİ BÖLGE AYIRIMI',
'İçme suyu, yemek hazırlama, tuvalet ve atık alanlarını birbirinden ayır. Temiz su azalınca hijyeni tamamen bırakmak yerine el temizliği ve gıda temas yüzeylerine öncelik ver.',
'GÜNLÜK DENETİM',
'Sabun/temiz su mevcut mu? Kaplarda kapak var mı? Çöpler haşere çekiyor mu? Tuvalet çevresinden içme suyu alanına yüzey akışı oluyor mu? Her görevin sorumlusu belirli mi?',
'Çiğ et bulaşmış malzemeyi içme suyu kabında yıkama. Klorlu temizlik ürünlerini birbirleriyle veya asitle karıştırma.'),
'İLETİŞİM':(
'MESAJ HAZIRLIĞI',
'Kâğıda aile adları, iki buluşma noktası, öncelikli telefon numaraları ve bir dış bölge irtibatı yaz. Şebeke yokken Wi-Fi/LAN sohbeti yalnız aynı yerel ağa bağlı kişiler arasında çalışır.',
'HABERLEŞME KONTROLÜ',
'Kim, nerede, kaç kişi, sağlık durumu, hangi yardım gerekli ve sonraki kontrol saati bilgilerini kısa ilet. Bilgiyi aktardığın saati not et; eski mesaj yeni durum sanılmamalı.',
'Ruhsatsız frekanslarda veya izin gerektiren telsiz kanallarında keyfi yayın yapma; önemli bilgiyi söylenti olarak yayma.'),
'ENERJİ':(
'ENERJİ ENVANTERİ',
'Cihaz etiketi ve adaptöründen güç (W), batarya kapasitesi (Wh) ve çıkış gerilimini not et. Güneş, powerbank ve şebeke girişini ayrı düşün. İlk kaynakları telefon, ışık ve haberleşmeye ayır.',
'BAĞLANTI KONTROLÜ',
'Kablo ısınıyor mu, batarya şişmiş mi, kutup yönü doğru mu, güneş paneli gölgede mi? Nem/yağmur ve açıkta metal bağlantılara dikkat et; hatalı bağlantıyı zorlamadan sök.',
'Sonradan rastgele voltaj yükseltme, çıplak batarya uçlarını kısa devre etme veya lityum hücreleri koruma devresi olmadan doğrudan şarj etme.'),
'NAVİGASYON':(
'HARİTA HAZIRLIĞI',
'Türkiye sokak haritasını ve rota segmentlerini internet varken indir. Ev, toplanma alanı, su noktası, sağlık birimi ve alternatif yollar için koordinat sakla. Çevrimdışı GPS konum bulabilir; harita verisi yine cihazda olmalı.',
'YOLA ÇIKMADAN',
'Harita güncelleme tarihi, kalan pil, arazinin eğimi, köprü/akarsu geçişi ve dönüş planını kontrol et. En az bir kişi hedefi ve dönüş zamanını bilsin; gerçek yol durumu haritada görünmeyebilir.',
'Kuş uçuşu mesafeyi yürünebilir rota diye kabul etme. GPS doğruluğu düşerse koordinatı kontrol etmeden tehlikeli arazide ilerleme.'),
'ONARIM':(
'BAKIM EKİPMANI',
'İş eldiveni, gözlük, pense, uygun tornavida, ip, yedek bağlantı ve işaretleme bandı bulundur. Onarımdan önce enerji, sıcak yüzey, keskin kenar ve kontaminasyon riskini ortadan kaldır.',
'ONARIM SONRASI TEST',
'Düşük riskli ortamda önce boş yük/düşük basınç testi yap. Sızıntı, gevşeme veya ısınma varsa kullanımı durdur. İşlem sırasında oluşan hasarı kayıt altına al.',
'Elektrikli sistemi enerjiliyken kurcalama. Kimyasal kap, yakıt bidonu veya kirli plastik kabı “içme suyu” amaçlı onarma.'),
'TOPLULUK':(
'KÜÇÜK GRUP DÜZENİ',
'En az iki kişi birbirini kontrol etsin; su, stok, sağlık ve haberleşme sorumlularını belirle. Yazılı kayıt kullan; kritik bilgiler tek kişinin telefonunda kalmasın.',
'GÜNLÜK TOPLANTI',
'Kim nerede, kimin yardıma ihtiyacı var, su/gıda kaç gün yeter, yeni risk nedir, bir sonraki kontrol saati ne? Kısa not tut ve doğrulanmamış bilgiyi işaretle.',
'Özel sağlık bilgilerini herkese açık sohbet kanalında paylaşma. Yardım isteyen kişileri izinleri dışında fotoğraflayıp dağıtma.'),
'SAĞLIK':(
'GÜVENLİ İLK DEĞERLENDİRME',
'Ortam güvenliğini sağla, kişinin yanıt verip vermediğini ve normal solunumunu değerlendir. Türkiye’de acil yardım için 112’yi ara. Bilinci, nefesi, durumun başlangıç zamanı ve görülen değişiklikleri kısa not et.',
'YARDIM GELENE KADAR',
'Kişiyi gereksiz taşımadan, güvenli ortamda tut; kötüleşmeyi izle. Bilinç kaybı, solunum güçlüğü, ağır kanama, yeni gelişen felç bulgusu veya ciddi alerji acil değerlendirme gerektirir.',
'Tanı koymaya ya da reçeteli ilaç seçmeye çalışma. Buradaki metin profesyonel ilk yardım eğitimini veya hekim değerlendirmesini yerine geçirmez.'),
'İLAÇ':(
'İLAÇ KULLANIMINDAN ÖNCE',
'Kutudaki tam ürün adı, etken madde, form/güç, son kullanım, saklama koşulu, alerji ve kişinin mevcut hastalık/ilaçlarını birlikte kontrol et. Aynı etken maddenin birden fazla üründe bulunabileceğini unutma.',
'KAYIT VE UYARI',
'İlacı kullanan kişide yeni döküntü, solunum sorunu, bayılma, bilinç değişikliği gibi ciddi belirtilerde acil yardım gerekir. Klinik açıdan güvenilir doz, yaş sınırı ve etkileşim bilgisi için güncel ürün KÜB/KT veya sağlık profesyoneli gerekir.',
'KALE ilaç kartları hekim/eczacı onaylı değildir; rastgele antibiyotik, insülin veya kan sulandırıcı kullanımı önerisi olarak okunmamalıdır.'),
'HAKKINDA':(
'OFFLINE SINIRLARI',
'KALE telefonun kendi belleğinden çalışır; web sayfası, su ve barınak rehberleri internet olmadan açılabilir. Yerel Wi-Fi sohbeti için kullanıcıların aynı KALE ağına bağlanması gerekir; internet mesajlaşması sağlamaz.',
'İŞLETME KONTROLÜ',
'Kendi telefonunda localhost ile sayfayı aç; diğer cihazda telefonun hotspot IP adresini ve 8090 portunu kullan. Haritalar yalnız indirilen bölgeyi kapsar, GPS ve rota farklı hizmetlerdir; Android pili ve hotspot davranışı cihaz sürümüne bağlıdır.',
'Sağlık/ilaç rehberleri bağımsız tıbbi doğrulamadan geçmemiştir; gerçek riskte 112 ve profesyonel yardım önceliklidir.'),
}

# Detailed, unique field observations for EVERY existing guide, by stable ID.
FOCUS={
1:'İlk dakikada herkesin sayımını yap: kim dışarıda, kim içeride, kim yaralı? Ağır tehlike varsa eşya toplamayı bırak. Çıkış güvenliyse tek buluşma noktasına geç; artçı sarsıntı, cam ve enerji hatlarına mesafe koy. İletişim için kısa konum mesajı hazırla.',
2:'Bir kâğıda saat, yer, kişi sayısı, yaralılar, kullanılabilir su, güvenli uyku alanı, enerji ve haberleşme durumunu yaz. Listeyi iki kişi doğrulasın. Her değişiklikte önce tehlike ve güvenli çıkış maddelerini yeniden kontrol et.',
3:'Alanı önce gündüz incele, sonra yağış suyunun nereden akacağını düşün. Dere yatağı, kaya dibi, kuru ağaç ve gevşek toprak kötü seçenektir. Sabit bir işaret belirle; gece karanlığında çıkış ve tuvalet yolunu kaybetme.',
4:'A tipi barınakta branda sırt hattını sağlam iki noktaya bağla; yan etekleri yere sabitle. Bir uçtan giriş bırak, gerginliği yağışa göre ayarla; su biriken cepleri gider. Altına mat/kuru katman koy, doğrudan ıslak zeminde yatma.',
5:'Önce zeminin suyu tutup tutmadığını kontrol et. Mat, kuru giysi veya uygun köpük katmanlar temasla ısı kaybını azaltır. Islak eşyanın uyku tulumuna değmesini engelle; gündüz ıslanan yalıtımı ayrı kurut.',
6:'Rüzgâr yönünü gözle, girişini doğrudan rüzgâra çevirmemeye çalış. Yağmurda zeminden akan suyu barınaktan uzak düşün; sıcak havada gölge ile hava akımını birlikte koru. Nem birikimi için iç yüzeyi denetle.',
7:'Öncelik kapalı ambalajlı su veya bilinen güvenli şebeke kaynağıdır. Akarsu temiz görünse bile mikroorganizma içerebilir. Sel, akaryakıt, fabrika veya tarım kimyasalı yakınından gelen suyu mikroplarından arındırmak tek başına yeterli değildir.',
8:'Görünür parçacıkları çöktür veya temiz bezle süz. Suyu güçlü kaynamaya getirip en az 1 dakika kaynat; 2.000 metreyi aşan yükseklikte 3 dakika uygula. Temiz, kapaklı kaba aktarırken kirli kepçe kullanma. Kimyasal kirlilikte bu yöntem işe yaramaz.',
9:'Bir filtrenin “0,1 mikron” gibi değeri her virüsü giderdiği anlamına gelmez. Ürünün bakteri, protozoa ve virüs için ayrı sertifikasyonunu oku. Filtre çıkışına kirli ellerle temas etme; filtreleme sonrası ek dezenfeksiyon gerekebilir.',
10:'Sıvı kaybı şüphesinde içebiliyorsa küçük ve sık yudumlarla güvenli su veya uygun ORS verilebilir; ancak bilinç bozukluğu olan kişiye ağızdan sıvı verme. Az idrar, aşırı susama, baş dönmesi ve halsizlik kötüleşme işaretidir.',
11:'Kapağa, musluk ağzına ve aktarım kabına kirli el değdirme. İçme ve temizlik bidonlarını açık yazıyla ayır. Eski yakıt/kimyasal kaplarını temizleyerek içme suyu kabına çevirmeye çalışma; son dolum tarihini etiketle.',
12:'Soğuğa karşı önce rüzgârı kes ve yere temas eden alanı yalıt; kuru çorap önemli olabilir. Tek kalın katman yerine hava tutan kuru katlar kullan. Kontrolsüz ateş, hipotermiyi tedavi etmekten çok yeni risk yaratabilir.',
13:'Açık ateş için yerel yangın yasağı, rüzgâr ve yakın bitki örtüsünü değerlendir. Ateş tamamen külleşse bile kömürün sıcak kalabileceğini unutma. Su ve söndürme aracı yoksa ateş yakma; kapalı alanda kesinlikle kullanma.',
14:'Kapaklı tencere ısı kaybını azaltır; küçük porsiyonlar hazırlamak yakıt yönetimini kolaylaştırır. Kullanılan ocak türünün açık alan koşullarına uygun olması gerekir. Ocağı çadır/araç içine taşıyarak “yakıt tasarrufu” yapma.',
15:'Termal yanığı mümkünse serin akan suyla yaklaşık 20 dakika soğut; kişi genel olarak üşümemeli. Sıkı yüzükleri erken çıkar; deriye yapışmış kumaşı çekme. Geniş, derin, elektrik/kimyasal yanıkta ve yüz/eller etkilendiğinde acil yardım al.',
16:'Önceliği suya ve saklama koşulu güvenilir hazır gıdaya ver. Hangi öğünün kaç kişiye yeteceğini basit tabloyla hesapla. Açılmış paketleri tarihleyerek önce bozulma ihtimali yüksek olanları değerlendir; güvensiz gıdayı “israf olmasın” diye tüketme.',
17:'Ekipman azsa önce mevcut güvenli gıda stokunu koru; balık tutmayı tek geçim planı yapma. Yerel yasakları, suyun kirlilik durumunu ve yenilebilirliğine kesin emin olduğun türleri değerlendir. Temizleme araçlarını gıda hazırlama alanından ayrı tut.',
18:'Tuzak ve av faaliyetleri insanlara, evcil hayvanlara ve korunan türlere zarar verebilir. Yerel mevzuata uy; bilinmeyen yaralı hayvana yaklaşma. Tuzak kurmaktan daha güvenli seçeneklerin stok/yardımlaşma olup olmadığını gözden geçir.',
19:'Benzer görünümlü zehirli türler olduğu için “bir yaprağa benziyor” ölçütü yeterli değildir. Tek fotoğraf veya yapay zekâ çıktısıyla güvenli tüketim kararı verme. Çiğ veya pişmiş deneme yapma; güvenilir gıda kaynağına dön.',
20:'Mantarların zehri pişirme ve kurutma ile güvenilir şekilde giderilmez. Şüpheli mantardan uzak dur; tüketim sonrası belirti olmasa bile ciddi zehirlenme gecikmeli başlayabilir. Şüphede acil tıbbi yardım al ve örneği güvenle sakla.',
21:'Çiğ et/balık ile hazır yenebilir malzemeyi ayrı kap ve kesme araçlarıyla işle. Gözle “pişti” demek her üründe güvenilir değildir; uygun gıda termometresi tercih et. Elleri ve yüzeyi tekrar kirletmemeye dikkat et.',
22:'Solunum güçlüğü, ağır kanama, bilinç kaybı, yeni gelişen felç bulgusu veya göğüs ağrısı acildir. 112 çağrısında tam konum, yaş aralığı, mevcut tehlike ve belirtilerin başladığı zamanı bildir. Yardım gelene kadar durumu takip et.',
23:'Karın ağrısının yeri, kusma, ateş, kanlı dışkı, su içebilme ve idrar sıklığını not et. Şiddetli ağrı, kanlı dışkı, bilinç değişikliği veya susuzluk belirtilerinde gecikmeden sağlık yardımı al. Rastgele ishal kesici kullanma.',
24:'Döküntü ve kaşıntı tek başına hafif olabilir; dudak/dil şişmesi, nefes darlığı, bayılma ve hızlı kötüleşme acildir. Bilinen tetikleyiciden uzaklaş; reçete edilmiş acil ilaç varsa kişinin kendi acil planını izle ve 112’yi ara.',
25:'Önce kendi güvenliğini ve el hijyenini sağla; aktif kanamada temiz malzemeyle doğrudan sürekli basınç uygulamak temel adımdır. Ciddi kanama veya durmayan kanamada 112. Kirli yarayı kapatmadan önce profesyonel değerlendirme gerekebilir.',
26:'Titreme, yavaş konuşma, koordinasyon bozulması veya dalgınlık soğuk etkisini düşündürebilir. Kişiyi rüzgârdan çıkar ve ıslak katları güvenle değiştir. Ağır durumlarda hızlı/yoğun ısıtma denemeleri yerine acil yardım sağla.',
27:'Ateşin ne zaman başladığını, eşlik eden döküntü, solunum, bilinç ve sıvı alımını not et. Giderek kötüleşme, ense sertliği, bilinç bulanıklığı veya nefes darlığı acildir. İlaç kararını yaş ve sağlık durumunu bilmeden verme.',
28:'İlaç kutusunun kapağı, son tüketim tarihi ve kullanım amacı belli değilse kullanma. Etken maddeyi tam tanımla; tablet kırma, doz bölme ve benzer isimli ilaçları eşdeğer sayma. Başkasına ait reçeteli ilacı verme.',
29:'Parasetamol içeren soğuk algınlığı kombinasyonlarıyla aynı etken maddenin tekrarlanması ciddi karaciğer hasarına neden olabilir. Kutudaki etken maddeleri karşılaştır; aşırı alım şüphesinde belirti beklemeden 112’ye başvur.',
30:'İbuprofen gibi NSAİİ’ler mide-bağırsak kanaması, böbrek sorunu ve bazı hastalık/ilaçlarla etkileşim riski taşıyabilir. Susuz kalmış veya kanama riski olan kişi için kendi kendine ilaç seçimi yapma.',
31:'Loperamid her ishal için uygun değildir; ateş, kanlı dışkı veya şiddetli karın ağrısı varsa durumu ilaçla gizleme. Susuzluk riskini ve güvenli sıvı erişimini önceliklendir; küçük çocukta profesyonel görüş gereklidir.',
32:'Setirizin bazı kişilerde uyku hâli yapabilir. Araç kullanımı, diğer sedatif ilaçlar ve böbrek hastalığı gibi durumlar önemlidir. Anafilaksi bulgularında antihistaminik tek başına acil tedavinin yerini tutmaz.',
33:'ORS doğru miktarda temiz suyla hazırlanmalıdır; oranı kafadan değiştirmek güvenli değildir. Paketin üzerindeki karıştırma talimatına uy. Bilinç bozukluğu veya içememe varsa ağızdan uygulamaya çalışmadan sağlık yardımı al.',
34:'Ege ve Akdeniz’de kıyıya yakın alçak bölgeler, yaz orman yangını hattı ve sıcaklık ayrı risklerdir. Deniz kıyısında deprem sonrası olağandışı su hareketinde sahilden hızla uzaklaşıp yüksek alana çık.',
35:'Karadeniz’de yoğun yağışta dere debisi çok hızlı yükselebilir. Yamaçta yeni çatlak, kaya düşmesi ve anormal su sızıntısı heyelan uyarısı olabilir. Sel suyuna araçla veya yaya girme.',
36:'İç/Doğu Anadolu’da gece ile gündüz sıcaklığı ve yüksek rakım yanıltıcı olabilir. Yola çıkarken kuru katman, su, yedek ışık ve dönüş saatini planla; kışın rüzgâr ve görüş kaybı rotayı bozabilir.',
37:'Bu sistem internetli arama motoru değildir: içerik güncellemesi önceden indirilmelidir. Rota motoru, harita verisi ve GPS üç ayrı bileşendir. Wi-Fi sohbeti diğer kişilerin KALE ağında olmasını gerektirir; tıbbi onay verilmemiştir.',
38:'Sarsıntı anında bulunduğun yerde korunma; koşarken merdiven veya asansöre yönelme. Sağlam bir eşyanın yanında çök-kapan-tutun ve baş-boyun bölgesini koru. Dışarıdaysan bina cephesi ve enerji hatlarından uzaklaş.',
39:'Sarsıntı sonrası çatlak, eğilme, dökülme, gaz kokusu ve kopmuş hatlara bakarken güvenli mesafeyi koru. Yapısal güvenlik gözle bakarak kesin belirlenemez; hasarlı binaya eşya almak için geri girme.',
40:'Duman varsa aşağıdan daha temiz hava bulunabilir; kapalı kapının arkasındaki yangını kontrolsüz açma. Güvenli çıkış varken eşya toplama. Yangın büyümüşse müdahaleye çalışma, uzaklaş ve 112’ye haber ver.',
41:'Taşkın suyunun hızı ve derinliği gözle anlaşılamaz. Köprü/menfez ve dere yataklarından uzak dur; yüksek ve sağlam yere çık. Elektrik hattı, kanalizasyon veya kimyasal kirlilik taşıyan suya girme.',
42:'Kıyıda güçlü veya uzun deprem, denizin aniden çekilmesi ya da yükselmesi doğal tsunami uyarısı olabilir. Resmî uyarıyı beklemeden kıyıdan uzaklaş ve yüksek yerlere yönel; ilk dalgadan sonra sahile dönme.',
43:'72 saatte kişi sayısı üzerinden günlük suyu ve ilaç gereksinimini hesapla. En az 3 günlük güvenli içme suyu, kolay bozulmayan gıda ve ışık bulundur. Aynı çantaya bütün kaynakları doldurup tek yerde kaybetme riskini azalt.',
44:'İki buluşma yeri belirle: ev yakınında güvenli açık alan ve daha uzak alternatif. Aile bireyleri için bir mesaj şablonu oluştur: “Konum, iyiyim/yardım gerekli, sonraki haber saati”. Kâğıt kopya sakla.',
45:'Tahliye sırasında çocukları bir yetişkine eşleştir; yaşlı ve hareket kısıtlı kişiler için daha yavaş rota planla. Kimlik, düzenli ilaç ve yardımcı cihazları önceden paketle. Koşuşturma yerine sayımla ilerle.',
46:'Gaz kokusunda elektrik anahtarına, prize, çakmağa veya telefona tehlikeli alan içindeyken müdahale etme. Güvenle mümkünse vanayı kapat, herkesle dışarı çık ve açık alandan yetkili birimi ara. Kaçağı alevle test etme.',
47:'Enkazda hareket, toz ve yeni çökme riski vardır. Gereksiz bağırmak yerine uygun anlarda düdük/sesle konum bildir; ağzını-burnunu tozdan koru. Kendi başına ağır parçaları oynatmak boşluğu çökertebilir.',
48:'Alan seçmeden önce yukarı bak: kuru dal, gevşek kaya, yıkılabilecek duvar var mı? Sonra aşağıya bak: su yolu, gevşek zemin, çukur var mı? Yakınında tuvalet ve su alanına güvenli mesafe bulunmalı.',
49:'Alçak barınak rüzgâra direnç sağlayabilir ancak giriş ve havalandırma daralmamalıdır. Branda gerilimini kontrol et, başın örtüye temas etmesin, yağmur suyunun yanlardan akacağı hat bırak.',
50:'İpin malzemesini ve aşınmış yerlerini önce kontrol et. Düğümü kuru ve ıslak durumda yük vererek yerde test et; can güvenliğini taşıyacak amaçla sıradan kamp ipi/düğümü kullanma. Uçların çözülmeyeceğini kontrol et.',
51:'Toprak ve beton, giysiye göre çok daha hızlı ısı çekebilir. En az bir sürekli kuru yalıtım katmanı ser; eklemlerde boşluk bırakma. Alt yalıtımı, üst örtü kalınlığından bağımsız kontrol et.',
52:'Örtüde oluşan yoğuşmayı yağmur sızıntısıyla karıştırma. Havalandırma bırakırken doğrudan yağmur almamaya dikkat et. Islak ayakkabı ve kıyafeti uyku malzemesinden ayrı konumlandır.',
53:'Rüzgâr yönüne göre daha alçak profil seç; bütün kenarları gergin sabitle. Kırılabilecek ağaç/kuru dallardan uzaklaş. Kontrolsüz rüzgâr varsa barınağı güçlendirmek yerine güvenli yapıya geçmeyi değerlendir.',
54:'Gölgeyi gün içinde güneşin değişen açısına göre planla. Tam kapalı tente altında sıcak hava birikebilir; çapraz hava akımını koru. Su ihtiyacını artıran eforu en sıcak saatlere bırakma.',
55:'Kış barınağında küçük alanı ısıtmak kolay görünse de nem ve karbonmonoksit riskini artırır. Ocağı içeri alma; nemli kıyafeti kurutmak için havalandırmayı kapatma. Kuru zemin ve katmanlar ana stratejidir.',
56:'Girişe yığılmış stok, ip ve çadır kazıkları gece düşmeye neden olabilir. El yordamıyla bulunacak ışık ve çıkış yolu bırak. Toplanma noktasıyla herkesin barınaktan çıktığını say.',
57:'Kaynağı seçerken yerleşim, tarım, sanayi ve sel etkisini ayrı değerlendir. Suyun berrak akması biyolojik güvenliği kanıtlamaz. Kaynak değiştiğinde önceki arıtma varsayımını otomatik aktarma.',
58:'Yağmur suyu için çatı malzemesi, kuş dışkısı, ilk akış ve depolama kabının temizliği önemlidir. İlk kirli akışı ayır; toplamayı içme suyu güvenliğiyle karıştırma. İşlem gerekebileceğini kabul et.',
59:'Bulanık suyun çöktürülmesi veya bezden süzülmesi sadece görünen tortuyu azaltır. Bu su yine mikroorganizma içerebilir. Temizlenmiş görünen suyu uygun dezenfeksiyon olmadan içilebilir sayma.',
60:'Yakıt, pestisit, çözücü ya da radyoaktif madde şüphesinde kaynatmak suyu güvenli yapmaz. İşleme başlamadan önce çevresel kirlenmeyi araştır; güvenli farklı kaynağa geç.',
61:'Yaklaşık 2.000 metre üzerindeki rakımlarda CDC kılavuzu güçlü kaynamadan itibaren 3 dakika önerir; daha alçakta en az 1 dakika. Rakım bilinmiyorsa ve yakıt yeterliyse daha uzun güvenlik marjını tercih et.',
62:'Filtre üzerindeki gözenek, mikroorganizma sınıfları ve kullanım ömrünü ayrı ayrı oku. “Su berraklaştı” testi yeterli değildir. Dondurulmuş veya darbe almış fiber filtre görünmeden zarar görebilir.',
63:'İçme, arıtılmamış ve teknik kullanım suyunu kap ve etiketle ayır. Aktarım hunisi/kepçesi de ayrı olmalı. Depo musluğunu kirli ellerle temas ettirmeden kullan.',
64:'Önce içme, yemek hazırlama ve temel el hijyenini koru. Gıda yıkama ve genel temizlik gibi işler için su kaynağının uygunluğunu ayrıca düşün. Günlük tüketimi kişi bazında kaydet.',
65:'Koyu/az idrar, ağız kuruluğu, baş dönmesi ve belirgin halsizlik susuzluğu düşündürebilir. Bebek, yaşlı ve kronik hastada risk daha yüksek olabilir. Bilinç değişikliği veya içememe acil değerlendirme gerektirir.',
66:'Su kesintisinde yemek öncesi/tuvalet sonrası el temizliğini önceliklendir. İçme suyu kabını ortak bardakla kullanma; musluk ağızlarını temiz tut. Bulaşık ve tuvalet alanını gıda hazırlığından ayır.',
67:'Karbonmonoksit renksiz/kokusuzdur; baş ağrısı, sersemlik, bulantı ve bilinç kaybı yapabilir. Şüphede içeri tekrar girmeden temiz havaya çık ve 112’yi ara. Jeneratör ve mangalı bina girişlerinden uzak tut.',
68:'İç katman teri uzaklaştırsın, orta katman hava tutsun, dış katman rüzgâr/yağışa karşı korusun. Terlemiş katı mümkün olduğunda değiştir. Tüm katmanları sıkıştırmak yalıtım etkisini azaltabilir.',
69:'Islak çorap/ayakkabı dolaşımı ve sıcaklığı etkileyebilir; değiştirilebilen kuru çorap bulundur. Eldivenin ıslanması küçük işlerde bile beceriyi düşürür. Sıkı giysi ve çorap dolaşımı engellememeli.',
70:'Yağışta ateşin duman yönü ve düşen dal riski değişir. Güvenli ocak yüzeyini ve sönme ekipmanını hazırlamadan deneme yapma. Islak yakıtın dumanı içeri kaçıyorsa ocağı iç mekâna taşımak çözüm değildir.',
71:'Hipotermi şüphesinde kişiyi nazikçe hareket ettir, soğuk ve ıslak ortamdan çıkar, kuru katla sar. Bilinç bozulmuşsa ağızdan yiyecek/içecek verme. Ağır belirtilerde acil yardım ve kontrollü izlem gerekir.',
72:'Rüzgâr, ıslak kıyafetten buharlaşmayı hızlandırarak üşümeyi artırır. Barınağın girişini ve uyku alanını rüzgârın doğrudan vurmadığı tarafa düzenle. Teri yönetmek için hareket-katman dengesini koru.',
73:'Baş feneri ve düşük güçte LED ışığı ilk seçenek yap; alevli ışıklar yangın riski taşır. Gece kapı/çıkış hattını işaretle. Yedek pilin kutuplarının metal eşyaya kısa devre yapmayacağından emin ol.',
74:'Şişmiş, sızdıran, paslı veya açılınca anormal fışkıran konserveyi tatma. Botulizm toksini her zaman görünür/kokulu olmayabilir. Şüpheli ürünü başka yiyeceğe bulaştırmadan güvenli biçimde ayır.',
75:'Soğutucu kapılarını gereksiz açma; elektrik kesintisinin saatini yaz. Buzdolabı sıcaklığı ve süre bilgisi yoksa bozulabilir ürünleri “hala soğuk gibi” diye güvenli sayma. Yeniden elektrik gelmesi gıdayı otomatik güvenli yapmaz.',
76:'Kuru gıdayı nem, kemirgen, böcek ve güneşten koruyan kaplarda sakla; açılma tarihini not et. Eski ürün önce kullanılsın ama ambalajı bozuk olanı ayır. Su gerektiren kuru ürünlerle yakıt/su stokunu birlikte hesapla.',
77:'Çiğ etle temas eden bıçak, tezgâh ve elleri hazır yiyecekten ayır. Pişmiş yemeği çiğ etin tabağına geri koyma. Ortak bezin kirli yüzeyiyle kapak veya temiz su kabı silme.',
78:'Tek seferde tüm yemeği ısıtıp tekrar tekrar soğutma. Kapak, tencere boyutu ve rüzgârdan korunan güvenli ocak alanı yakıtı azaltır. Kapalı çadırda yakıt kullanarak tasarruf sağlamaya çalışma.',
79:'Olta, iğne ve misinayı kuru ve kapalı kutuda taşı; çocuk ve hayvan erişiminden uzak tut. Avlandığın suyun kirlilik geçmişini değerlendir. Bilinmeyen türde veya kokusu bozuk balığı tüketme.',
80:'Balığı yakaladıktan sonra serin koşullarda tutmak gerekir; sıcak havada bekleme bozulmayı hızlandırır. Çiğ balık parazit ve bakteri riski taşır. Uygun pişirme, temiz yüzey ve ayrı bıçak kullan.',
81:'Yerel av yasakları ve korunan alanlar afet nedeniyle otomatik kalkmaz. Tuzak insanlara ve evcil hayvana zarar verebilir. İşaretlenemeyen, kontrol edilemeyen tuzakları kurma; stok/yardımlaşma seçeneklerini tercih et.',
82:'Yaprak şekli, çiçek rengi veya telefon fotoğrafıyla kesin tür tanımlaması yapılamaz. “Az miktar deneyip bekleme” güvenli test değildir. Bilinmeyen bitkiyi yemektense güvenilir kuru gıdayı rationla.',
83:'Bazı zehirli mantarlar yenebilir türlere çok benzer. Pişirmek ve suda bekletmek türü güvenli hâle getirmez. Şüpheli mantar yemiş biri belirtileri gecikse de tıbbi değerlendirme almalıdır.',
84:'Kişi sayısı, yaş, hava sıcaklığı, fiziksel efor ve mevcut gıda miktarıyla basit öğün çizelgesi hazırla. Ağır iş yapacak kişiye su/enerji planı ayır. Tıbbi ihtiyaç veya çocuk beslenmesini aynı standarda zorlama.',
85:'İlk sağlık taramasında “yanıt veriyor mu, normal nefes alıyor mu, ciddi kanama var mı” sorularıyla başla. Hasta sayısı, şikâyet başlangıcı ve hangi yardımın gerekli olduğunu kaydet. Uzman eğitimin yoksa müdahale sınırını aşma.',
86:'Yeni göğüs ağrısı, baskı hissi, nefes darlığı veya soğuk terleme acil olabilir. Kişiyi dinlendirmeye al, kendi başına yürütme ve 112’yi ara. Bilinç/solunum değişirse acil ekip yönlendirmesini izle.',
87:'Yüzde kayma, tek kol güçsüzlüğü veya konuşma bozukluğu inme uyarısı olabilir. Belirtilerin ilk başladığı zamanı not et ve 112’yi ara. Belirti kendiliğinden geçse bile tıbbi değerlendirme gerekir.',
88:'Anafilaksi hızlı gelişebilir: boğaz/dil şişmesi, hırıltı, bayılma ve yaygın reaksiyonu izle. Reçeteli otoenjektör taşıyan kişinin acil eylem planına göre hareket et; 112 çağrısını erteleme.',
89:'Kirli su sonrası ishalde aynı suyla bardak/tabak yıkamak bulaşı sürdürebilir. İçme, diş fırçalama ve yemek hazırlama için güvenli su kullan. Susuzluk, yüksek ateş veya kanlı dışkıda sağlık yardımı gerekebilir.',
90:'Yaranın kirli toprak, paslı metal veya hayvan ısırığıyla ilişkisini not et; tetanos/diğer enfeksiyon değerlendirmesi gerekebilir. Giderek artan kızarıklık, şişlik, akıntı veya ateşi izle. Yaraya gelişi güzel madde sürme.',
91:'Yanıkta önce ısı kaynağından uzaklaştır; yaklaşık 20 dakika serin akan suyla soğut, kişinin geri kalanını sıcak tut. Buzu doğrudan temas ettirme. Büyük/derin ya da özel bölgeleri tutan yanıkta acil yardım al.',
92:'Kafa travmasından sonra bilinç kaybı, giderek artan baş ağrısı, tekrarlayan kusma, konuşma bozukluğu veya nöbet acildir. Belirti olmasa da kişi sonradan kötüleşebilir. Boyun yaralanması şüphesinde gereksiz hareket ettirme.',
93:'Aşırı sıcakta bilinç değişikliği, bayılma, yüksek vücut sıcaklığı veya davranış bozukluğu ısı çarpmasını düşündürür. 112 çağır; güvenli serin alana geç ve soğutmayı başlat. Bilinci kapalı kişiye ağızdan sıvı verme.',
94:'Reçeteyi, ilacın tam formunu, kutudaki etken maddeyi ve saklama koşullarını karşılaştır. “Aynı isimli” şurup/tablet/kapsül farklı miktarlar içerebilir. Belirsiz ilaçları kullanım için ayırma.',
95:'Ateşli çocukta zor nefes alma, belirgin uyandırılamama, nöbet, yayılabilen morumsu döküntü ve sıvı alamama acil bulgulardır. İlaç dozunu kilo/yaş bilmeden önerme; 112 veya hekim yönlendirmesi al.',
96:'Sık kusmada su içememe, az idrar, bilinç değişikliği ve şiddetli karın ağrısı kötüleşme işaretidir. Özellikle çocuk ve yaşlılarda susuzluk hızlı olabilir. Baygın kişiye ağızdan sıvı verme.',
97:'Önce kişiyi güvenli ve sakin ortama al; nasıl yardım istediğini sor. Kaygısını küçümseme, zorla olay anlattırma veya gerçek dışı güvence verme. Yakınlarına ulaşmasına ve temel ihtiyaçlarını düzenlemesine destek ol.',
98:'Amoksisilin her enfeksiyona etkili değildir; viral enfeksiyon için kendiliğinden başlanmamalıdır. Penisilin alerjisi ve başka ilaç kullanımı önemlidir. Süre ve doz kararı sağlık profesyoneli tarafından verilmelidir.',
99:'Metronidazolün endikasyonları ve etkileşimleri vardır; “mide bozuldu” diye kullanılmaz. İlaç-alkol etkileşimi ve mevcut hastalıklar için ürün bilgisi doğrulanmalı. Rastgele antibiyotik başlanmamalıdır.',
100:'Doksisiklinin çocuk/gebelik, güneş duyarlılığı ve bazı mineral takviyeleriyle etkileşim yönünden özel uyarıları vardır. Her kene ısırığında otomatik ilaç başlama doğru değildir; klinik değerlendirme gerekir.',
101:'Azitromisin bazı kişilerde kalp ritmiyle ilgili risk ve başka ilaçlarla etkileşim oluşturabilir. Antibiyotik kararını ateş veya boğaz ağrısına bakarak verme; doğru endikasyonu sağlık profesyoneli belirler.',
102:'Omeprazol mide asidi üretimini azaltır, her karın ağrısını tedavi etmez. Yeni alarm belirtileri, uzun süreli kullanım ve etkileşimler için hekim/eczacı görüşü gerekir. Göğüs ağrısını “mide yanması” diye geçiştirme.',
103:'Salbutamol içeren inhalerler yalnız uygun hastaya, reçetelenen yöntemle kullanılmalıdır. Solunum sıkıntısı ağırsa ya da tedaviye yanıt yoksa acil yardım gerekir. Son kullanım, doz sayacı ve cihaz tipini doğrula.',
104:'Adrenalin otoenjektörü ciddi alerji acil planının parçasıdır; cihaz marka ve uygulama tekniği farklı olabilir. Kişinin kendi reçeteli cihaz ve eğitimini esas al. Kullanım sonrası 112 değerlendirmesi gerekir.',
105:'Aspirin kanama riskini artırabilir; çocuklarda ve bazı hastalıklarda özel kısıtları vardır. Göğüs ağrısında kişinin durumunu değerlendirmeden “herkese aspirin” talimatı verme.',
106:'Kan sulandırıcı kullanan kişide kafa travması ve açıklanamayan kanama daha riskli olabilir. İlacı kendi kendine kesmek de tehlikeli olabilir; doz/ara verme kararını klinik destek olmadan verme.',
107:'İnsülin soğuk zincir ve sıcaklık maruziyeti açısından ürüne özeldir; donmuş veya aşırı ısınmış ürünü güvenli sayma. Doz hatası ciddi hipoglisemiye yol açabilir. Reçete ve saklama talimatlarını doğrula.',
108:'Birinci kuşak antihistaminikler daha belirgin uyku hâli yapabilir; farklı ürünler farklı etken madde taşır. İsim benzerliği nedeniyle ilaçları eşdeğer sayma; anafilaksiyi tek başına antihistaminikle yönetmeye çalışma.',
109:'Etken madde, miktar, dozaj şekli, SKT, seri numarası ve saklama talimatını ayrı oku. Muadil/benzer isim kararı sadece marka adına bakılarak verilmemelidir. Bilinmeyen ürünleri ayrı kutuda sakla.',
110:'Ege yazında sıcaklık, kurak ot ve kuvvetli rüzgâr yangını hızlandırabilir. Orman/çalı alanından çıkış yönünü önceden planla. Dumanın geldiği yöne yürümek veya araçla sıkışmış orman yoluna girmek kötü seçenektir.',
111:'Marmara’da deprem sonrası bina ve kıyı sanayi bölgelerinde ikincil tehlikeler olabilir. Toplanma alanı ile alternatif kent dışı rotayı ayrı tut. Köprü ve alt geçit güvenliğini varsayma.',
112:'Akdeniz’de sıcak hava ile ani sağanak/taşkın aynı sezonda yaşanabilir. Kurumuş dere yatakları yağışta hızla su taşıyabilir. Şehir içinde bile alt geçit ve zemin kat girişlerini sel açısından izle.',
113:'Karadeniz’de yamaç yerleşimlerde yağmur sonrası kayma ve kaya düşme riski artabilir. Yeni duvar çatlakları, eğilen ağaçlar veya toprağın akması uyarı olabilir. Dere yatağına kamp kurma.',
114:'İç Anadolu gündüz sıcak, gece çok soğuk olabilir. Tek kıyafet planına güvenme; kuru üst katman ve gece ısı kaybını azaltacak mat hazırla. Açık arazide rüzgârı ayrıca değerlendir.',
115:'Yüksek rakımda soğuk, UV ve nefes darlığı belirtilerini ayırt etmek önemlidir. Yol hesaplarında yükselti ve hava değişimini düşün. Yüksek rakımda su kaynatma süresi değişir.',
116:'Güneydoğu’da sıcak ve su yönetimi kritik olabilir; öğlen eforunu azaltıp gölge ve su stokunu önceliklendir. Açıkta kalmış depolama kabı sıcaklığı ve kirlenmesi izlenmelidir.',
117:'Yemek öncesi ve tuvalet sonrası temiz su-sabunla el yıkamak bulaşmayı azaltır. Su azsa içme/gıda temas alanlarının temizliği önceliklidir. Ortak havlu yerine kişisel temiz malzeme kullan.',
118:'Tuvaleti yaşam ve su alma alanından akış yönü açısından ayır. Yüzey suyu tuvaletten depoya ilerlememeli. Çocukların el temizliği ve atık alanına erişimini kontrol et.',
119:'Lavabo/banyo kaynaklı gri su, arıtma ve kullanım koşulları bilinmeden içme suyuna karıştırılmamalıdır. Depolama kabını işaretle. Tuvalet/kimyasal kaynaklı suyla sebze yıkama.',
120:'Gıda kırıntıları, açık çöp ve duran su haşere çeker. Kapalı gıda kapları kullan, gece atığı toplu tut. Kemirgen izleri varsa gıdayı ayrı değerlendir ve temas yüzeylerini temizle.',
121:'Islak organik atık, keskin metal ve tıbbi atıkları ayrı düşün. Çöp alanı içme/gıda noktasının yanında olmamalı. Kirli atıkla uğraştıktan sonra el temizliğini öncele.',
122:'KALE Wi-Fi sohbeti, Bluetooth dosya paylaşımı, SMS, telsiz ve yazılı not farklı kapsama ve enerji ister. Yakın kişilere yerel ağ, uzak irtibata mümkünse operatör/telsiz kullan. Ağın internet sağlamadığını açıkça bildir.',
123:'Telsiz çağrısında kısa format kullan: çağrılan kişi, gönderen, konum, kişi sayısı, ihtiyaç, saat. Gereksiz uzun konuşma pil ve kanal işgalini artırır. İzin gerektiren kanallarda mevzuata uy.',
124:'Ekran parlaklığını azalt, kullanılmayan uygulamaları kapat ve haritaları internet varken indir. Sunucu olarak çalışan telefonda hotspot ve CPU uyanık tutulması ayrı enerji tüketir; güç tasarrufu modunu test etmeden kullanma.',
125:'Aile iletişim kartına isim, iki buluşma noktası, şehir dışı irtibat, kritik ilaç/özel gereksinim notlarını mahremiyet gözeterek yaz. Kopyalarını kişilere dağıt; tek telefona bağımlı kalma.',
126:'SOS işaretlerinde en görünür ve güvenli yeri seç. Telsiz/ışık/düdük sinyallerinin anlamını grupla önceden kararlaştır. Bir sinyal görünürken gereksiz pil tüketen sürekli flaş kullanma.',
127:'Örnek: 10 W cihaz 5 saat çalışırsa 50 Wh tüketir. Panel etiketindeki W değeri ideal koşuldur; gölge, açı, sıcaklık ve şarj kayıpları gerçek üretimi düşürür. Günlük tüketimle karşılaştır.',
128:'W anlık güçtür, Wh enerji miktarıdır; Ah tek başına Wh değildir, gerilimle birlikte değerlendirilir. Örnek: 5 V × 10 Ah yaklaşık 50 Wh nominal enerji eder; dönüştürme kaybı nedeniyle kullanılabilir miktar daha azdır.',
129:'Şarjda uygun voltaj/kablo ve cihazın kendi koruma devresini kullan. Şişmiş, hasarlı, aşırı sıcak veya ıslanmış bataryayı şarj etme. Kapalı kutuda veya güneş altında kontrolsüz bırakma.',
130:'Jeneratörü ev, çadır ve pencere/kapı yakınında çalıştırma; egzoz karbonmonoksit taşır. Yağmurdan koruma sağlarken havalandırmayı kapatma. Yakıt ikmalini motor kapalı ve soğukken yap.',
131:'Cihaz başına saat ve Wh tahmini oluştur. Öncelik telsiz, telefon, düşük güçlü ışık ve kritik destek cihazları olsun. Güneş üretimi olmayacağı günler için yedek enerji payı ayır.',
132:'USB-C ve USB-A aynı gücü sunmayabilir; cihazın PD/QC gereksinimini kontrol et. Ucu/ek yeri ısınan kabloyu kullanma. Uyumsuz yüksek voltaj kaynağına dönüştürücü olmadan bağlama.',
133:'Haritayı arazideki belirgin çizgilerle eşleştir: ana yol, kıyı, tepe, dere. Pusula çevresinde telefon, mıknatıs veya metal pusula sapmasına yol açabilir. Yön tayinini tek işarete dayandırma.',
134:'GPS yoksa yürüyüşte saat, yön, belirgin dönemeç ve mesafeyi deftere kaydet. Dönüşte aynı izleri ters sırayla takip et; ancak bozuk köprü veya taşkın varsa eski yolu güvenli sayma.',
135:'Koordinat girerken enlem ve boylamın sırasını, negatif işareti ve ondalık ayırıcıyı kontrol et. Farklı formatları karıştırmak kilometrelerce hata yapabilir. Hedefi haritada ikinci kez doğrula.',
136:'Toplanma alanını yalnız isim olarak değil koordinat ve iki rota ile kaydet. Karanlıkta veya yol kapanınca alternatif toplanma alanına geçmek için aileye ortak kural belirle.',
137:'Dik yamaç, düşen kaya, gevşek zemin, hızlı su ve devrilmiş elektrik direği görünür tehlikeleridir. Çamurlu arazide ayak izi yönü yanıltabilir. Şüphede geri dön ve daha güvenli güzergâh ara.',
138:'Küçük tamir setini görev başlıklarına ayır: kesme, sıkma, bağlama, ölçme ve işaretleme. Eldiven ve gözlük olmadan keskin metal veya camı tutma. Her aletin sap/yalıtımını önceden kontrol et.',
139:'Elektrik kaçağı şüphesinde ıslak zemine veya metal yüzeye dokunma. Güvenli noktadan enerjiyi kesebiliyorsan kes; yetkin değilsen arızalı hatta müdahale etme. Elektrik çarpmasında önce kaynağı güvenli biçimde ayır.',
140:'Branda dikişi, kuşgözü ve ipin sürtünen noktalarını düzenli kontrol et. Keskin kenarda koruma kullan; gevşeyen düğümü yük altındayken çözme. Islak ve UV görmüş halatın dayanımı değişebilir.',
141:'İçme suyu kabındaki çatlak onarımla mikroplar için saklanma alanına dönüşebilir. Gıdaya uygunluğu bilinmeyen yapıştırıcı kullanma. Sızıntılı kabı teknik suya ayırmak, temiz içme suyu kabı edinmekten güvenli değildir.',
142:'Görevleri tek kişiye yükleme; yedek sorumlu belirle. Su, sağlık, harita ve enerji durumunu ortak kâğıda yaz. Tüm işlerde tehlikeli işe tek başına gitmeme kuralı uygula.',
143:'Kayıt defterinde tarih, ürün/su miktarı, son tüketim, kim aldı ve kalan miktarı tut. Ölçü birimlerini standartlaştır: litre, kilogram, adet. Kayıp/tüketim hızından sonraki günlerin ihtiyacını hesapla.',
144:'Kaynaksız söylentiye göre tahliye kararı verme. Mesajın zamanı, kaynağı ve iki bağımsız doğrulama imkânı var mı bak. Eski fotoğraf ve haritaları güncel uyarı gibi yayma.',
145:'Çocuklara yaşına uygun kısa bilgi ver, rutin ve güvenli bir görev sun. Görmediği tehlikeleri abartarak anlatma. Aile iletişim planını oyun gibi prova etmek paniği azaltabilir.',
146:'Komşulara güvenli mesafeden ihtiyaç sor; özel sağlık bilgilerini toplu sohbetle yayma. Tek başına tehlikeli binaya girerek yardım etmeye çalışma. Su, şarj ve haberleşme kaynaklarını adil ve kayıtlı paylaş.'
}

RESEARCHED={
8:['https://www.cdc.gov/water-emergency/about/'],
60:['https://www.cdc.gov/water-emergency/about/'],
61:['https://www.cdc.gov/water-emergency/about/'],
43:['https://www.cdc.gov/water-emergency/about/how-to-create-and-store-an-emergency-water-supply.html'],
11:['https://www.cdc.gov/water-emergency/about/how-to-create-and-store-an-emergency-water-supply.html'],
15:['https://www.who.int/news-room/fact-sheets/detail/burns/'],
91:['https://www.who.int/news-room/fact-sheets/detail/burns/'],
38:['https://afad.gov.tr/deprem-oncesi-ani-ve-sonrasi-onlemini-al-guvende-kal'],
39:['https://afad.gov.tr/deprem-oncesi-ani-ve-sonrasi-onlemini-al-guvende-kal'],
42:['https://afad.gov.tr/deprem-oncesi-ani-ve-sonrasi-onlemini-al-guvende-kal'],
89:['https://www.cdc.gov/water-emergency/safety/'],
}


def expand():
    db=json.loads(CONTENT.read_text(encoding='utf8'))
    es=db['entries']
    assert len(es)==146 and set(int(i) for i in FOCUS)=={int(e['id']) for e in es}
    updates=0
    for e in es:
        if '\n\nSAHA UYGULAMA PLANI' in e['body']:
            continue
        if e['category'] not in CATEGORY:raise ValueError(e['category'])
        # Medical fields remain explicitly unapproved, not advertised as validated procedures.
        top,prep,check_title,check,avoid=CATEGORY[e['category']]
        old=e['body'].strip()
        e['body']=f'''TEMEL BİLGİ / MEVCUT REHBER\n{old}\n\nSAHA UYGULAMA PLANI\n{FOCUS[e['id']]}\n\n{top}\n{prep}\n\n{check_title}\n{check}\n\nKRİTİK HATALAR VE SINIRLAR\n{avoid}'''
        e['origin']=(e.get('origin') or 'Editoryal taslak') + ' | KALE v2.3 saha notları'
        # Do not change any clinical review statuses.
        if e['id'] in RESEARCHED:
            e['sources']=list(dict.fromkeys((e['sources'] or [])+RESEARCHED[e['id']]))
        updates+=1
    if updates:
        db['version']='2.3.0'
        db['build_date']='2026-11-07'
        db['notice']='Saha rehberleri editoryal taslaktır. İlaç/ilk yardım içerikleri klinik olarak onaylanmadı; tehlikeli durumlarda 112 ve yetkili kurum uyarıları önceliklidir.'
        CONTENT.write_text(json.dumps(db,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'Updated {updates} entries; {len(es)} total; average length {sum(len(e["body"]) for e in es)//len(es)} chars')

if __name__=='__main__':expand()
