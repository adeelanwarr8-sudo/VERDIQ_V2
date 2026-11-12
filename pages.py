"""Six visual-only workspace pages. No calculations or processing.

All metrics, plans, factor tables, and recommendations are clearly labeled examples.
"""
from __future__ import annotations

import streamlit as st
from html import escape
import hashlib

from quantity_reconciliation_v2 import (quantity_context, reconcile, can_confirm, confirmed_snapshot)

from layout import Project
from dxf_viewer import parse_dxf, render_dxf_viewer
from gyf_engine_v2 import load_selected, inspect_dxf, assess_readiness
from manual_proforma import render_manual_proforma
from visuals import card, check_badge, continue_button, icon, kpi, plan_workspace_html, show_plan, title

SAMPLE_ROWS = [
    {"CAD layer": "G_Y3 · Planting beds", "Mapped factor": "Planting bed ≥800 mm", "Quantity": "3,678.1 m²", "Review": "Example"},
    {"CAD layer": "G_Y2 · Green ground", "Mapped factor": "Ground vegetation", "Quantity": "1,690.0 m²", "Review": "Example"},
    {"CAD layer": "K20 · Trees", "Mapped factor": "New medium trees", "Quantity": "44 pcs", "Review": "Example"},
    {"CAD layer": "G_Y0 · Hardscape", "Mapped factor": "Sealed surfaces", "Quantity": "6,137.2 m²", "Review": "Example"},
]



QUANTITIES = [("Planting bed ≥800 mm", "3,678.1", "m²", "0.9"),
              ("New medium-sized trees", "44", "pcs", "1.5"),
              ("Sealed surfaces", "6,137.2", "m²", "0.0"),
              ("Paved surfaces with permeability", "5,081.7", "m²", "–"),
              ("Shrubs (general)", "120.0", "m²", "0.2")]


def _quantity_table() -> str:
    body = "".join(f"<tr><td>{escape(f)}</td><td class=r>{q}</td><td class=c>{u}</td><td class=r>{w}</td></tr>"
                   for f, q, u, w in QUANTITIES)
    return ('<table class="v-qtable"><thead><tr><th>Factor</th><th class=r>Quantity</th><th class=c>Unit</th>'
            f'<th class=r>Weight</th></tr></thead><tbody>{body}</tbody></table>')


