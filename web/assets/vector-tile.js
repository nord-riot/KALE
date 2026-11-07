'use strict';
/* Minimal dependency-free Mapbox Vector Tile reader for the Shortbread OSM schema.
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
 function paint(ctx,layers,x,y,tileSize,z){ctx.save();ctx.beginPath();ctx.rect(x,y,tileSize,tileSize);ctx.clip();
  const priority=['landcover','landuse','water','waterway','building','boundary','transportation','transportation_name','place'];
  const layerMap=new Map(layers.map(l=>[l.name,l]));
  let labels=0;
  for(const name of priority){const l=layerMap.get(name);if(!l)continue;
   const extent=l.extent||4096,scale=tileSize/extent;
   for(const f of l.features){if(f.type!==1&&f.type!==2&&f.type!==3)continue;const pr=f.properties||{},cls=String(pr.class||pr.subclass||'');let style=null;
    if(name==='water'||name==='waterway')style={fill:'#225a72',stroke:'#3987a0',width:1};
    else if(name==='landcover')style={fill:cls==='wood'?'#294e37':'#3e5041'};
    else if(name==='landuse')style={fill:/forest|wood|grass|park/.test(cls)?'#3b624a':'#374849'};
    else if(name==='building'&&z>=11)style={fill:'#66706a',stroke:'#73827b',width:.4};
    else if(name==='boundary'&&z>=7)style={stroke:'#66786a',width:.7,dash:[4,4]};
    else if(name==='transportation'||name==='transportation_name'){
      if(name==='transportation_name')continue;
      if(['motorway','trunk'].includes(cls))style={stroke:'#ebc17d',width:z>=12?4:2.5};
      else if(['primary','secondary'].includes(cls))style={stroke:'#eacfa0',width:z>=12?3:1.7};
      else if(cls==='tertiary')style={stroke:'#d7c6ab',width:z>=12?2:1.2};
      else if(['path','track','footway','cycleway','steps'].includes(cls))style={stroke:'#b8baa0',width:.85,dash:[2,3]};
      else style={stroke:'#a2a9a0',width:z>=12?1.4:.6};
    }else if(name==='place'){if(z<6||labels>=8||!pr.name)continue;labels++;style={label:String(pr.name).slice(0,42)};}
    else continue;
    const path=paths(f);if(style.label){const first=path.find(a=>a.length);if(!first)continue;ctx.font='12px sans-serif';ctx.strokeStyle='#182833';ctx.lineWidth=3;ctx.fillStyle='#f0ebe1';const px=x+first[0][0]*scale,py=y+first[0][1]*scale;ctx.strokeText(style.label,px,py);ctx.fillText(style.label,px,py);continue;}
    ctx.beginPath();for(const pts of path){let start=true;for(const pt of pts){const px=x+pt[0]*scale,py=y+pt[1]*scale;if(start){ctx.moveTo(px,py);start=false;}else ctx.lineTo(px,py);}if(f.type===3)ctx.closePath();}
    if(style.fill){ctx.fillStyle=style.fill;ctx.fill(f.type===3?'evenodd':'nonzero');}
    if(style.stroke){ctx.strokeStyle=style.stroke;ctx.lineWidth=style.width||1;ctx.setLineDash(style.dash||[]);ctx.stroke();ctx.setLineDash([]);}
   }
  }
  ctx.restore();
 }
 return {decode,paint,paths};
})();
