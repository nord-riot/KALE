'use strict';
/* Dependency-free MVT renderer for Shortbread 1.x and legacy OpenMapTiles.
   Locally-served PBF only, no CDN. It is intentionally a simple 2D renderer,
   not a replacement for MapLibre's full labels, 3D or advanced styling. */
window.KALEVector=(()=>{
 const decoder=new TextDecoder();
 class Reader{
  constructor(data){this.u=data instanceof Uint8Array?data:new Uint8Array(data);this.i=0;this.end=this.u.length;}
  varint(){let val=0,mul=1;for(let n=0;n<10;n++){if(this.i>=this.end)throw Error('Kısa MVT varint');const v=this.u[this.i++];val+=(v&127)*mul;if(!(v&128)){if(!Number.isSafeInteger(val))throw Error('Büyük MVT değeri');return val;}mul*=128;}throw Error('MVT varint fazla uzun');}
  bytes(){const n=this.varint();if(n<0||n>this.end-this.i)throw Error('MVT alan uzunluğu');const sub=this.u.subarray(this.i,this.i+n);this.i+=n;return sub;}
  skip(w){if(w===0)this.varint();else if(w===1)this.i+=8;else if(w===2)this.bytes();else if(w===5)this.i+=4;else throw Error('Desteklenmeyen MVT wire type');if(this.i>this.end)throw Error('MVT taşma');}
  packed(){const d=new Reader(this.bytes()),a=[];while(d.i<d.end){a.push(d.varint());if(a.length>250000)throw Error('Aşırı MVT liste');}return a;}
  string(){return decoder.decode(this.bytes());}
 }
 const zig=n=>n%2?-((n+1)/2):n/2;
 function value(data){const r=new Reader(data);let out=null;while(r.i<r.end){const tag=r.varint(),field=tag>>3,wire=tag&7;
   if(field===1)out=r.string();else if(field===4||field===5)out=r.varint();else if(field===6)out=zig(r.varint());else if(field===7)out=Boolean(r.varint());else r.skip(wire);}return out;}
 function feature(data){const r=new Reader(data),f={type:0,tags:[],geometry:[]};while(r.i<r.end){let v=r.varint(),field=v>>3,wire=v&7;
   if(field===2)f.tags=r.packed();else if(field===3)f.type=r.varint();else if(field===4)f.geometry=r.packed();else r.skip(wire);}return f;}
 function layer(data){const r=new Reader(data),l={name:'',extent:4096,keys:[],values:[],features:[]};while(r.i<r.end){let v=r.varint(),field=v>>3,wire=v&7;
   if(field===1)l.name=r.string();else if(field===2){if(l.features.length<18000)l.features.push(feature(r.bytes()));else r.bytes();}
   else if(field===3)l.keys.push(r.string());else if(field===4)l.values.push(value(r.bytes()));else if(field===5)l.extent=r.varint();else r.skip(wire);}
  for(const f of l.features){const p={};for(let i=0;i<f.tags.length-1;i+=2){const k=l.keys[f.tags[i]];if(k!==undefined)p[k]=l.values[f.tags[i+1]];}f.properties=p;}
  return l;
 }
 function decode(buffer){const r=new Reader(buffer),layers=[];while(r.i<r.end){let tag=r.varint();if((tag>>3)===3)layers.push(layer(r.bytes()));else r.skip(tag&7);}return layers;}
 function paths(data){const p=[],a=data.geometry||[];let x=0,y=0,i=0,pts=null;
   while(i<a.length){const command=a[i++],op=command&7,n=command>>3;if(n>30000||!n)throw Error('Geçersiz geometri');
    if(op===1||op===2){for(let k=0;k<n;k++){if(i+1>=a.length)throw Error('Kesik geometri');x+=zig(a[i++]);y+=zig(a[i++]);if(op===1){pts=[];p.push(pts);}if(pts)pts.push([x,y]);}}
    else if(op===7){if(pts&&pts.length)pts.push(pts[0]);}else throw Error('MVT geometri komutu');if(i>160000)throw Error('Aşırı büyük geometri');}
   return p;
 }
 // Shortbread 1.x is used by the BBBike Türkiye pack. Earlier versions were
 // mistakenly rendering OpenMapTiles layer names and therefore hid ALL streets.
 const shortbread=['land','ocean','water_polygons','water_lines','sites','street_polygons',
  'buildings','boundaries','streets','bridges','street_labels','place_labels','pois'];
 const openmaptiles=['landcover','landuse','water','waterway','building','boundary',
  'transportation','transportation_name','place'];
 function roadStyle(cls,z,link=false){
  if(/motorway|trunk/.test(cls))return {stroke:'#f5b66c',width:z>=13?5:3};
  if(/primary|secondary/.test(cls))return {stroke:'#f0d295',width:z>=13?4:2.2};
  if(/tertiary/.test(cls))return {stroke:'#d4d0b9',width:z>=13?3.1:1.9};
  if(/rail|tram|subway|funicular/.test(cls))return {stroke:'#71878c',width:1.2,dash:[4,3]};
  if(/track|footway|path|steps|cycleway|pedestrian/.test(cls))
    return {stroke:'#adb99f',width:z>=14?1.7:1,dash:[2.5,2.5]};
  return {stroke:'#d4d8c7',width:z>=14?2.5:z>=12?1.6:.95};
 }
 function featureStyle(name,pr,z){
  const cls=String(pr.kind||pr.class||pr.subclass||'');
  if(name==='ocean'||name==='water_polygons'||name==='water')return {fill:'#245a70',stroke:'#39778e',width:.7};
  if(name==='water_lines'||name==='waterway')return {stroke:'#387f98',width:1.3};
  if(name==='land'||name==='landcover'||name==='landuse')
    return {fill:/forest|wood|park|grass|meadow/.test(cls)?'#42644a':'#344c42'};
  if(name==='sites')return {fill:/forest|park|grass/.test(cls)?'#44684d':'#40534d'};
  if((name==='buildings'||name==='building')&&z>=12)return {fill:'#7d8078',stroke:'#8b9087',width:.3};
  if((name==='boundaries'||name==='boundary')&&z>=7)return {stroke:'#5c797b',width:.8,dash:[5,4]};
  if(name==='street_polygons')return {fill:'#b6b9a9'};
  if(name==='streets'||name==='transportation'||name==='bridges')return roadStyle(cls,z,!!pr.link);
  if(name==='street_labels'&&z>=13&&pr.name)return {label:String(pr.name).slice(0,38),textSize:10};
  if((name==='place_labels'||name==='place')&&pr.name)return {label:String(pr.name).slice(0,38),textSize:z>=10?12:11};
  return null;
 }
 function paint(ctx,layers,x,y,tileSize,z){
  ctx.save();ctx.beginPath();ctx.rect(x,y,tileSize,tileSize);ctx.clip();
  const layerMap=new Map(layers.map(l=>[l.name,l]));
  const order=layerMap.has('streets')?shortbread:openmaptiles;
  let labels=0;
  for(const name of order){const l=layerMap.get(name);if(!l)continue;
   const extent=l.extent||4096,scale=tileSize/extent;
   for(const f of l.features){if(f.type!==1&&f.type!==2&&f.type!==3)continue;
    const style=featureStyle(name,f.properties||{},z);if(!style)continue;
    const path=paths(f);
    if(style.label){
      if(labels>32)continue;
      const line=path.find(a=>a.length>=2)||path.find(a=>a.length);if(!line)continue;
      const pt=line[Math.floor(line.length/2)];if(!pt)continue;
      const px=x+pt[0]*scale,py=y+pt[1]*scale;
      if(px<x+9||px>x+tileSize-9||py<y+9||py>y+tileSize-9)continue;
      if(name==='street_labels'&&z<14&&labels>13)continue;
      ctx.textAlign='center';ctx.font=`${style.textSize}px sans-serif`;
      ctx.lineWidth=2.5;ctx.strokeStyle='#19303b';ctx.fillStyle='#f2f1d9';
      ctx.strokeText(style.label,px,py);ctx.fillText(style.label,px,py);labels++;continue;
    }
    ctx.beginPath();for(const pts of path){let start=true;for(const pt of pts){const px=x+pt[0]*scale,py=y+pt[1]*scale;
      if(start){ctx.moveTo(px,py);start=false;}else ctx.lineTo(px,py);}if(f.type===3)ctx.closePath();}
    if(style.fill){ctx.fillStyle=style.fill;ctx.fill(f.type===3?'evenodd':'nonzero');}
    if(style.stroke){ctx.strokeStyle=style.stroke;ctx.lineWidth=style.width||1;
      ctx.setLineDash(style.dash||[]);ctx.stroke();ctx.setLineDash([]);}
   }
  }
  ctx.restore();
 }

 return {decode,paint,paths};
})();
