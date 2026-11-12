"""Deterministic V2 quantity ledger: one chosen source per factor.

This module does not calculate GYF, evaluate municipal eligibility, or certify a CAD quantity.
It deliberately refuses to add manual and DXF quantities together implicitly.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

SOURCES = ("Unresolved", "DXF", "Manual", "Override", "Exclude")


@dataclass(frozen=True)
class QuantityRow:
    factor_id: str
    label: str
    section: str
    measure: str
    dxf: float
    manual: float
    source: str
    override: float
    final: float | None
    status: str
    has_dxf: bool
    has_manual: bool


def quantity_context(municipality: str, version: str, drawing_sha: str | None,
                     rulebook_sha: str | None, mapping: dict[str, str] | None,
                     units_to_m: float | None) -> str:
    """Any modification of drawing, mapped layers, unit scale or rulebook changes the ledger identity."""
    payload = {"municipality": municipality, "version": version,
               "drawing_sha": drawing_sha or "", "rulebook_sha": rulebook_sha or "",
               "mapping": sorted((mapping or {}).items()), "units_to_m": units_to_m}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]


def _quantity(number: Any, *, count: bool = False) -> float:
    try:
        value = float(number)
    except (TypeError, ValueError) as exc:
        raise ValueError("Quantity must be a nonnegative number") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError("Quantity must be finite and nonnegative")
    if count and not value.is_integer():
        raise ValueError("Count-based factors require whole numbers")
    return value


def decide_source(dxf: float, manual: float, *, selection: str | None = None) -> str:
    if selection is not None:
        if selection not in SOURCES:
            raise ValueError(f"Unknown quantity source: {selection}")
        return selection
    if dxf > 0 and manual > 0:
        return "Unresolved"
    if dxf > 0:
        return "DXF"
    if manual > 0:
        return "Manual"
    return "Exclude"


def reconcile(factors: list[dict], manual: dict[str, Any], dxf: dict[str, Any],
              *, choices: dict[str, str] | None = None,
              overrides: dict[str, Any] | None = None) -> list[QuantityRow]:
    """Build a factor ledger; selected source *replaces*, never adds to, the other source."""
    choices = choices or {}
    overrides = overrides or {}
    rows = []
    for factor in factors:
        fid = str(factor["id"])
        is_count = factor.get("measure") == "count"
        m = _quantity(manual.get(fid, 0), count=is_count)
        d = _quantity(dxf.get(fid, 0), count=is_count)
        override = _quantity(overrides.get(fid, 0), count=is_count)
        source = decide_source(d, m, selection=choices.get(fid))
        if source == "Unresolved":
            final, status = None, "CONFLICT_REVIEW_REQUIRED"
        elif source == "DXF":
            final, status = (d, "PROVISIONAL_DXF") if d > 0 else (None, "DXF_QUANTITY_MISSING")
        elif source == "Manual":
            final, status = m, "MANUAL_UNVERIFIED"
        elif source == "Override":
            final, status = override, "USER_OVERRIDE_UNVERIFIED"
        else:
            final, status = 0.0, "EXCLUDED"
        labels = factor.get("label", {})
        label = (labels.get("en") or labels.get("sv") or fid) if isinstance(labels, dict) else str(labels)
        rows.append(QuantityRow(fid, label, str(factor.get("section", "")),
                                str(factor.get("measure", "area")), d, m, source,
                                override, final, status, d > 0, m > 0))
    return rows


def can_confirm(rows: list[QuantityRow], *, blocking_findings: bool = False) -> tuple[bool, list[str]]:
    reasons = []
    if blocking_findings:
        reasons.append("DXF extraction contains blocking errors; resolve or explicitly exclude DXF-derived quantities.")
    if any(r.status == "CONFLICT_REVIEW_REQUIRED" for r in rows):
        reasons.append("Resolve factors with both DXF and manual quantities.")
    if any(r.status == "DXF_QUANTITY_MISSING" for r in rows):
        reasons.append("A selected DXF source has no extracted quantity.")
    if not any((r.final or 0) > 0 for r in rows):
        reasons.append("There are no positive quantities to confirm.")
    return not reasons, reasons


def confirmed_snapshot(rows: list[QuantityRow], *, context: str) -> dict:
    """Review confirmation only. This must never be interpreted as eligibility certification."""
    return {"context": context, "status": "USER_CONFIRMED_QUANTITIES_UNVERIFIED_ELIGIBILITY",
            "quantities": {r.factor_id: r.final for r in rows if r.final is not None},
            "evidence": [{"factor_id": r.factor_id, "source": r.source, "dxf": r.dxf,
                          "manual": r.manual, "override": r.override, "final": r.final,
                          "status": r.status} for r in rows]}
