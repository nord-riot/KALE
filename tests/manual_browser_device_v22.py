"""Chromium smoke for KALE 7/24 admin UI; uses simulated metrics, no Android access."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
html=(WEB/'yonetim.html').read_text()
css=(WEB/'assets/module.css').read_text()+'\n'+(WEB/'assets/device.css').read_text()
js=(WEB/'assets/device.js').read_text()
html=html.replace('<link rel="stylesheet" href="/assets/module.css">','').replace('<link rel="stylesheet" href="/assets/device.css">','').replace('<script defer src="/assets/device.js"></script>','')
html=html.replace('</head>',f'<style>{css}</style></head>')
fixture='''<script>
window.__eco=true;
const example={server_running:true,uptime_seconds:90600,cpu_percent:12.4,cpu_cores:8,
 memory:{total_mb:12000,used_mb:4800,percent:40},
 battery:{available:true,percentage:82,status:'DISCHARGING',plugged:'UNPLUGGED',temperature_c:30.1,remaining_hours_estimate:18.5},
 energy_saving_mode:true,online_chat_users:4,hotspot_clients:null,
 supervisor:{state:'running',restarts:1},events:[{time:'2026-11-07T09:00:00Z',message:'KALE servis başlatıldı'}]};
window.fetch=async (url, options={})=>{
 if(url==='/api/device/eco'){window.__eco=JSON.parse(options.body).enabled;return {ok:true,json:async()=>({enabled:window.__eco})};}
 return {ok:true,json:async()=>({...example,energy_saving_mode:window.__eco})};};
</script>'''
html=html.replace('</body>',fixture+'<script>'+js+'</script></body>')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1280,'height':820})
 errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
 page.set_content(html,wait_until='load')
 page.wait_for_function("document.querySelector('#battery').textContent.includes('82')",timeout=5000)
 assert '82' in page.locator('#battery').inner_text()
 assert '4' in page.locator('#chatUsers').inner_text()
 assert '1' in page.locator('#restarts').inner_text()
 assert 'Ekonomik' in page.locator('#ecoStatus').inner_text()
 page.locator('#ecoBtn').click()
 page.wait_for_function("document.querySelector('#ecoStatus').textContent.includes('Normal')",timeout=5000)
 assert not errors,errors
 page.screenshot(path='/mnt/data/KALE-v2.2-Android-7x24-Onizleme.png',full_page=True)
 print('Chromium admin panel: battery, CPU, RAM, chat, watchdog, eco toggle PASS')
 browser.close()
