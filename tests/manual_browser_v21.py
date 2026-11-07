"""Test the real UI code against simulated BRouter/Shortbread data.
This does NOT verify phone hardware or a downloaded Turkey dataset.
"""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def varint(v):
 r=bytearray()
 while v>127:r.append((v&127)|128);v>>=7
 r.append(v);return bytes(r)
def f(n,b,w=2):return varint(n*8+w)+(varint(len(b))+b if w==2 else varint(b))
feature=f(2,b'\x00\x00')+f(3,2,0)+f(4,b'\x09\x80\x20\x80\x20\x0a\x80\x20\x00')
layer=f(1,b'transportation')+f(2,feature)+f(3,b'class')+f(4,f(1,b'primary'))+f(5,4096,0)+f(15,2,0)
tile=f(3,layer)
raw_b64=base64.b64encode(tile).decode()
html=(WEB/'harita.html').read_text()
css=(WEB/'assets/module.css').read_text()
for fpath in ['/assets/module.css','/assets/vector-tile.js','/assets/map.js','/assets/route.js']:
 html=html.replace('<link rel="stylesheet" href="'+fpath+'">','').replace('<script defer src="'+fpath+'"></script>','')
html=html.replace('</head>','<style>'+css+'</style></head>')
route={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'LineString','coordinates':[[27.14,38.419],[27.15,38.425],[27.16,38.43]]},'properties':{'track_length_m':2350,'total_time_s':2100}}]}
script='''<script>
const storage={};Object.defineProperty(window,'localStorage',{value:{getItem:k=>storage[k]||null,setItem:(k,v)=>{storage[k]=v}}});
window.fetch=async uri=>{
 const u=String(uri),answer=(d)=>({ok:true,json:async()=>d});
 if(u.includes('/api/route?'))return answer(__ROUTE__);
 if(u.includes('/api/route/status'))return answer({ready:true,segments_found:10,segments_required:10,engine_online:true});
 if(u.includes('/api/street/status'))return answer({installed:true,name:'TEST TILE — not real OSM',format:'pbf',minzoom:3,maxzoom:14,size_bytes:600000000});
 if(u.includes('/api/maps/list'))return answer({maps:[{id:'turkiye',installed:true,name:'Test raster',minzoom:3,maxzoom:8,format:'png',size_bytes:200000}]});
 if(u.includes('/api/maps/status'))return answer({installed:false});
 if(u.includes('/api/street/tiles/'))return {ok:true,arrayBuffer:async()=>Uint8Array.from(atob('__B64__'),c=>c.charCodeAt(0)).buffer};
 if(u.includes('/assets/base-map.json'))return answer({areas:[]});
 return answer({});
};
</script>'''.replace('__ROUTE__',json.dumps(route)).replace('__B64__',raw_b64)
html=html.replace('</body>',script+'<script>'+(WEB/'assets/vector-tile.js').read_text()+'</script>'+'<script>'+(WEB/'assets/map.js').read_text()+'</script>'+'<script>'+(WEB/'assets/route.js').read_text()+'</script></body>')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1100,'height':900},accept_downloads=True)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='load')
 page.wait_for_function("document.querySelector('#mapStatus').textContent.includes('SOKAK HARİTASI AKTİF')",timeout=8000)
 print('Loaded synthetic vector tile:',page.evaluate('window.KALEVector.decode(new Uint8Array('+str(list(tile))+')).map(l=>l.name)'))
 page.locator('#routeFind').click()
 page.wait_for_function("document.querySelector('#routeResult').textContent.includes('GERÇEK YOL ROTASI')",timeout=5000)
 assert '2.4 km' in page.locator('#routeResult').inner_text()
 with page.expect_download() as dl:page.locator('#routeExport').click()
 obj=json.loads(dl.value.path().read_text())
 assert obj['features'][0]['geometry']['coordinates'][1]==[27.15,38.425]
 assert not errors,errors
 print('Chromium test PASS: vector decoding+painting, map choice, BRouter route drawing & GeoJSON download (SIMULATED FIXTURES).')
 b.close()
