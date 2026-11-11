# VERDIQ_V2 — Compact UI optimization

Independent Streamlit UI-only prototype. No connections to the previous VERDIQ repository.

## Install

Upload the **contents** of this folder to the root of your `VERDIQ_V2` GitHub repository. Preserve the `.streamlit/config.toml` folder path. Replace the current files and commit to `main`. On Streamlit Community Cloud, reboot if the theme config has changed.

Entry point: `streamlit_app.py`. Dependencies: `requirements.txt` (Streamlit 1.67.0).

## UI refinements

- Header and six-button navigation occupy distinct normal-flow rows; no negative top margin overlap.
- Duplicate bottom workflow progress strip removed.
- Compact Project Setup panel and separated Model/Source and target controls.
- More compact heading, method selection, upload drop-zone, plan toolbar, tab strip, quantity summary, and primary action.
- CSS includes desktop breakpoint adjustments for approximately 1366px and 1920px wide viewports.
- Placeholder status is labeled as an example rather than claiming uploaded DXF processing or verified geometry.

## Scope

This remains a **UI prototype**. Uploaded DXF files are not parsed. Charts, plans and quantities are example content. The toolbar illustrations are not functioning GIS tools. Do not interpret the example data as a calculation or compliance determination.

## Validation performed

Python source compiles and static checks confirm the flat root imports and all six pages are retained. Live Streamlit/browser rendering was **not** available in this execution environment; visual verification is required after deployment at 100% browser zoom.
