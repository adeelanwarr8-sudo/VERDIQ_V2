"""VERDIQ_V2 — reference-matched, standalone Streamlit UI prototype."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Verdiq Studio", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

from layout import apply_styles, render_footer, render_header, render_navigation, render_sidebar  # noqa: E402
from pages import (render_compare_designs, render_design_improvements, render_gyf_assessment,  # noqa: E402
                   render_plan_quantities, render_project_setup, render_reports_export)

PAGE_RENDERERS = {
    "project": render_project_setup,
    "plan": render_plan_quantities,
    "assessment": render_gyf_assessment,
    "improvements": render_design_improvements,
    "compare": render_compare_designs,
    "reports": render_reports_export,
}


def main() -> None:
    apply_styles()
    st.session_state.setdefault("page", "project")
    render_header()
    with st.container(key="nav"):
        render_navigation()
    left, right = st.columns([1, 3.98], gap="small")
    with left:
        with st.container(border=True, key="side_panel"):
            project = render_sidebar()
    with right:
        with st.container(border=True, key="main_panel"):
            PAGE_RENDERERS.get(st.session_state.page, render_project_setup)(project)
    render_footer()


if __name__ == "__main__":
    main()