def render_project_setup(project: Project) -> None:
    st.markdown('<div class="v-main-heading">DXF Plan Workspace</div>'
                '<div class="v-main-sub">Upload a DXF drawing, view the plan, map layers and extract GYF quantities.</div>'
                '<div class="v-topspace"></div>',
                unsafe_allow_html=True)

    with st.container(border=True, key="method_card"):
       
        intro, options = st.columns([1, 2], gap="medium", vertical_alignment="center")
        with intro:
            st.markdown('<div class="v-method-title">Assessment Method</div>'
                        '<div class="v-method-sub">Choose how you want to provide quantities for your GYF assessment.</div>',
                        unsafe_allow_html=True)
        with options:
            method = st.radio(
                "Assessment method",
                [":material/stacks: **DXF Plan Analysis**", ":material/calculate: **Manual GYF Calculation**"],
                captions=["Upload a CAD drawing. Verdiq extracts surfaces, trees and quantities automatically.",
                          "Enter GYF quantities manually when no DXF file is available."],
                horizontal=True, key="assessment_method", label_visibility="collapsed")

    if "Manual" in method:
        render_manual_proforma(project)
        return

    st.markdown("**Upload GYF Marking Plan (DXF)**")
    st.caption(
        "**Preferred:** GYF Markeringsplan. A Landscape / Site Development Plan "
        "(Markplaneringsritning) is also accepted. A Site Plan (Situationsplan) "
        "alone is generally insufficient for a complete GYF assessment."
    )
    with st.expander("Which DXF drawing should I upload?"):
        st.markdown(
            "**1. GYF Marking Plan (GYF Markeringsplan) — Recommended.** "
            "Clearly identifies green and blue areas, trees, other GYF features, "
            "and their classifications.\n\n"
            "**2. Landscape / Site Development Plan (Markplaneringsritning) — Accepted.** "
            "Shows planting, surface materials, trees, and drainage; some GYF "
            "properties and factor assignments may need verification.\n\n"
            "**3. Site Plan (Situationsplan) — Supporting only.** "
            "Useful for site boundaries, building footprints, and dimensions, "
            "but normally lacks the detail needed for a complete GYF assessment."
        )
        st.caption(
            "Upload a native DXF containing measurable CAD entities and clearly named "
            "layers where possible. Imported images or flattened drawings cannot "
            "provide reliable geometry-based quantities."
        )

    up, _ = st.columns([1.62, 1])
    with up:
        st.file_uploader("Upload GYF Marking Plan (DXF)", type=["dxf"],
                         key="dxf_upload", label_visibility="collapsed")

    drawing_data = None
    uploaded = st.session_state.get("dxf_upload")
    if uploaded is not None:
        try:
            with st.spinner("Reading DXF drawing..."):
                drawing_data = parse_dxf(uploaded.getvalue())
        except (ValueError, OSError) as exc:
            st.error(f"DXF import failed: {exc}")

    tab_plan, tab_mapping, tab_validation = st.tabs(
        [":material/map: Plan view", ":material/stacks: Layer mapping", ":material/check_circle: Drawing validation"])
    with tab_plan:
        if drawing_data is None:
            st.info("Upload a DXF file to view its actual modelspace drawing. No sample plan is loaded.")
        else:
            drawing, details = st.columns([1.7, 1], gap="small")
            with drawing:
                render_dxf_viewer(drawing_data, height=560)
            with details:
                with st.container(border=True, key="qty_card"):
                    st.markdown("#### Drawing overview")
                    st.metric("CAD layers", len(drawing_data["layers"]))
                    st.metric("Modelspace entities", drawing_data["entity_count"])
                    st.metric("Rendered primitives", drawing_data["shape_count"])
                    st.caption("Interactive drawing preview. Review extracted quantities and geometry checks in the Layer Mapping and Drawing Validation tabs.")
                    if drawing_data["truncated"]:
                        st.warning("Preview truncated at 25,000 primitives. The full DXF has not been rendered.")
                    if drawing_data["skipped"]:
                        st.caption("Unsupported or unrendered entities: " + ", ".join(
                            f"{name} ({count})" for name, count in sorted(drawing_data["skipped"].items())))
    with tab_mapping:
        if drawing_data is None or uploaded is None:
            st.caption("Upload a DXF to inspect its CAD layers and propose GYF factor mappings.")
        else:
            try:
                rb, rb_sha = load_selected(project.municipality, project.version)
            except ValueError as exc:
                st.warning(str(exc))
            else:
                st.caption(f"Rulebook: {rb.meta.id} · version {rb.meta.version} · "
                           f"declared status {rb.meta.status} · SHA {rb_sha}")
                # Explicit units; never quietly assume the unitless drawing is in metres.
                with st.container(border=True):
                    unit_choice = st.selectbox("Drawing unit override", ["From DXF ($INSUNITS)",
                        "Metres", "Millimetres", "Centimetres", "Feet", "Inches"],
                        key="dxf_unit_choice")
                    conversion = {"From DXF ($INSUNITS)":None, "Metres":1.,
                                  "Millimetres":0.001, "Centimetres":0.01,
                                  "Feet":0.3048, "Inches":0.0254}[unit_choice]
                    try:
                        preview = inspect_dxf(uploaded.getvalue(),project.municipality,project.version,
                                              units_to_m=conversion, mapping={})
                    except (ValueError, OSError) as exc:
                        st.error(f"Quantity extraction unavailable: {exc}")
                    else:
                        factor_labels={f.id:f"{f.label.text('en')} [{f.id}]" for f in rb.factors}
                        ids=[""]+[f.id for f in rb.factors]
                        mapped={}
                        for layer in preview.layer_names:
                            suggested=preview.proposed_mapping.get(layer,"")
                            options=ids
                            choice=st.selectbox(f"CAD layer: {layer}",options,
                                index=options.index(suggested) if suggested in options else 0,
                                format_func=lambda x: factor_labels.get(x,"Do not map"),
                                key=f"mapping_{project.municipality}_{project.version}_{preview.drawing_sha}_{layer}")
                            if choice:mapped[layer]=choice
                        if st.button("Extract provisional GYF quantities", key="extract_gyf_review"):
                            result=inspect_dxf(uploaded.getvalue(),project.municipality,project.version,
                                               units_to_m=conversion,mapping=mapped)
                            result.review_mapping = dict(mapped)
                            result.selection = (project.municipality, project.version)
                            st.session_state["gyf_dxf_result"]=result
                        result=st.session_state.get("gyf_dxf_result")
                        if result and result.drawing_sha==preview.drawing_sha and result.version==project.version and result.rulebook_id==rb.meta.id and result.units_to_m == (conversion if conversion is not None else preview.units_to_m) and getattr(result, 'review_mapping', mapped) == mapped:
                            st.markdown("#### Provisional extracted quantities")
                            if result.quantities:
                                st.dataframe([{"Factor ID":fid,"Quantity":v,
                                              "Unit":rb.factor(fid).measure}
                                             for fid,v in sorted(result.quantities.items())],
                                             hide_index=True,use_container_width=True)
                            else:
                                st.caption("No extractable quantities. Check mappings and drawing units.")
                            st.caption(f"Assessment gate: {assess_readiness(result)}. "
                                       "These quantities are not yet accepted for GYF scoring.")
    with tab_validation:
        result=st.session_state.get("gyf_dxf_result")
        if result is None or uploaded is None:
            st.info("Upload a DXF and run provisional extraction to see rulebook and geometry findings.")
        elif (result.drawing_sha != __import__('hashlib').sha256(uploaded.getvalue()).hexdigest()[:16]
              or result.version != project.version
              or (project.municipality, project.version) != getattr(result, 'selection', (project.municipality, result.version))):
            st.info("DXF or municipality selection changed. Run extraction again.")
        else:
            st.caption(f"DXF SHA: {result.drawing_sha} · rulebook SHA: {result.rulebook_sha} "
                       f"· unit conversion: {result.units_to_m}")
            if result.findings:
                for f in result.findings:
                    (st.error if f.severity=='error' else st.warning)(f"{f.code}: {f.text}")
            else:
                st.info("No preliminary flags. Advanced spatial validation is not yet complete.")
            if result.evidence:
                st.markdown("#### Factor-level extraction evidence")
                st.dataframe(result.evidence,hide_index=True,use_container_width=True)
            if result.object_evidence:
                with st.expander(f"Object-level DXF audit ({len(result.object_evidence)} records)"):
                    st.caption("Raw measurements before polygon union, plot clipping, and municipal eligibility validation. CAD handles allow source tracing.")
                    st.dataframe(result.object_evidence, hide_index=True, use_container_width=True)
            st.caption("Spatial and object-level screening only. Geometry flags require human review; no municipal compliance certification or automatic repair is performed.")



