"""Standalone UI-only layout. No legacy Verdiq imports or GYF processing."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from html import escape
import streamlit as st

ROOT=Path(__file__).resolve().parent
MODELS={
 'Nacka':[('2019-10','Version 2 · 2019-10','Grönytefaktor – Nacka stad, version 2','Nacka kommun')],
 'Stockholm':[('2021-02-01','2021-02-01','GYF – Grönytefaktor för kvartersmark','Stockholms stad'),('2015-06-17','2015-06-17','GYF – Grönytefaktor för kvartersmark','Stockholms stad')],
 'Täby':[('2017-04-25','Västra Roslags-Näsby · 2017','Grönytefaktor för Västra Roslags-Näsby','Täby kommun')],
 'SGBC Miljöbyggnad':[('2026','Miljöbyggnad · 2026','Grönytefaktor inom Miljöbyggnad','Sweden Green Building Council')],
}
PAGES=[('project','Project Setup','▱'),('plan','Plan & Quantities','▱'),('assessment','GYF Assessment','▥'),('improvements','Design Improvements','♧'),('compare','Compare Designs','◧'),('reports','Reports & Export','▤')]
@dataclass(frozen=True)
class Project:
 name:str;project_type:str;address:str;municipality:str;version:str;model:str;publisher:str;target_override:bool;target:float;plot_area:float

def apply_styles():
 st.markdown('<style>'+ (ROOT/'styles.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)

def render_header():
 st.markdown('''<div class="v-header"><div class="v-brand"><span class="v-logo">🌿</span><div><div class="v-title">Verdiq Studio</div><div class="v-tagline">Green Infrastructure Design &amp; GYF Assessment</div></div></div><div class="v-top-icons">ⓘ &nbsp; ♙</div></div>''',unsafe_allow_html=True)

def set_page(page):st.session_state.page=page

def render_navigation():
 cols=st.columns(6,gap='small')
 for col,(ident,label,ic) in zip(cols,PAGES):
  with col:
   st.button(f'{ic}  {label}',key=f'nav_{ident}',use_container_width=True,type='primary' if st.session_state.page==ident else 'secondary',on_click=set_page,args=(ident,))
 st.markdown('<div class="v-nav-gap"></div>',unsafe_allow_html=True)

def render_sidebar()->Project:
 st.markdown('<div class="v-panel-title">Project Setup</div><div class="v-panel-sub">Define project parameters and import the site plan.</div>',unsafe_allow_html=True)
 name=st.text_input('Project Name',value='Nacka Demonstration',key='project_name')
 kind=st.selectbox('Project Type',['Residential','Mixed-use','Commercial','School / Preschool','Public space','Other'],key='project_type')
 address=st.text_input('Project Site Address',value='Sickla Allé 12, 131 54 Nacka, Sweden',key='project_address')
 muni=st.selectbox('Municipality',list(MODELS),key='municipality')
 choices=MODELS[muni]
 if st.session_state.get('gyf_version') not in [x[0] for x in choices]:st.session_state['gyf_version']=choices[0][0]
 version=st.selectbox('GYF Version',[x[0] for x in choices],format_func=lambda x:next(a[1] for a in choices if a[0]==x),key='gyf_version')
 selected=next(x for x in choices if x[0]==version)
 st.markdown(f'<div class="v-source"><div class="v-source-head">▣ &nbsp; Model and Source</div><div>{escape(selected[2])}.</div><div><b>Publisher:</b> {escape(selected[3])}.</div><div><b>Version:</b> {escape(selected[0])}.</div></div>',unsafe_allow_html=True)
 override=st.checkbox('Project-specific GYF target',value=True,key='target_override',help="From the city's GYF documentation")
 st.markdown('<div class="v-hint">(from the city’s GYF documentation)</div>',unsafe_allow_html=True)
 target=st.number_input('Target',min_value=0.0,max_value=5.0,value=.60,step=.05,format='%.2f',disabled=not override,key='target')
 area=st.number_input('Plot Area (m²)',min_value=0.,value=15894.40,step=10.,format='%.2f',key='plot_area')
 with st.expander('Municipal requirements & guidance'):
  st.caption('UI placeholder. Official sources and project requirements will be connected in a later phase.')
 return Project(name,kind,address,muni,version,selected[2],selected[3],override,target,area)
