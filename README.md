# VERDIQ_V2 — Reference-Matched UI Prototype

UI-only standalone Streamlit prototype built to match the approved `UI_SAMPLE.jpg`.

## Repository layout
Put these files **directly in the repository root**:

```
streamlit_app.py
layout.py
pages.py
visuals.py
styles.css
requirements.txt
README.md
.streamlit/config.toml     <- inside a folder named .streamlit
```

`.streamlit/config.toml` sets the green theme and the 50 MB DXF upload limit shown in the UI.

## Deploy
1. Upload/replace the files above (keep `config.toml` inside `.streamlit/`).
2. Deploy `streamlit_app.py` on Streamlit Community Cloud.
3. Reboot the app after the commit so the new config is picked up.

## Notes
- Streamlit is pinned to `1.67.0`: the styling targets that version's widget markup. Upgrading may need small CSS adjustments.
- Designed for a desktop browser around 1600 px wide; narrower screens wrap gracefully.

## Limitations
**This is a visual prototype only.** DXF upload does not render the drawing, the plan, quantities, layer mapping, validation, recommendations and exports are sample content and not computed. No imports or dependencies on VERDIQ V1.
