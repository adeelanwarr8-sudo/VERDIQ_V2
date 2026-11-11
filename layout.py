"""Shared branding, navigation, and project sidebar for the UI prototype."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import streamlit as st

CSS = Path(__file__).resolve().parent.parent / "assets" / "styles.css"

MODEL_OPTIONS = {
    "Nacka": [
        ("2019-10", "Grönytefaktor – Nacka stad, version 2", "Nacka Municipality"),
    ],
    "Stockholm": [
        ("2021-02-01", "GYF – Grönytefaktor för kvartersmark", "City of Stockholm"),
        ("2015-06-17", "GYF – Grönytefaktor för kvartersmark", "City of Stockholm"),
    ],
    "Täby": [
        ("2017-04-25", "Grönytefaktor för Västra Roslags-Näsby", "Täby Municipality"),
    ],
    "SGBC Miljöbyggnad": [
        ("2026", "Grönytefaktor inom Miljöbyggnad", "Sweden Green Building Council"),
    ],
}

PAGES = [
    ("project", "01", "Project Setup", "📁"),
    ("plan", "02", "Plan & Quantities", "▦"),
    ("assessment", "03", "GYF Assessment", "▥"),
    ("improvements", "04", "Design Improvements", "✳"),
    ("compare", "05", "Compare Designs", "◫"),
    ("reports", "06", "Reports & Export", "▤"),
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
    st.markdown(f"<style>{CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_header() -> None:
    st.markdown(
        '<div class="v-header"><div class="v-brand"><span class="v-leaf">❧</span>'
        '<div><div class="v-title">Verdiq Studio <span class="v-version">V2</span></div>'
        '<div class="v-tagline">Green Infrastructure Design &amp; GYF Assessment</div></div></div>'
        '<div class="v-header-right">UI Prototype &nbsp; • &nbsp; English</div></div>',
        unsafe_allow_html=True,
    )


def set_page(page: str) -> None:
    st.session_state.page = page


def render_navigation() -> None:
    columns = st.columns(6, gap="small")
    for column, (page_id, number, label, icon) in zip(columns, PAGES):
        with column:
            selected = st.session_state.page == page_id
            st.button(
                f"{icon}  {number}  {label}",
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if selected else "secondary",
                on_click=set_page,
                args=(page_id,),
            )
    st.markdown('<div class="v-nav-space"></div>', unsafe_allow_html=True)


def render_sidebar() -> Project:
    with st.sidebar:
        st.markdown('<div class="v-side-brand">PROJECT SETTINGS</div>', unsafe_allow_html=True)
        name = st.text_input("Project name", value="Nacka Demonstration", key="project_name")
        project_type = st.selectbox("Project type", ["Residential", "Mixed-use", "Commercial", "School / Preschool", "Public space", "Other"], key="project_type")
        address = st.text_input("Project site address", value="Nacka, Stockholm County", key="project_address")
        st.divider()
        municipality = st.selectbox("Municipality / Scheme", list(MODEL_OPTIONS), key="municipality")
        options = MODEL_OPTIONS[municipality]
        valid_versions = [item[0] for item in options]
        if st.session_state.get("gyf_version") not in valid_versions:
            st.session_state["gyf_version"] = valid_versions[0]
        version = st.selectbox("GYF version", [item[0] for item in options], key="gyf_version")
        chosen = next(x for x in options if x[0] == version)
        st.markdown(
            f'<div class="v-source"><div class="v-source-head">MODEL &amp; SOURCE</div>'
            f'<strong>{chosen[1]}</strong><div>Publisher: {chosen[2]}</div>'
            f'<div>Version: {chosen[0]}</div><div class="v-source-note">Illustrative metadata · source validation comes later</div></div>',
            unsafe_allow_html=True,
        )
        st.caption("Rulebooks are not loaded in this UI-only prototype.")
        st.divider()
        override = st.checkbox("Project-specific GYF target", value=True, key="target_override")
        target = st.number_input("Target GYF", min_value=0.0, max_value=5.0, value=0.60, step=0.05, format="%.2f", disabled=not override, key="target")
        if not override:
            st.caption("Automatic municipal targets will be connected later.")
        plot_area = st.number_input("Plot area (m²)", min_value=0.0, value=15894.40, step=10.0, format="%.2f", key="plot_area")
        st.divider()
        st.markdown('<div class="v-sidebar-foot">◌ &nbsp; Demo workspace — inputs are not saved to a project file.</div>', unsafe_allow_html=True)
        return Project(name, project_type, address, municipality, version, chosen[1], chosen[2], override, target, plot_area)
