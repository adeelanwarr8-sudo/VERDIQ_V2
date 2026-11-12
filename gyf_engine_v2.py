"""VERDIQ_V2: versioned rulebook selection and reviewed DXF quantity workflow.

A rulebook's declared status is metadata, not independent external verification.
No GYF score is issued from unreviewed extraction by this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from collections import Counter
import hashlib
import math
import os

import ezdxf

from verdiq_loader import parse_rulebook, sha256
from verdiq_dxf import auto_mapping, read_layers, plot_geometry, quantities, INSUNITS_TO_M

ROOT = Path(__file__).resolve().parent
RULEBOOK_FILES = {
    ("Stockholm", "2021-02-01"): "rulebook_stockholm_gyf_2021-02-01.yaml",
    ("Stockholm", "2015-06-17"): "rulebook_stockholm_gyf_2015-06-17.yaml",
    ("Nacka", "2019-10"): "rulebook_nacka_gyf_2019-10.yaml",
    ("SGBC Miljöbyggnad", "2026"): "rulebook_sgbc_miljobyggnad_gyf_2026.yaml",
}

@dataclass
class Finding:
    severity: str
    code: str
    text: str

@dataclass
class Extraction:
    rulebook_id: str
    version: str
    rulebook_sha: str
    drawing_sha: str
    units_to_m: float | None
    unit_code: int
    layer_names: list[str]
    proposed_mapping: dict[str,str]
    quantities: dict[str,float]
    evidence: list[dict]
    findings: list[Finding] = field(default_factory=list)
    plot_area_m2: float | None = None


def load_selected(municipality: str, version: str):
    """Only loads explicitly bundled, schema-validated YAML; no PDF-to-rules execution."""
    name = RULEBOOK_FILES.get((municipality, version))
    if name is None:
        raise ValueError(f"No executable municipal rulebook bundled for {municipality} {version}. "
                         "A display-only catalogue is not a validated rulebook.")
    # Support both the current GitHub repository layout (YAML files in root)
    # and a future organized rulebooks/ directory.
    candidates = (ROOT / "rulebooks" / name, ROOT / name)
    source = next((candidate for candidate in candidates if candidate.is_file()), None)
    if source is None:
        raise ValueError(
            f"Municipal rulebook file '{name}' is missing. "
            "Add it to the repository root or the rulebooks/ folder."
        )
    raw = source.read_text(encoding="utf-8")
    rb = parse_rulebook(raw)
    if rb.meta.version != version:
        raise ValueError("Rulebook version mismatch")
    return rb, sha256(raw)


def _read_insunits(path):
    try:
        doc = ezdxf.readfile(str(path))
    except ezdxf.DXFStructureError:
        from ezdxf import recover
        doc, _ = recover.readfile(str(path))
    code = int(doc.header.get("$INSUNITS", 0) or 0)
    return code, INSUNITS_TO_M.get(code)


def inspect_dxf(blob: bytes, municipality: str, version: str, *,
                units_to_m: float | None = None, mapping: dict[str,str] | None = None,
                plot_layer: str | None = None) -> Extraction:
    """Inspect real CAD content and extract *provisional* quantities.

    Ambiguous DXF units are a hard stop until user supplies an explicit scale.
    Mapping is per layer and requires review; factor eligibility is NOT inferred.
    """
    if not blob or len(blob) > 50 * 1024 * 1024:
        raise ValueError("DXF is empty or larger than 50 MB")
    rb, rule_sha = load_selected(municipality,version)
    findings=[]
    if rb.meta.status != 'verified':
        findings.append(Finding('warning','DRAFT_RULEBOOK',f"Rulebook declares status '{rb.meta.status}'; official conformity is not independently verified."))
    if rb.balancing.status != 'verified':
        findings.append(Finding('warning','UNVERIFIED_BALANCING','Ecosystem-service balancing is not verified for this rulebook.'))
    with NamedTemporaryFile(suffix='.dxf', delete=False) as h:
        path=Path(h.name);h.write(blob)
    try:
        code, detected=_read_insunits(path)
        if units_to_m is not None:
            if not (math.isfinite(units_to_m) and units_to_m > 0):
                raise ValueError('Manual unit conversion must be a positive finite number')
            factor=units_to_m
            if detected is not None and abs(detected-factor)>1e-10:
                findings.append(Finding('warning','UNIT_OVERRIDE','The selected drawing-unit conversion overrides DXF metadata.'))
        else:
            factor=detected
        if factor is None:
            findings.append(Finding('error','UNCONFIRMED_UNITS',f"DXF $INSUNITS={code}; choose the correct units before area/count extraction."))
            # Read only layer names without performing potentially wrong measurements.
            doc=ezdxf.readfile(str(path))
            layers=sorted({e.dxf.get('layer','0') for e in doc.modelspace()})
            suggested=auto_mapping(rb,layers)
            return Extraction(rb.meta.id,version,rule_sha,hashlib.sha256(blob).hexdigest()[:16],None,code,
                              layers,suggested,{},[],findings)
        stats=read_layers(path,units_to_m=factor)
        layers=sorted(stats)
        suggested=auto_mapping(rb,layers)
        chosen=suggested if mapping is None else {k:v for k,v in mapping.items() if v}
        known={f.id for f in rb.factors}
        bad={k:v for k,v in chosen.items() if v not in known or k not in stats}
        if bad:raise ValueError(f"Invalid CAD-to-GYF mapping: {bad}")
        unknown=[k for k in layers if k not in chosen]
        if unknown:
            findings.append(Finding('warning','UNMAPPED_LAYERS',f"{len(unknown)} CAD layers remain unmapped; confirm whether they contain relevant GYF geometry."))
        plot=plot_geometry(rb,stats,plot_layer=plot_layer)
        if plot is None:
            findings.append(Finding('warning','NO_PLOT_BOUNDARY','No plot boundary found; quantities may include objects outside the site.'))
        for layer,s in stats.items():
            if len(s.points)!=len(set(s.points)):
                findings.append(Finding('warning','DUPLICATE_SYMBOL',f"Layer '{layer}' contains repeated symbol coordinates; check duplicate tree counts."))
        q=quantities(rb,stats,chosen,plot=plot) if chosen else {}
        evidence=[]
        for layer,fid in chosen.items():
            factor_obj=rb.factor(fid)
            stat=stats[layer]
            evidence.append({'layer':layer,'factor_id':fid,'factor_name':factor_obj.label.text('en'),
                             'measure':factor_obj.measure,'polygons':stat.polygons,'symbols':stat.symbols,
                             'raw_area_m2':round(stat.area_m2+stat.circle_area_m2,4),
                             'status':'PROVISIONAL_REVIEW_REQUIRED'})
        if any(rb.factor(fid).measure=='length' for fid in chosen.values()):
            findings.append(Finding('error','LENGTH_UNSUPPORTED','Legacy extractor does not measure line lengths. Length-based quantities must not be used.'))
            for fid in list(q):
                if rb.factor(fid).measure=='length':q.pop(fid)
        return Extraction(rb.meta.id,version,rule_sha,hashlib.sha256(blob).hexdigest()[:16],factor,code,
                          layers,suggested,q,evidence,findings, round(plot.area,3) if plot is not None else None)
    finally:
        path.unlink(missing_ok=True)


def assess_readiness(extraction: Extraction) -> str:
    """No automatic scoring from DXF. User must reconcile and confirm quantities."""
    if any(f.severity=='error' for f in extraction.findings): return 'BLOCKED'
    return 'REVIEW_REQUIRED'
