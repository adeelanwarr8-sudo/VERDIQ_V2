"""VERDIQ_V2 — standalone UI-only Streamlit prototype.

No calculations, municipality rulebooks, DXF interpretation, or exports are connected.
Run locally: streamlit run streamlit_app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Verdiq Studio V2 | UI Prototype", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

from app.layout import apply_styles, render_header, render_navigation, render_sidebar  # noqa: E402
from app.pages import (  # noqa: E402
    render_project_setup, render_plan_quantities, render_gyf_assessment,
    render_design_improvements, render_compare_designs, render_reports_export,
)


def main() -> None:
    apply_styles()
    st.session_state.setdefault("page", "project")
    render_header()
    render_navigation()
    project = render_sidebar()
    pages = {
        "project": render_project_setup,
        "plan": render_plan_quantities,
        "assessment": render_gyf_assessment,
        "improvements": render_design_improvements,
        "compare": render_compare_designs,
        "reports": render_reports_export,
    }
    pages.get(st.session_state.page, render_project_setup)(project)
    st.markdown('<div class="v-footer">VERDIQ V2 · UI DESIGN PROTOTYPE · Example data only — no regulatory assessment or file processing</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
