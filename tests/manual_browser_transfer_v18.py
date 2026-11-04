"""Chromium UI smoke: mocked localStorage; does not need reachable HTTP server."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
html=(WEB/'aktarim.html').read_text('utf8')
css=(WEB/'assets/module.css').read_text('utf8')+'\n'+(WEB/'assets/transfer.css').read_text('utf8')
stock=(WEB/'assets/inventory-core.js').read_text('utf8')
core=(WEB/'assets/sync-core.js').read_text('utf8')
app=(WEB/'assets/transfer.js').read_text('utf8')
for tag in ['<link rel="stylesheet" href="/assets/module.css">','<link rel="stylesheet" href="/assets/transfer.css">',
            '<script src="/assets/inventory-core.js" defer></script>','<script src="/assets/sync-core.js" defer></script>','<script src="/assets/transfer.js" defer></script>']:
    assert tag in html,tag
    html=html.replace(tag,'')
html=html.replace('</head>',f'<style>{css}</style></head>')
fixture={'format':'KALE-STOK-v1','people':3,'perPersonDay':3,'items':[], 'log':[]}
mock='''<script>
const __store={'kale-inventory-v16':__FIXTURE__};
Object.defineProperty(window,'localStorage',{value:{
 getItem:k=>Object.hasOwn(__store,k)?__store[k]:null,
 setItem:(k,v)=>{__store[k]=v;},removeItem:k=>{delete __store[k];}}});
</script>'''.replace('__FIXTURE__',json.dumps(json.dumps(fixture)))
html=html.replace('</body>',mock+f'<script>{stock}</script><script>{core}</script><script>{app}</script></body>')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1100,'height':825},accept_downloads=True)
    errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
    page.set_content(html,wait_until='load')
    assert page.locator('.transfer-slot').count()==6
    with page.expect_download() as info:page.locator('#exportBtn').click()
    out=json.loads(info.value.path().read_text())
    assert out['format']=='KALE-PERSONAL-TRANSFER-v1'
    assert len(out['data'])==1
    assert out['data']['kale-inventory-v16']['people']==3
    print('Chromium transfer export:',info.value.suggested_filename, 'recognized keys',list(out['data']))
    # Verify file import/validation and explicit overwrite in the browser.
    out['data']['kale-inventory-v16']['people']=4
    page.locator('#importFile').set_input_files({'name':'kale-transfer.json','mimeType':'application/json','buffer':json.dumps(out).encode()})
    assert '1 veri alanı bulundu' in page.locator('#preview').inner_text()
    page.locator('input[value="replace"]').check()
    page.on('dialog',lambda dialog:dialog.accept())
    page.locator('#applyBtn').click()
    assert page.evaluate('JSON.parse(localStorage.getItem("kale-inventory-v16")).people')==4
    assert '1 alan yüklendi' in page.locator('#result').inner_text()
    # Invalid file is rejected, import button remains disabled.
    page.locator('#importFile').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':b'{"format":"invalid","data":{}}'})
    assert 'REDDEDİLDİ' in page.locator('#preview').inner_text()
    assert page.locator('#applyBtn').is_disabled()
    assert not errors,errors
    page.screenshot(path='/mnt/data/KALE-v1.8-Yedek-Aktarim-Onizleme.png',full_page=True)
    browser.close()