def render_plan_quantities(project: Project) -> None:
    """Unified review of manual and DXF quantities; no municipal score is computed."""
    title("Plan & Quantities", "Review extracted and manually entered factor quantities. Select one source per factor before confirming.")
    model_key = f"{project.municipality}|{project.version}"
    from manual_proforma import CATALOG
    catalogue = CATALOG.get(model_key)
    if not catalogue:
        st.warning("No factor catalogue is available for the selected municipality/version.")
        return
    factors = catalogue["factors"]
    manual_store = st.session_state.get("manual_quantities", {})
    manual = {f["id"]: manual_store.get(f"{model_key}|{f['id']}", 0) for f in factors}

    extraction = st.session_state.get("gyf_dxf_result")
    upload = st.session_state.get("dxf_upload")
    dxf = {}
    matching = False
    if extraction:
        # Streamlit removes the file-uploader widget state when the user navigates
        # to a different page. Keep the already-extracted in-session snapshot.
        matching = (getattr(extraction, "selection", None) == (project.municipality, project.version)
                    and (upload is None or getattr(extraction, "drawing_sha", None)
                         == hashlib.sha256(upload.getvalue()).hexdigest()[:16]))
        if matching:
            dxf = extraction.quantities
    if extraction and not matching:
        st.warning("A prior DXF extraction does not match this drawing or municipality/version. It has not been included.")
    if matching and upload is None:
        st.caption("Using the last extracted DXF snapshot from this session (the upload control is on Project Setup).")
    try:
        rb, rb_sha = load_selected(project.municipality, project.version)
    except ValueError:
        rb_sha = None
    # Bind final review to the exact extraction provenance and mapping, when available.
    context = quantity_context(project.municipality, project.version,
                               extraction.drawing_sha if matching else None,
                               extraction.rulebook_sha if matching else rb_sha,
                               getattr(extraction, "review_mapping", {}) if matching else {},
                               extraction.units_to_m if matching else None)
    existing = st.session_state.get("v2_quantity_ledger")
    if not existing or existing.get("context") != context:
        st.session_state["v2_quantity_ledger"] = {"context": context, "choices": {}, "overrides": {}}
        st.session_state.pop("v2_quantity_confirmation", None)
    ledger = st.session_state["v2_quantity_ledger"]

    st.caption(f"{project.municipality} · {project.version} · {len(factors)} municipal factor fields"
               + (" · Matching DXF extraction available" if matching else " · No matching DXF extraction"))
    st.markdown('<div class="v-callout v-warn">Quantities are for user review only. No municipal eligibility, geometry approval, GYF score, or compliance result is issued here.</div>', unsafe_allow_html=True)
    group_names = list(dict.fromkeys(str(f.get("section", "")) for f in factors))
    group = st.selectbox("Factor group", ["Factors with quantities", "All factors"] + group_names,
                         key="v2_review_group")
    choices = ledger["choices"]
    overrides = ledger["overrides"]
    baseline = reconcile(factors, manual, dxf, choices=choices, overrides=overrides)
    visible = ([r for r in baseline if r.has_dxf or r.has_manual or r.source == "Override"]
               if group == "Factors with quantities" else baseline if group == "All factors"
               else [r for r in baseline if r.section == group])
    st.caption(f"Showing {len(visible)} factors. Source choices replace other sources; they never add them together.")

    for row in visible:
        row_id = row.factor_id
        with st.container(border=True):
            header, measured, manual_col = st.columns([2.7, 1, 1], vertical_alignment="center", gap="small")
            with header:
                st.markdown(f"**{escape(row.label)}**")
                st.caption(f"{row_id} · {row.measure} · {row.section}")
            with measured:
                st.caption("DXF extracted")
                st.markdown(f"**{row.dxf:,.2f}**" if row.measure != "count" else f"**{row.dxf:,.0f}**")
            with manual_col:
                st.caption("Manual input")
                st.markdown(f"**{row.manual:,.2f}**" if row.measure != "count" else f"**{row.manual:,.0f}**")
            select_col, input_col = st.columns([1.3, 1], gap="medium")
            with select_col:
                allowed = ["Unresolved", "DXF", "Manual", "Override", "Exclude"]
                selected = st.selectbox("Quantity source", allowed, index=allowed.index(row.source),
                                        key=f"v2_source_{context}_{row_id}")
                choices[row_id] = selected
            with input_col:
                if selected == "Override":
                    is_count = row.measure == "count"
                    val = st.number_input("Override quantity (pcs)" if is_count else "Override quantity (m²)",
                                          min_value=0 if is_count else 0.0,
                                          value=int(overrides.get(row_id, 0)) if is_count else float(overrides.get(row_id, 0)),
                                          step=1 if is_count else 1.0,
                                          key=f"v2_override_{context}_{row_id}")
                    overrides[row_id] = val
                elif selected == "Unresolved":
                    st.warning("Choose one source")
                else:
                    st.caption("Final quantity uses the selected source only.")
    rows = reconcile(factors, manual, dxf, choices=choices, overrides=overrides)
    current = [r for r in rows if r.final is not None and r.final > 0]
    st.markdown("#### Quantity reconciliation summary")
    st.dataframe([{"Factor": r.label, "Source": r.source, "Final quantity": r.final,
                   "Measure": r.measure, "Review status": r.status} for r in current],
                 hide_index=True, use_container_width=True)
    blocking = bool(matching and any(f.severity == "error" for f in extraction.findings)
                    and any(r.source == "DXF" and r.dxf > 0 for r in rows))
    allowed, reasons = can_confirm(rows, blocking_findings=blocking)
    for reason in reasons:
        st.warning(reason)
    if st.button("Confirm reviewed factor quantities", type="primary", disabled=not allowed,
                 key="v2_confirm_quantities"):
        st.session_state["v2_quantity_confirmation"] = confirmed_snapshot(rows, context=context)
        st.success("Quantity selections confirmed for this session. Municipal eligibility remains unverified.")
    confirmation = st.session_state.get("v2_quantity_confirmation")
    if confirmation and confirmation.get("context") == context:
        # Do not present stale confirmation if inputs have been edited after confirming.
        candidate = confirmed_snapshot(rows, context=context)
        if candidate["evidence"] == confirmation["evidence"]:
            st.info("Reviewed quantities are confirmed for this session. They have NOT been approved for GYF scoring.")
        else:
            st.session_state.pop("v2_quantity_confirmation", None)
            st.warning("Quantity values or source selections changed; confirm the revised quantities again.")
    st.caption("Entered quantities are session-only; no database persistence or audit export is implemented yet.")
    continue_button("Continue to GYF Assessment", "assessment", "continue_quantities")


