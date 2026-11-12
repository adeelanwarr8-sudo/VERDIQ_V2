"""Non-destructive modelspace DXF quality audit for VERDIQ_V2.

This is a screening layer, NOT a geometry repair or municipal certification.
Measurements shown here are raw per-entity estimates before union, clipping,
municipal eligibility rules and user review.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import ezdxf
from ezdxf import path as dxfpath, recover
from shapely.geometry import Polygon


def audit_entities(path: str | Path, units_to_m: float, mapping: dict[str, str],
                   max_records: int = 10000):
    try:
        doc = ezdxf.readfile(str(path))
    except ezdxf.DXFStructureError:
        doc, _ = recover.readfile(str(path))
    records = []
    issues = []
    counts = Counter()
    seen_symbols = defaultdict(list)
    for e in doc.modelspace():
        kind = e.dxftype()
        layer = str(e.dxf.get('layer', '0'))
        handle = str(e.dxf.get('handle', ''))
        mapped = mapping.get(layer, '')
        counts[kind] += 1
        row = {'handle': handle, 'layer': layer, 'entity_type': kind,
               'factor_id': mapped, 'raw_area_m2': None,
               'measurement_status': 'Not measured'}
        try:
            if kind in ('LWPOLYLINE', 'POLYLINE'):
                closed = bool(e.closed if kind == 'LWPOLYLINE' else e.is_closed)
                if not closed:
                    issues.append(('warning', 'OPEN_CONTOUR', f'{layer} / {handle}: open {kind}; not counted as an area.'))
                    row['measurement_status'] = 'Open contour'
                elif kind == 'POLYLINE' and (e.is_poly_face_mesh or e.is_polygon_mesh):
                    row['measurement_status'] = 'Mesh unsupported'
                else:
                    flat = [(p.x * units_to_m, p.y * units_to_m)
                            for p in dxfpath.make_path(e).flattening(max(0.01 / units_to_m, 1e-8))]
                    if len(flat) >= 3:
                        poly = Polygon(flat)
                        if not poly.is_valid:
                            issues.append(('warning', 'INVALID_POLYGON',
                                           f'{layer} / {handle}: invalid boundary; legacy extractor may repair it, review area.'))
                            row['measurement_status'] = 'Invalid polygon'
                        else:
                            row['measurement_status'] = 'Raw valid polygon'
                        row['raw_area_m2'] = round(poly.area, 4)
            elif kind in ('INSERT', 'POINT', 'CIRCLE'):
                xyz = e.dxf.insert if kind == 'INSERT' else (e.dxf.location if kind == 'POINT' else e.dxf.center)
                xy = (round(float(xyz[0]) * units_to_m, 4), round(float(xyz[1]) * units_to_m, 4))
                row['measurement_status'] = 'Symbol candidate; classification unverified'
                if mapped:
                    key = (mapped, xy)
                    if seen_symbols[key]:
                        issues.append(('warning', 'POSSIBLE_DUPLICATE_SYMBOL',
                                       f'{layer} / {handle}: same mapped factor and location as entity {seen_symbols[key][0]}.'))
                    seen_symbols[key].append(handle)
            elif kind in ('TEXT', 'MTEXT', 'DIMENSION'):
                row['measurement_status'] = 'Annotation; not counted'
            else:
                row['measurement_status'] = 'Unsupported for quantity extraction'
        except (ValueError, TypeError, ezdxf.DXFError) as exc:
            issues.append(('warning', 'ENTITY_MEASUREMENT_FAILED',
                           f'{layer} / {handle}: failed audit of {kind} ({type(exc).__name__}).'))
            row['measurement_status'] = 'Audit failed'
        if len(records) < max_records:
            records.append(row)
    if sum(counts.values()) > max_records:
        issues.append(('info', 'EVIDENCE_TRUNCATED', f'Object evidence displays the first {max_records} modelspace entities.'))
    return records, issues, dict(counts)
