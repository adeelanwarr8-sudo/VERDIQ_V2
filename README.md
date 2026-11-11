# VERDIQ_V2 — standalone UI-only prototype (flat repository)

Upload **all seven files** in this folder directly to your GitHub repository root (the same level as `streamlit_app.py`). No `app/` or `assets/` directory is needed.

- `streamlit_app.py` — Streamlit entrypoint
- `layout.py` — header, navigation, project sidebar
- `pages.py` — six prototype pages
- `visuals.py` — plan illustrations and UI helpers
- `styles.css` — UI styling
- `requirements.txt` — Streamlit dependency
- `README.md` — these instructions

In Streamlit Community Cloud, deploy `streamlit_app.py` on the `main` branch. After pushing changes, reboot the app if the previous deployment remains cached.

This UI prototype uses illustrative values and does not calculate GYF or parse DXF drawings. No connection to the prior VERDIQ repository is required.