def render_gyf_assessment(project: Project) -> None:
    title("GYF Assessment", "Illustrative scorecard design — not an actual GYF result or compliance determination.")
    st.markdown('<div class="v-callout v-warn">EXAMPLE VALUES ONLY · Calculations, targets, ecosystem-service balancing, and compliance checks are not implemented.</div>', unsafe_allow_html=True)
    st.write("")
    a,b,c,d = st.columns(4, gap="small")
    with a: kpi("Example GYF score", "0.33", "Demonstration value", True)
    with b: kpi("Example target", "0.60", "Illustrative threshold")
    with c: kpi("Example eco-effective area", "5,241 m²", "Demonstration value")
    with d: kpi("Example shortfall", "4,296 m²", "Demonstration value", True)
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown("#### Ecosystem-service balancing")
        for label, value in [("Social values", 25),("Stormwater management", 40),("Biodiversity", 48),("Local climate", 35),("Air purification", 55)]:
            st.caption(f"{label} · illustrative {value}%")
            st.progress(value)
        st.markdown("#### Assessment messages")
        st.warning("No assessment has been performed. The indicators above illustrate dashboard placement only.")
    with right:
        st.markdown("#### Plan reference")
        show_plan(height=270)
        st.caption("Illustrative plan, not calculated geometry.")
    continue_button("Continue to Design Improvements", "improvements", "continue_assessment")


