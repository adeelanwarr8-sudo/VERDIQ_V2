"""Six visual-only workspace pages. No calculations or processing.

All metrics, plans, factor tables, and recommendations are clearly labeled examples.
"""
from __future__ import annotations

import streamlit as st
from html import escape

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

    up, _ = st.columns([1.62, 1])
    with up:
        st.file_uploader("Upload DXF", type=["dxf"], key="dxf_upload", label_visibility="collapsed")

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
                    st.caption("Preview only. Geometry inspection, factor mapping and GYF quantity extraction belong to later increments.")
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
                            st.session_state["gyf_dxf_result"]=result
                        result=st.session_state.get("gyf_dxf_result")
                        if result and result.drawing_sha==preview.drawing_sha and result.version==project.version and result.rulebook_id==rb.meta.id:
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
        elif result.drawing_sha != __import__('hashlib').sha256(uploaded.getvalue()).hexdigest()[:16] or result.version!=project.version:
            st.info("DXF or rulebook selection changed. Run extraction again.")
        else:
            st.caption(f"DXF SHA: {result.drawing_sha} · rulebook SHA: {result.rulebook_sha} "
                       f"· unit conversion: {result.units_to_m}")
            if result.findings:
                for f in result.findings:
                    (st.error if f.severity=='error' else st.warning)(f"{f.code}: {f.text}")
            else:
                st.info("No preliminary flags. Advanced spatial validation is not yet complete.")
            if result.evidence:
                st.dataframe(result.evidence,hide_index=True,use_container_width=True)
            st.caption("This is preliminary geometry screening, not municipal compliance certification.")



def render_plan_quantities(project: Project) -> None:
    title("Plan & Quantities", "Review the drawing, organize factor groups, and inspect quantities in a future connected version.")
    st.markdown('<div class="v-callout v-warn">UI preview only · The values on this page are sample data and not taken from your DXF upload or manual entries.</div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.4, 1], gap="large")
    with left:
        st.markdown("#### Plan workspace")
        show_plan()
        st.caption("Placeholder plan · import, zoom, selection, and layer filtering will be connected later.")
    with right:
        st.markdown("#### Quantity inspector")
        group = st.selectbox("Factor group", ["All factors", "Planting", "Trees", "Hard surfaces", "Water", "Additional qualities"], key="quantity_group")
        st.dataframe(SAMPLE_ROWS, use_container_width=True, hide_index=True)
        st.markdown("#### Geometry checks")
        st.warning("No geometry checks have been performed. Validation appears here once DXF processing is integrated.")
        st.button("Edit quantities (coming later)", use_container_width=True, disabled=True)
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
