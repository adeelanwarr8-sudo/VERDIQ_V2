"""Increment 1: read supported DXF entities and display an interactive local-CAD SVG viewer.

This module intentionally does not calculate GYF quantities or validate design geometry.
"""
from __future__ import annotations

from collections import Counter
from html import escape
import io
import json
import math
from pathlib import Path
import tempfile

import ezdxf
import streamlit as st
import streamlit.components.v1 as components

MAX_ENTITIES = 25000
MAX_DXF_BYTES = 50 * 1024 * 1024
PALETTE = ["#0f7a43", "#336cba", "#a76c20", "#8555a5", "#227d84", "#ad425e", "#555e68", "#7e7530"]


def _xy(p):
    return [float(p[0]), float(p[1])]


def _curve(cx, cy, rx, ry, start=0, end=2 * math.pi, rotation=0):
    span = end - start
    if span <= 0:
        span += 2 * math.pi
    n = max(18, min(180, int(math.ceil(abs(span) / (math.pi / 40)))))
    cr, sr = math.cos(rotation), math.sin(rotation)
    result = []
    for i in range(n + 1):
        a = start + span * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        result.append([cx + x * cr - y * sr, cy + x * sr + y * cr])
    return result


def _entity_shapes(entity):
    typ = entity.dxftype()
    try:
        if typ == "LINE":
            return [("line", [_xy(entity.dxf.start), _xy(entity.dxf.end)], False)]
        if typ == "LWPOLYLINE":
            # ezdxf virtual_entities resolves arc bulges into LINE/ARC primitives.
            if any(abs(point[4]) > 1e-10 for point in entity.get_points("xyseb")):
                shapes = []
                for item in entity.virtual_entities():
                    shapes.extend(_entity_shapes(item))
                return shapes
            return [("line", [[float(p[0]), float(p[1])] for p in entity.get_points("xy")], entity.closed)]
        if typ == "POLYLINE":
            if entity.is_polygon_mesh or entity.is_poly_face_mesh:
                return []
            return [("line", [_xy(v.dxf.location) for v in entity.vertices], bool(entity.is_closed))]
        if typ == "CIRCLE":
            return [("line", _curve(entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius, entity.dxf.radius), True)]
        if typ == "ARC":
            return [("line", _curve(entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius, entity.dxf.radius,
                                     math.radians(entity.dxf.start_angle), math.radians(entity.dxf.end_angle)), False)]
        if typ == "ELLIPSE":
            center = entity.dxf.center
            major = entity.dxf.major_axis
            radius = math.hypot(major.x, major.y)
            rotation = math.atan2(major.y, major.x)
            return [("line", _curve(center.x, center.y, radius, radius * entity.dxf.ratio,
                                     entity.dxf.start_param, entity.dxf.end_param, rotation),
                     abs(entity.dxf.end_param - entity.dxf.start_param) >= 2 * math.pi - 0.01)]
        if typ == "SPLINE":
            return [("line", [_xy(p) for p in entity.flattening(0.1, segments=8)], False)]
        if typ == "POINT":
            return [("point", [_xy(entity.dxf.location)], False)]
        if typ == "SOLID" or typ == "TRACE":
            pts = [_xy(getattr(entity.dxf, v)) for v in ("vtx0", "vtx1", "vtx3", "vtx2")]
            return [("line", pts, True)]
        if typ == "INSERT":
            shapes = []
            for part in entity.virtual_entities():
                shapes.extend(_entity_shapes(part))
                if len(shapes) > 3000:
                    break
            return shapes
        if typ == "HATCH":
            shapes = []
            for path in entity.paths:
                if hasattr(path, "vertices"):
                    points = [[float(p[0]), float(p[1])] for p in path.vertices]
                    if len(points) >= 2:
                        shapes.append(("line", points, True))
                elif hasattr(path, "edges"):
                    for edge in path.edges:
                        kind = edge.type
                        if kind == "LineEdge":
                            shapes.append(("line", [_xy(edge.start), _xy(edge.end)], False))
                        elif kind == "ArcEdge":
                            pts = _curve(edge.center[0], edge.center[1], edge.radius, edge.radius,
                                         math.radians(edge.start_angle), math.radians(edge.end_angle))
                            shapes.append(("line", pts, False))
            return shapes
    except (ValueError, TypeError, AttributeError, ZeroDivisionError, OverflowError, ezdxf.DXFError):
        return []
    return []