def render_design_improvements(project: Project) -> None:
    title("Design Improvements", "Visual concept for exploring future site-design improvements and scenario packages.")
    st.markdown('<div class="v-callout v-warn">Sample recommendations only. No feasibility, GYF gain, balancing change, or spatial suitability has been computed.</div>', unsafe_allow_html=True)
    st.write("")
    left,right = st.columns([1.25,1],gap="large")
    with left:
        st.markdown("#### Suggested interventions · illustrative")
        for name, detail, tag in [
            ("Enhance planting quality", "Add biodiversity qualities where suitable planting beds already exist.", "Vegetation"),
            ("Introduce new trees", "Explore potential tree planting zones subject to buildability and root space.", "Trees"),
            ("Improve stormwater retention", "Investigate rain gardens or retention opportunities in paved areas.", "Water"),
        ]:
            card(name, f"<span class='v-pill'>{tag}</span><p style='font-size:12px;color:#6b7b70;margin-top:10px'>{detail}</p>")
        st.markdown("#### Design choices")
        st.multiselect("Intervention themes to explore", ["Biodiversity", "Trees", "Stormwater", "Permeable surfaces", "Thermal comfort"], default=["Biodiversity", "Trees"], key="intervention_themes")
        st.caption("Selections change the prototype UI only.")
    with right:
        st.markdown("#### Example improvement overlay")
        show_plan(improved=True)
        st.caption("Illustrative additions are not derived from a spatial model.")
        kpi("Example improvement", "+0.15", "Not calculated")
    continue_button("Continue to Compare Designs", "compare", "continue_improvements")


