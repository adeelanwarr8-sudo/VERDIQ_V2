"""Municipality-specific quantity-entry UI prototype.

All factor definitions are an offline display snapshot supplied in factor_catalog_ui.json.
No GYF computations, compliance determinations, or model validation occur here.
"""
from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

import streamlit as st

from layout import Project
from visuals import continue_button

CATALOG = json.loads((Path(__file__).parent / "factor_catalog_ui.json").read_text(encoding="utf-8"))

STOCKHOLM_SECTIONS = [
    ("green_base", "Greenery — base factors"),
    ("green_field", "Greenery — field layer"),
    ("green_shrub", "Greenery — shrubs"),
    ("green_tree", "Greenery — trees"),
    ("green_vertical", "Greenery — vertical planting"),
    ("green_elements", "Greenery — biodiversity elements"),
    ("green_recreation", "Greenery — recreation and social values"),
    ("green_climate", "Greenery — local climate"),
    ("water_base", "Water and paving — base factors"),
    ("water_bio", "Water — biodiversity and stormwater"),
    ("water_recreation", "Water — recreation"),
    ("water_climate", "Water — local climate"),
]
STOCKHOLM_PAGES = {
    "green_base":"24–25", "green_field":"26", "green_shrub":"26", "green_tree":"27",
    "green_vertical":"28", "green_elements":"28", "green_recreation":"29–30", "green_climate":"30",
    "water_base":"31", "water_bio":"32", "water_recreation":"33", "water_climate":"34"
}
GROUP_NAMES = {"S":"Supporting", "K":"Cultural", "R":"Regulating"}


def section_title(section: str) -> str:
    return dict(STOCKHOLM_SECTIONS).get(section, section.replace("_", " ").title())


def _factor_note(factor: dict) -> str:
    detail = []
    for item in factor.get("constraints", []):
        if isinstance(item, dict):
            detail.append(str(item.get("text") or item.get("type", "Requirement")))
    if factor.get("excludes"):
        detail.append("Not combinable with: " + ", ".join(factor["excludes"]))
    if factor.get("note"):
        detail.append(str(factor["note"]))
    if factor.get("unit_area_m2"):
        detail.append(f"Reference area per item: {factor['unit_area_m2']:g} m²")
    return " · ".join(detail)


def _source_note(model: str, section: str) -> str:
    if model == "Stockholm|2021-02-01":
        return f"Source: Stockholm City GYF handbook (2021-02-01), pp. {STOCKHOLM_PAGES.get(section, '22–34')}"
    return "Factor information: municipal model draft catalogue; verify against official municipal source before use."


def _save_quantity(model_key: str, factor_id: str, widget_key: str) -> None:
    """Persist values independently of transient Streamlit widget keys."""
    st.session_state.setdefault("manual_quantities", {})[f"{model_key}|{factor_id}"] = st.session_state[widget_key]


def _factor_row(model_key: str, factor: dict, rownum: int) -> None:
    fid = factor["id"]
    labels = factor.get("label", {})
    en = labels.get("en") or labels.get("sv") or fid
    sv = labels.get("sv") or ""
    unit = "pcs" if factor.get("measure") == "count" else "m²"
    weight = factor.get("factor")
    groups = [GROUP_NAMES.get(x,x) for x in factor.get("groups", [])]
    identity = f"{model_key}|{fid}".replace(" ", "_")
    widget_key = f"quantity_{identity}"
    restored = st.session_state.get("manual_quantities", {}).get(f"{model_key}|{fid}", 0)
    with st.container(border=True, key=f"mf_{identity}"):
        description, amount = st.columns([3.2, 1], gap="medium", vertical_alignment="center")
        with description:
            st.markdown(f'<div class="v-factor-title">{escape(en)}</div>', unsafe_allow_html=True)
            if sv and sv != en:
                st.markdown(f'<div class="v-factor-sv">{escape(sv)}</div>', unsafe_allow_html=True)
            tags = [f"Weight {weight:g}" if isinstance(weight,(int,float)) else "Weight —", unit]
            if groups:
                tags.append(" / ".join(groups))
            st.markdown('<div class="v-factor-meta">' + ' · '.join(escape(t) for t in tags) + '</div>', unsafe_allow_html=True)
        with amount:
            if unit == "pcs":
                st.number_input(f"Quantity ({unit})", min_value=0, step=1, value=int(restored),
                                key=widget_key, label_visibility="visible", on_change=_save_quantity,
                                args=(model_key, fid, widget_key))
            else:
                st.number_input(f"Quantity ({unit})", min_value=0.0, step=1.0, value=float(restored), format="%.2f",
                                key=widget_key, label_visibility="visible", on_change=_save_quantity,
                                args=(model_key, fid, widget_key))
        extra = _factor_note(factor)
        if extra:
            with st.expander("Eligibility and measurement notes"):
                st.write(extra)
                st.caption(_source_note(model_key, factor.get("section", "")))


