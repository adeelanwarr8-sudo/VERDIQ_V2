"""VERDIQ_V2 — reference-matched, standalone Streamlit UI prototype."""
from __future__ import annotations
import streamlit as st
st.set_page_config(page_title='Verdiq Studio V2 · UI Prototype',page_icon='🌿',layout='wide',initial_sidebar_state='collapsed')
from layout import apply_styles,render_header,render_navigation,render_sidebar
from pages import render_project_setup,render_plan_quantities,render_gyf_assessment,render_design_improvements,render_compare_designs,render_reports_export

def main():
 apply_styles()
 st.session_state.setdefault('page','project')
 render_header()
 render_navigation()
 left,right=st.columns([0.255,1],gap='small')
 with left:
  with st.container(border=True):project=render_sidebar()
 with right:
  with st.container(border=True):
   pages={'project':render_project_setup,'plan':render_plan_quantities,'assessment':render_gyf_assessment,'improvements':render_design_improvements,'compare':render_compare_designs,'reports':render_reports_export}
   pages.get(st.session_state.page,render_project_setup)(project)
 st.markdown('<div class="v-footer">Workflow progress &nbsp; ① Project Setup ─── ② Plan &amp; Quantities ─── ③ GYF Assessment ─── ④ Design Improvements ─── ⑤ Compare Designs ─── ⑥ Reports &amp; Export</div>',unsafe_allow_html=True)
if __name__=='__main__':main()
