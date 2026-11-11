"""Shell layout: header, navigation tabs, project-setup panel and workflow footer.

UI-only. No legacy Verdiq imports or GYF processing.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

import streamlit as st

from visuals import icon

ROOT = Path(__file__).resolve().parent

MODELS = {
    "Nacka": [("2019-10", "Version 2 - 2019-10", "Grönytefaktor – Nacka stad, version 2", "Nacka kommun")],
    "Stockholm": [("2021-02-01", "2021-02-01", "GYF – Grönytefaktor för kvartersmark", "Stockholms stad"),
                  ("2015-06-17", "2015-06-17", "GYF – Grönytefaktor för kvartersmark", "Stockholms stad")],
    "Täby": [("2017-04-25", "Västra Roslags-Näsby - 2017", "Grönytefaktor för Västra Roslags-Näsby", "Täby kommun")],
    "SGBC Miljöbyggnad": [("2026", "Miljöbyggnad - 2026", "Grönytefaktor inom Miljöbyggnad", "Sweden Green Building Council")],
}

# (page id, label, Material Symbols icon)
PAGES = [
    ("project", "Project Setup", ":material/folder_open:"),
    ("plan", "Plan & Quantities", ":material/stacks:"),
    ("assessment", "GYF Assessment", ":material/bar_chart:"),
    ("improvements", "Design Improvements", ":material/psychiatry:"),
    ("compare", "Compare Designs", ":material/view_column_2:"),
    ("reports", "Reports & Export", ":material/description:"),
]


@dataclass(frozen=True)
class Project:
    name: str
    project_type: str
    address: str
    municipality: str
    version: str
    model: str
    publisher: str
    target_override: bool
    target: float
    plot_area: float


def apply_styles() -> None:
    st.markdown("<style>" + (ROOT / "styles.css").read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)


def render_header() -> None:
    st.markdown(
        f'<div class="v-header"><div class="v-brand"><span class="v-logo">{icon("sprout", 34, "#ffffff", 2)}</span>'
        f'<div><div class="v-title">Verdiq Studio</div><div class="v-tagline">Green Infrastructure Design &amp; GYF Assessment</div></div></div>'
        f'<div class="v-top-icons">{icon("help", 34, "#ffffff", 1.6)}{icon("user", 34, "#ffffff", 1.6)}</div></div>',
        unsafe_allow_html=True)


def set_page(page: str) -> None:
    st.session_state.page = page


def render_navigation() -> None:
    cols = st.columns([1, 0.93, 0.93, 1.03, 0.93, 0.93], gap="medium")
    for col, (ident, label, ic) in zip(cols, PAGES):
        with col:
            st.button(label, icon=ic, key=f"nav_{ident}", use_container_width=True,
                      type="primary" if st.session_state.page == ident else "secondary",
                      on_click=set_page, args=(ident,))


def render_sidebar() -> Project:
    st.markdown('<div class="v-panel-title">Project Setup</div>'
                '<div class="v-panel-sub">Define project parameters and import the site plan.</div>', unsafe_allow_html=True)
    name = st.text_input("Project Name", value="", key="project_name", placeholder="Enter project name")
    kind = st.selectbox("Project Type", ["Residential", "Mixed-use", "Commercial", "School / Preschool", "Public space", "Other"],
                        key="project_type")
    address = st.text_input("Project Site Address", value="", key="project_address", placeholder="Enter project site address")
    muni = st.selectbox("Municipality", list(MODELS), key="municipality")
    choices = MODELS[muni]
    if st.session_state.get("gyf_version") not in [x[0] for x in choices]:
        st.session_state["gyf_version"] = choices[0][0]
    version = st.selectbox("GYF Version", [x[0] for x in choices],
                           format_func=lambda x: next(a[1] for a in choices if a[0] == x), key="gyf_version")
    selected = next(x for x in choices if x[0] == version)
    st.markdown(
        f'<div class="v-source"><div class="v-source-head">{icon("book", 20, "#1d5a3a", 1.8)}<span>Model and Source</span>'
        f'<span class="v-source-link">{icon("external", 18, "#1d7a48", 1.8)}</span></div>'
        f'<div class="v-source-body">{escape(selected[2])}.<br><b>Publisher:</b> {escape(selected[3])}.<br>'
        f'<b>Version:</b> {escape(selected[0])}.</div></div>', unsafe_allow_html=True)
    override = st.checkbox("Project-specific GYF target", value=True, key="target_override")
    st.markdown("<div class=\"v-hint\">(from the city’s GYF documentation)</div>", unsafe_allow_html=True)
    target = st.number_input("Target", min_value=0.0, max_value=5.0, value=0.60, step=0.05, format="%.2f",
                             disabled=not override, key="target")
    area = st.number_input("Plot Area (m²)", min_value=0.0, value=15894.40, step=10.0, format="%.2f", key="plot_area")
    with st.expander("Municipal requirements & guidance", icon=":material/description:"):
        st.caption("Official sources and project requirements will be connected in a later phase.")
    return Project(name, kind, address, muni, version, selected[2], selected[3], override, target, area)


def render_footer() -> None:
    current = [p[0] for p in PAGES].index(st.session_state.page)
    steps = []
    for i, (_, label, _) in enumerate(PAGES):
        cls = "on" if i == current else ("done" if i < current else "")
        steps.append(f'<div class="v-step {cls}"><span class="n">{i + 1}</span><span class="l">{escape(label)}</span></div>')
    line = '<span class="v-step-line"></span>'
    st.markdown(f'<div class="v-footer"><div class="v-footer-title">Workflow Progress {icon("info", 18, "#4b5a52", 1.8)}</div>'
                f'<div class="v-steps">{line.join(steps)}</div></div>', unsafe_allow_html=True)