@st.cache_data(show_spinner=False, max_entries=4)
def parse_dxf(blob: bytes) -> dict:
    if len(blob) > MAX_DXF_BYTES:
        raise ValueError("The DXF exceeds the 50 MB upload limit.")
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as handle:
        handle.write(blob)
        filepath = Path(handle.name)
    try:
        doc = ezdxf.readfile(str(filepath))
    except (OSError, ezdxf.DXFError, UnicodeError) as exc:
        raise ValueError(f"Unable to read this DXF: {exc}") from exc
    finally:
        filepath.unlink(missing_ok=True)
    layers = {}
    counter = Counter()
    skipped = Counter()
    bounds = [math.inf, math.inf, -math.inf, -math.inf]
    added = 0
    truncated = False
    for entity in doc.modelspace():
        typ = entity.dxftype()
        name = entity.dxf.get("layer", "0")
        if name not in layers:
            layers[name] = {"shapes": [], "entities": 0}
        layers[name]["entities"] += 1
        counter[typ] += 1
        shapes = _entity_shapes(entity)
        if not shapes:
            skipped[typ] += 1
        for kind, pts, closed in shapes:
            if added >= MAX_ENTITIES:
                truncated = True
                break
            pts = [[round(x, 5), round(y, 5)] for x, y in pts if math.isfinite(x) and math.isfinite(y)]
            if not pts:
                continue
            for x, y in pts:
                bounds[0] = min(bounds[0], x)
                bounds[1] = min(bounds[1], y)
                bounds[2] = max(bounds[2], x)
                bounds[3] = max(bounds[3], y)
            layers[name]["shapes"].append({"points": pts, "closed": closed, "kind": kind})
            added += 1
        if truncated:
            break
    return {"layers": layers, "bounds": bounds if added else None,
            "entity_count": sum(counter.values()), "shape_count": added, "types": dict(counter),
            "skipped": dict(skipped), "truncated": truncated, "units_code": int(doc.header.get("$INSUNITS", 0))}


def render_dxf_viewer(data: dict, height: int = 530) -> None:
    # JSON is transmitted as inert application/json, not executable JavaScript.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    template = r'''<!doctype html><html><head><meta charset="UTF-8"/>
