# VERDIQ_V2 — Reference-Matched UI Prototype

UI-only standalone Streamlit prototype designed against the approved `UI_SAMPLE.jpg` image. All seven files belong **directly in the GitHub repository root**.

## Deploy
1. Upload/replace all seven files in the root of `VERDIQ_V2` (not inside a folder).
2. Deploy `streamlit_app.py` using Streamlit Community Cloud.
3. Refresh the application after the commit.

## Contents
- `streamlit_app.py`: page shell and two-column composition
- `layout.py`: full-width green header, six tabs, left project-setup panel
- `pages.py`: six UI-only pages, including DXF/manual method selection
- `visuals.py`: vector illustration of a sample site plan
- `styles.css`: enlarged type, proportions, colours and visual components
- `requirements.txt`: Streamlit dependency
- `README.md`: instructions

## Limitations
**This is a visual prototype only.** DXF selection does not render the uploaded drawing, layer mapping does not save, example quantities are not computed, and checks, recommendations, and exports are not live. The reference image is an idealized design; some details will differ because Streamlit controls are native browser widgets. No imports or dependencies on VERDIQ V1.
