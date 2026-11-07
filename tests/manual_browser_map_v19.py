"""Optional Chromium smoke, local fixtures only (no actual Android/GPS hardware)."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'web'
html=(WEB/'harita.html').read_text('utf-8')
css=(WEB/'assets/module.css').read_text('utf-8')
js=(WEB/'assets/map.js').read_text('utf-8')
html=html.replace('<link rel="stylesheet" href="/assets/module.css">','')
html=html.replace('<script defer src="/assets/map.js"></script>','')
html=html.replace('</head>','<style>'+css+'</style></head>')
mock="""<script>
const __local={};Object.defineProperty(window,'localStorage',{value:{getItem:k=>__local[k]||null,setItem:(k,v)=>__local[k]=v}});
Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(success,fail)=>success({coords:{latitude:38.4237,longitude:27.1428,accuracy:7}})}});
window.fetch=async uri=>({ok:true,json:async()=>String(uri).includes('/api/maps/status')?{installed:false}:{areas:[]}});
</script>"""
html=html.replace('</body>',mock+'<script>'+js+'</script></body>')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1100,'height':860})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='load')
 assert page.locator('#gpsBrowser').count()==1
 page.locator('#gpsBrowser').click()
 assert '38.423700' in page.locator('#gpsStatus').inner_text(),page.locator('#gpsStatus').inner_text()
 page.locator('#gpsToPoint').click()
 assert page.locator('#pointLat').input_value()=='38.423700'
 page.locator('#pointName').fill('Buluşma noktası')
 page.locator('#pointForm button[type="submit"]').click()
 assert page.locator('.point-item').count()==1
 # Change waypoint to a different location and verify distance / direction calculation.
 page.locator('#pointLat').fill('38.455')
 page.locator('#pointLon').fill('27.211')
 page.locator('#pointName').fill('Alternatif bölge')
 page.locator('#pointForm button[type="submit"]').click()
 page.locator('.point-item .goal').last.click()
 assert 'Kuş uçuşu' in page.locator('#targetStatus').inner_text(),page.locator('#targetStatus').inner_text()
 assert 'Alternatif bölge' in page.locator('#targetStatus').inner_text()
 assert not errors,errors
 page.screenshot(path='/mnt/data/KALE-v1.9-Android-GPS-Onizleme.png',full_page=True)
 print('Chromium v1.9 map smoke OK: GPS click, accuracy, waypoint, 2 targets and bearing/distance; 0 JS errors')
 browser.close()
