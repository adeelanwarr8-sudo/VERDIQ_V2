"""Six visual-only workspace pages. No calculations or processing.

All metrics, plans, factor tables, and recommendations are clearly labeled examples.
"""
from __future__ import annotations

import streamlit as st
from html import escape

from layout import Project
from visuals import card, continue_button, kpi, show_plan, title

SAMPLE_ROWS = [
    {"CAD layer": "G_Y3 · Planting beds", "Mapped factor": "Planting bed ≥800 mm", "Quantity": "3,678.1 m²", "Review": "Example"},
    {"CAD layer": "G_Y2 · Green ground", "Mapped factor": "Ground vegetation", "Quantity": "1,690.0 m²", "Review": "Example"},
    {"CAD layer": "K20 · Trees", "Mapped factor": "New medium trees", "Quantity": "44 pcs", "Review": "Example"},
    {"CAD layer": "G_Y0 · Hardscape", "Mapped factor": "Sealed surfaces", "Quantity": "6,137.2 m²", "Review": "Example"},
]


def render_project_setup(project: Project) -> None:
    st.markdown('<div class="v-main-heading">DXF Plan Workspace</div><div class="v-main-sub">Upload a DXF drawing, view the plan, map layers and extract GYF quantities.</div>', unsafe_allow_html=True)
    st.markdown('<div class="v-method-title">Assessment Method</div><div class="v-main-sub">Choose how you want to provide quantities for your GYF assessment.</div>', unsafe_allow_html=True)
    method=st.radio('Assessment method', ['DXF Plan Analysis','Manual GYF Calculation'],horizontal=True,key='assessment_method',label_visibility='collapsed')
    if method=='Manual GYF Calculation':
        st.markdown('<div class="v-main-heading v-topspace">Manual GYF Calculation</div><div class="v-main-sub">Enter quantities directly without a DXF drawing. This is a visual prototype; calculations are not connected.</div>',unsafe_allow_html=True)
        c1,c2=st.columns([1.5,1],gap='medium')
        with c1:
            with st.container(border=True):
                grp=st.selectbox('Factor category',['Ground and planting','Trees and vegetation','Water and stormwater','Supplementary qualities'],key='manual_cat')
                rows={'Ground and planting':['Preserved natural ground (m²)','Planting bed ≥800 mm (m²)','Sealed surfaces (m²)'],'Trees and vegetation':['Existing trees (pcs)','New medium trees (pcs)','Shrubs (m²)'],'Water and stormwater':['Water bodies (m²)','Rain gardens (m²)'],'Supplementary qualities':['Field diversity (m²)','Nest boxes (pcs)']}
                for i,n in enumerate(rows[grp]):st.number_input(n,min_value=0.,step=1.,key=f'manu_{grp}_{i}')
        with c2:
            st.markdown('<div class="v-callout">Manual quantities will use the selected municipal rulebook when the calculation engine is connected.</div>',unsafe_allow_html=True)
            st.warning('Spatial geometry validation is unavailable in manual-entry mode.')
        continue_button('Continue to Plan & Quantities →','plan','manual_continue')
        return
    status=st.columns(3,gap='small')
    for col,ic,txt in zip(status,['✓','▤','♧'],['DXF imported · example','6 layers mapped · example','44 trees detected · example']):
        with col:st.markdown(f'<div class="v-status">{ic} &nbsp; {txt}</div>',unsafe_allow_html=True)
    uploaded=st.file_uploader('Upload DXF',type=['dxf'],key='mock_dxf',help='Upload control demonstration: DXF content is not read or rendered in this UI-only phase.')
    if uploaded is not None:st.caption(f'Selected: {escape(uploaded.name)} — file not processed. The drawing below remains a sample illustration.')
    tab_plan,tab_mapping,tab_validation=st.tabs(['▣  Plan view','▤  Layer mapping','◉  Drawing validation'])
    with tab_plan:
        drawing,quantities=st.columns([1.32,1],gap='small')
        with drawing:
            st.markdown('<div class="v-tools">↖ &nbsp; ✋ &nbsp; ⊕ &nbsp; ⊖ &nbsp; ⛶ &nbsp; │ &nbsp; ✎ <span style="float:right">▤ &nbsp; Layers ▾</span></div>',unsafe_allow_html=True)
            show_plan(height=480)
            st.markdown('<div class="v-legend">🟩 Planted ground &nbsp;&nbsp; ▫️ Permeable paving &nbsp;&nbsp; ◼ Sealed &nbsp;&nbsp; ● Trees</div>',unsafe_allow_html=True)
        with quantities:
            st.markdown('<div class="v-qtitle">Detected Quantities <span style="float:right;color:#2f7851;font-size:12px">✎ Edit quantities (later)</span></div>',unsafe_allow_html=True)
            st.dataframe([{'Factor':'Planting bed ≥800 mm','Quantity':'3,678.1','Unit':'m²','Weight':'0.9'}, {'Factor':'New medium-sized trees','Quantity':'44','Unit':'pcs','Weight':'1.5'}, {'Factor':'Sealed surfaces','Quantity':'6,137.2','Unit':'m²','Weight':'0.0'}, {'Factor':'Paved surfaces','Quantity':'5,081.7','Unit':'m²','Weight':'—'}, {'Factor':'Shrubs (general)','Quantity':'120.0','Unit':'m²','Weight':'0.2'}],hide_index=True,use_container_width=True)
            st.markdown('<div class="v-status">✓ &nbsp; Example drawing: no problems shown</div>',unsafe_allow_html=True)
            st.caption('Sample visualization only; no DXF geometry has been checked.')
            continue_button('Confirm quantities and proceed to GYF assessment →','assessment','confirm_quantities_mock')
    with tab_mapping:
        st.info('Layer mapping interface preview. No uploaded file is processed.')
        a,b=st.columns(2)
        with a:st.selectbox('CAD layer',['G_Y3 · Planting beds','G_Y2 · Ground','K20 · Trees'],key='cad_layer')
        with b:st.selectbox('GYF factor',['Planting bed ≥800 mm','Ground vegetation','New medium-sized trees'],key='gyf_factor')
        st.button('Save mapping (not connected)',disabled=True)
    with tab_validation:
        st.warning('Drawing validation has not been performed. The geometry engine will be added in a later stage.')
        st.dataframe([{'Check':'Plot boundary','Status':'Not run'},{'Check':'Overlapping surfaces','Status':'Not run'},{'Check':'Unmapped layers','Status':'Not run'}],hide_index=True,use_container_width=True)


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
    continue_button("Continue to GYF Assessment →", "assessment", "continue_quantities")


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
    continue_button("Continue to Design Improvements →", "improvements", "continue_assessment")


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
    continue_button("Continue to Compare Designs →", "compare", "continue_improvements")


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
    continue_button("Continue to Reports & Export →", "reports", "continue_compare")


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