<style>
*{box-sizing:border-box}body{margin:0;background:#fff;color:#18241d;font-family:Inter,Arial,sans-serif;font-size:13px}
.shell{height:100vh;display:flex;flex-direction:column;border:1px solid #dde5df;border-radius:9px;overflow:hidden}
.toolbar{display:flex;align-items:center;gap:8px;padding:8px 10px;border-bottom:1px solid #e2e8e3;flex-wrap:wrap}
button{border:1px solid #d8e1da;background:#fff;color:#23372a;border-radius:6px;min-height:34px;padding:0 11px;cursor:pointer;font-weight:600;font-size:13px}
button:hover,button:focus-visible{background:#eaf6e9;border-color:#75b891}button:disabled{opacity:.4;cursor:not-allowed}
button.active{background:#e7f5e7;border-color:#81c491;color:#0d6036}
.sep{border-left:1px solid #d9e3da;height:25px;margin:0 3px}.right{margin-left:auto}
.canvas-wrap{position:relative;flex:1;min-height:180px;overflow:hidden;background:#fff}
svg{width:100%;height:100%;touch-action:none;cursor:grab;display:block}svg.dragging{cursor:grabbing}
.layer-panel{position:absolute;right:10px;top:10px;width:min(270px,60%);max-height:85%;overflow:auto;background:#fff;border:1px solid #dce5de;border-radius:8px;box-shadow:0 8px 25px #0b382021;padding:12px}
.layer-panel.hidden{display:none}.panel-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.layer-row{display:flex;align-items:center;gap:9px;padding:5px 0;overflow-wrap:anywhere}.layer-row input{accent-color:#0e7b44;width:17px;height:17px;flex:none}
.swatch{width:16px;height:4px;border-radius:2px;flex:none}.layer-name{flex:1;min-width:0}.count{color:#718076;font-size:11px}
.footer{padding:9px 12px;background:#f9fbf9;border-top:1px solid #e0e7e1;display:flex;gap:15px;flex-wrap:wrap;color:#4b5d50;font-size:12px}
.empty{display:flex;align-items:center;justify-content:center;height:100%;font-size:14px;color:#65736a}
</style></head><body><div class="shell">
<div class="toolbar"><button id="pan" class="active" title="Drag to pan">✋ Pan</button>
<button id="zin" title="Zoom in">＋</button><button id="zout" title="Zoom out">－</button>
<button id="fit" title="Fit entire drawing">⛶ Fit</button><span class="sep"></span>
<button id="expand" title="Expand viewer">⤢ Expand</button>
<button id="layersButton" class="right" title="Toggle CAD layers">▱ Layers ▾</button></div>
<div class="canvas-wrap" id="area"><svg id="drawing" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-label="DXF drawing workspace"><g id="features" transform="scale(1,-1)"></g></svg>
<div id="layerPanel" class="layer-panel"><div class="panel-head"><strong>CAD Layers</strong><button id="closeLayers" aria-label="Close layers">×</button></div><div id="layerRows"></div></div></div>
<div class="footer"><span id="summary">DXF viewer</span><span>Local drawing coordinates · wheel to zoom · drag to pan</span></div>
</div><script type="application/json" id="dataset">__DATA__</script><script>
(()=>{'use strict';
const data=JSON.parse(document.getElementById('dataset').textContent),svg=document.getElementById('drawing');
const features=document.getElementById('features'), rows=document.getElementById('layerRows'),NS='http://www.w3.org/2000/svg';
let box={x:0,y:0,w:100,h:100},pointer=null;
const palette=['#0f7a43','#336cba','#a76c20','#8555a5','#227d84','#ad425e','#555e68','#7e7530'];
function apply(){svg.setAttribute('viewBox',[box.x,box.y,box.w,box.h].join(' '));}
function fit(){if(!data.bounds)return;const [x0,y0,x1,y1]=data.bounds;
 const w=Math.max(x1-x0,1),h=Math.max(y1-y0,1),r=Math.max(1,svg.clientWidth)/Math.max(1,svg.clientHeight),pad=1.1;
 const newW=Math.max(w,h*r)*pad,newH=newW/r;
 box={x:(x0+x1-newW)/2,y:(-y0-y1-newH)/2,w:newW,h:newH};apply();}
function zoom(k,centerX=.5,centerY=.5){const nw=box.w*k,nh=box.h*k;
 box={x:box.x+(box.w-nw)*centerX,y:box.y+(box.h-nh)*centerY,w:nw,h:nh};apply();}
function el(name,attrs){const e=document.createElementNS(NS,name);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);return e;}
Object.entries(data.layers||{}).forEach(([name,layer],idx)=>{
 const color=palette[idx%palette.length],id='layer'+idx;
 const group=el('g',{'data-layer':name});
 for(const s of layer.shapes){if(s.kind==='point'){
  group.appendChild(el('circle',{cx:s.points[0][0],cy:s.points[0][1],r:Math.max(0.15,((data.bounds||[0,0,100,100])[2]-(data.bounds||[0,0,100,100])[0])*.001),fill:color}));continue;}
  if(s.points.length<2)continue;
  const d=s.points.map((p,i)=>(i?'L':'M')+p[0]+' '+p[1]).join(' ')+(s.closed?' Z':'');
  group.appendChild(el('path',{d,fill:'none',stroke:color,'stroke-width':'1.5','vector-effect':'non-scaling-stroke','stroke-linecap':'round','stroke-linejoin':'round'}));
 }
 features.appendChild(group);
 const row=document.createElement('label');row.className='layer-row';
 const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;cb.addEventListener('change',()=>{group.style.display=cb.checked?'':'none';});
 const sw=document.createElement('span');sw.className='swatch';sw.style.background=color;
 const title=document.createElement('span');title.className='layer-name';title.textContent=name;
 const count=document.createElement('span');count.className='count';count.textContent=String(layer.entities);
 row.append(cb,sw,title,count);rows.append(row);
});
const summary=document.getElementById('summary');summary.textContent=Object.keys(data.layers||{}).length+' layers · '+data.entity_count+' entities';
if(data.truncated)summary.textContent+=' · preview limit reached';
if(!data.bounds){const empty=document.createElement('div');empty.className='empty';empty.textContent='No supported modelspace geometry found in this DXF.';document.getElementById('area').appendChild(empty);svg.style.display='none';}
else fit();
document.getElementById('zin').onclick=()=>zoom(.8);document.getElementById('zout').onclick=()=>zoom(1.25);document.getElementById('fit').onclick=fit;
const panel=document.getElementById('layerPanel');document.getElementById('layersButton').onclick=()=>panel.classList.toggle('hidden');document.getElementById('closeLayers').onclick=()=>panel.classList.add('hidden');
const shell=document.querySelector('.shell');document.getElementById('expand').onclick=()=>{
 if(document.fullscreenElement){document.exitFullscreen?.();return;}if(shell.requestFullscreen){shell.requestFullscreen().catch(()=>{});}};
svg.addEventListener('wheel',ev=>{ev.preventDefault();const rect=svg.getBoundingClientRect(),u=(ev.clientX-rect.left)/rect.width,v=(ev.clientY-rect.top)/rect.height;zoom(ev.deltaY<0?.83:1.2,u,v);},{passive:false});
svg.addEventListener('pointerdown',ev=>{if(ev.button!==0)return;pointer={x:ev.clientX,y:ev.clientY,b:{...box}};svg.setPointerCapture(ev.pointerId);svg.classList.add('dragging');});
svg.addEventListener('pointermove',ev=>{if(!pointer)return;const r=svg.getBoundingClientRect();box={...pointer.b,x:pointer.b.x-(ev.clientX-pointer.x)*pointer.b.w/r.width,y:pointer.b.y-(ev.clientY-pointer.y)*pointer.b.h/r.height};apply();});
function end(){pointer=null;svg.classList.remove('dragging');}svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
window.addEventListener('resize',()=>{if(data.bounds)fit();});
})();
</script></body></html>'''
    components.html(template.replace('__DATA__', payload), height=height, scrolling=False)