def render_manual_proforma(project: Project) -> None:
    model_key = f"{project.municipality}|{project.version}"
    definition = CATALOG.get(model_key)
    st.markdown('<div class="v-manual-intro"><div class="v-main-heading">Manual GYF Calculation</div>'
                '<div class="v-main-sub">Enter quantities by municipality-specific factor. No assessment is calculated in this UI prototype.</div></div>',
                unsafe_allow_html=True)
    if not definition:
        st.error("No demonstration factor catalogue is available for this selected model.")
        return
    factors = definition["factors"]
    model_is_stockholm = project.municipality == "Stockholm"
    st.markdown(
        f'<div class="v-manual-context"><strong>{escape(project.municipality)}</strong> · '
        f'{escape(project.version)} · {len(factors)} factor-entry fields · UI demonstration catalogue</div>',
        unsafe_allow_html=True
    )
    if model_is_stockholm:
        st.markdown("#### Which GYF requirements apply to this project?")
        mode = st.radio("Project GYF basis", ["General GYF", "SpecialGYF", "Not yet determined"],
                        horizontal=True, key=f"basis_{model_key}", label_visibility="collapsed")
        if mode == "SpecialGYF":
            st.markdown('<div class="v-manual-banner v-manual-warning"><strong>SpecialGYF: No numerical GYF calculation</strong>'
                        '<div>Stockholm City specifies project-specific greenery or stormwater measures instead of a GYF score. '
                        'Refer to the project GYF-underlag and document the stipulated measures.</div></div>', unsafe_allow_html=True)
            st.text_area("Project-specific measures or documentation notes", key=f"special_notes_{model_key}",
                         placeholder="Enter or summarize the measures specified in the project GYF-underlag.", height=110)
            st.caption("Official Stockholm City handbook (2021-02-01), p. 17 and SpecialGYF appendix, p. 42.")
            return
        if mode == "Not yet determined":
            st.markdown('<div class="v-manual-banner v-manual-warning">'
                        'The applicable GYF-underlag has not yet been confirmed. Quantity entries below are exploratory only.'
                                               '</div>', unsafe_allow_html=True)
        else:
            st.caption("General GYF: the project-specific GYF-underlag determines the target and balancing requirements. "
                       "The target is configured in Project Setup.")
    else:
        st.caption("The fields below reflect the selected municipality/version draft factor catalogue. "
                   "Municipality-specific eligibility rules will be connected and verified in a later phase.")

    left, right = st.columns([2.25, 1], gap="large")
    with left:
        st.markdown("#### Factor quantities")
        if model_key == "Stockholm|2021-02-01":
            main_groups = [
                ("Greenery — base factors (11)", lambda f: f.get("kind") == "base" and f["section"].startswith("green")),
                ("Greenery — supplementary factors (28)", lambda f: f.get("kind") == "supplementary" and f["section"].startswith("green")),
                ("Water and paving — base factors (5)", lambda f: f.get("kind") == "base" and f["section"].startswith("water")),
                ("Water — supplementary factors (9)", lambda f: f.get("kind") == "supplementary" and f["section"].startswith("water")),
            ]
            grp = st.selectbox("Factor category", [n for n, _ in main_groups], key=f"manual_major_{model_key}")
            chosen = [f for f in factors if next(fn for n,fn in main_groups if n == grp)(f)]
        else:
            sections = list(dict.fromkeys(f["section"] for f in factors))
            counts = Counter(f["section"] for f in factors)
            opts = [section_title(sec) + f" ({counts[sec]})" for sec in sections]
            lookup = dict(zip(opts, sections))
            selected_label = st.selectbox("Factor category", opts, key=f"manual_group_{model_key}")
            selected = lookup[selected_label]
            chosen = [f for f in factors if f["section"] == selected]
        st.caption(f"{len(chosen)} factor fields · Enter area (m²) or number of elements (pcs). Empty fields count as zero once the calculator is connected.")
        previous_section = None
        for i, item in enumerate(chosen):
            sec = item.get("section")
            if sec != previous_section:
                st.markdown(f'<div class="v-factor-section">{escape(section_title(sec))}</div>', unsafe_allow_html=True)
                previous_section = sec
            _factor_row(model_key, item, i)
    with right:
        st.markdown("#### Guidance")
        st.markdown('<div class="v-manual-banner v-manual-info"><strong>Applicable model</strong><div>'
                    f'{escape(project.municipality)} · {escape(project.version)}<br>'
                    'All factor groups are available using the selector. Entered quantities are preserved while navigating groups.'
                                           '</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="v-manual-banner v-manual-warning"><strong>Manual-entry limitation</strong><div>'
                    'Geometry, surface overlap, eligibility, and actual GYF compliance are not validated in this prototype.'
                                           '</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="v-manual-guidance"><strong>Factor documentation</strong><div>'
                    'Select “Eligibility and measurement notes” under a factor when guidance is supplied in the catalogue.'
                                           '</div></div>', unsafe_allow_html=True)
        if model_key == "Stockholm|2021-02-01":
            st.caption("Source: Stockholm City, Grönytefaktor för kvartersmark (2021-02-01), pp. 19–34. "
                       "The three ecosystem-service groups are Supporting, Cultural, and Regulating.")
        st.caption("No quantity is converted into a score in this UI-only phase.")
    continue_button("Continue to Plan & Quantities", "plan", "manual_continue")