def render_compare_designs(project: Project) -> None:
    title("Compare Designs", "Side-by-side design comparison using the same illustrative plan extent.")
    st.markdown('<div class="v-callout v-warn">UI sample only · Neither plan represents a processed DXF file or a validated GYF scenario.</div>', unsafe_allow_html=True)
    st.write("")
    left,right = st.columns(2, gap="medium")
    with left:
        st.markdown("#### Original design")
        show_plan()
        st.metric("Example GYF", "0.33")
        st.caption("Illustrative baseline")
    with right:
        st.markdown("#### Improved design")
        show_plan(improved=True)
        st.metric("Example GYF", "0.48", delta="+0.15")
        st.caption("Illustrative proposal — not computed")
    st.markdown("#### Comparison summary")
    st.dataframe([
        {"Indicator": "GYF score", "Original": "0.33", "Proposed": "0.48", "Status": "Example"},
        {"Indicator": "Eco-effective area", "Original": "5,241 m²", "Proposed": "7,683 m²", "Status": "Example"},
        {"Indicator": "Geometry checks", "Original": "Not run", "Proposed": "Not run", "Status": "Pending integration"},
    ], use_container_width=True, hide_index=True)
    continue_button("Continue to Reports & Export", "reports", "continue_compare")


def render_reports_export(project: Project) -> None:
    title("Reports & Export", "Preview the document types and project summary that the completed platform will provide.")
    left,right = st.columns([1.1,1], gap="large")
    with left:
        card("Project summary", f"<div style='font-size:13px;line-height:2'>"
             f"<strong>Project:</strong> {escape(project.name)}<br><strong>Type:</strong> {escape(project.project_type)}<br>"
             f"<strong>Municipality:</strong> {escape(project.municipality)}<br><strong>Model:</strong> {escape(project.model)}<br>"
             f"<strong>Version:</strong> {project.version}<br><strong>Plot area:</strong> {project.plot_area:,.2f} m²</div>")
        st.markdown("#### Available report formats (future)")
        for label, note in [("PDF assessment report", "Project, calculation, balancing, and audit trail"),
                            ("Municipal Excel workbook", "Municipality-specific calculation template"),
                            ("CSV quantities", "Validated factor quantities"),
                            ("JSON project data", "Structured machine-readable results")]:
            with st.container(border=True):
                a,b = st.columns([2.4,1],vertical_alignment="center")
                with a:
                    st.markdown(f"**{label}**")
                    st.caption(note)
                with b:
                    st.button("Export later", key=f"export_{label}", disabled=True, use_container_width=True)
    with right:
        st.markdown("#### Report preview")
        st.markdown('<div class="v-card" style="min-height:350px;padding:25px">'
                    '<div style="color:#2b8056;font-size:12px;letter-spacing:2px;font-weight:750">VERDIQ STUDIO</div>'
                    '<div style="font-size:25px;font-weight:800;margin:15px 0 5px">GYF Assessment Report</div>'
                    '<div style="color:#7a8b80;font-size:12px;margin-bottom:25px">Preview only · Not generated</div>'
                    '<hr style="border:0;border-top:1px solid #e1ebe3"/>'
                    '<p style="font-size:13px">Project identification and applicable methodology</p>'
                    '<p style="font-size:13px">Site quantities and ecosystem-service balancing</p>'
                    '<p style="font-size:13px">Geometry findings and design scenarios</p>'
                    '<p style="font-size:13px">References and methodological limitations</p>'
                    '<div style="background:#f0f5f0;padding:14px;border-radius:8px;margin-top:40px;font-size:12px;color:#65756a">Document generation not connected.</div>'
                    '</div>', unsafe_allow_html=True)
    st.info("Document export is disabled in the UI-only phase.")
