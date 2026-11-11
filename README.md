# Verdiq Studio V2 — UI-only prototype

A **standalone Streamlit interface prototype** for a future Swedish municipality-specific Green Area Factor (GYF) design and assessment platform.

**This is not a working GYF calculator.** It does not parse DXF files, retrieve rulebooks, calculate a score, validate geometry, make real design recommendations, or generate reports. All plans, quantities, balancing bars, and metrics shown are illustrative mock data.

## Start locally

1. Install Python 3.10 or newer.
2. In the repository folder run `python -m pip install -r requirements.txt`.
3. Run `streamlit run streamlit_app.py`.

## Deploy on Streamlit Community Cloud

1. Create or open the GitHub repository `VERDIQ_V2`.
2. Upload **all** the files and directories from this package to the repository root (do not upload the containing `VERDIQ_V2` folder as an additional level).
3. In Streamlit Community Cloud, select the repository, branch and entrypoint `streamlit_app.py`.
4. Deploy. No secrets, database or external assets are needed for the UI prototype.

## UI structure

- **Page 1 — Project Setup & GYF Input**: Sidebar project identity, municipality and version, model/source, target and area. DXF or manual-entry choice. DXF uploader is a mock control; it accepts a file but does not inspect or render it. Drawing, mapping, and quantities are illustrations.
- **Page 2 — Plan & Quantities**: Preview plan, sample factors, and geometric finding placeholder.
- **Page 3 — GYF Assessment**: Sample scorecards and balancing.
- **Page 4 — Design Improvements**: Illustrative intervention cards and overlay.
- **Page 5 — Compare Designs**: Sample side-by-side plan comparison.
- **Page 6 — Reports & Export**: Preview report structure and disabled export buttons.

Use the top navigation to switch pages. Inputs update the current Streamlit browser session only and are not saved to files or a database.

## Implementation boundaries

The repository imports **no original Verdiq Studio modules**, and requires only Streamlit. No backend integrations should be added until the interface has been reviewed and approved.

## Files

- `streamlit_app.py` — entrypoint, dispatch, page configuration
- `app/layout.py` — global header, navigation, dynamic example rulebook metadata and sidebar
- `app/pages.py` — six visual-only pages
- `app/visuals.py` — vector demonstration plan and shared display helpers
- `assets/styles.css` — page styling
- `requirements.txt` — dependency

## Future integration sequence

1. Attach official rulebook YAML data and validate versions/sources.
2. Add manual calculation inputs and common calculation engine.
3. Connect DXF geometry, layer mapping, and validation.
4. Connect assessment, advice, scenario comparisons, and reporting.
5. Introduce Swedish localization after English UX is approved.
