# VERDIQ_V2 — Municipal GYF Intelligence Foundation (Increment 2A)

This **incremental** package builds upon the deployed DXF Viewer Increment 1 and retains the previously approved Streamlit UI, manual proforma and styling.

## New capabilities
- Structured, version-pinned YAML rulebooks for Stockholm 2021/2015, Nacka 2019 and SGBC 2026.
- Schema validation with SHA fingerprints and declared source status.
- CAD layer-to-factor suggestions and manual correction in the **Layer mapping** tab.
- DXF-derived **provisional** factor quantities, with a geometry evidence table.
- Explicit handling of unknown `$INSUNITS`: blocked until units are selected.
- Basic flags for unmapped CAD layers, duplicate symbol coordinates, missing plot boundary and unverified balancing.
- Legacy geometry extraction and calculator retained as reusable modules. No automatic compliance scoring is enabled.

## Important limitations
- The old rulebook's `meta.status: verified` means its YAML *claims* verification; no independent verification against official city templates has been performed in this increment.
- Geometry extraction still uses legacy semantics; **not yet validated** for nested blocks, severe topology defects or all HATCH variants. The viewer and extractor may support different entity classes.
- Tree symbols can be ambiguous; repeated symbols and overlapping features must be reviewed manually.
- Line-length measurements are not ready; factors measured in length are blocked from extracting accidental polygon area.
- Stockholm 2021 balancing is marked *unverified* in the bundled rulebook.
- No rulebook for Täby exists in the old code archive. Täby is not silently substituted with another scheme.
- **Manual proforma currently remains separate** from extracted provisional quantities pending reconciliation, user confirmation and validation.
- SpecialGYF is handled by the existing manual workflow; no numerical compliance calculation for SpecialGYF is attempted.
- Unmapped geometry, eligibility conditions, and site constraints require expert review.

## Repository installation
Upload all files under the ZIP root (keep `.streamlit/config.toml` intact). If your repo already has the DXF Viewer Increment 1, only **`pages.py`, `requirements.txt`, `gyf_engine_v2.py`, the five `verdiq_*.py` engine files, and four YAML files in `rulebooks/`** are new or changed. The rest are identical.

## Test
`python -m unittest discover -s tests -v`

A full live Streamlit browser interaction test has not been run. Existing styling is retained.

## Next increments
Complete topology validation and object-level lineage; unify the DXF and manual quantity records; verify each municipal workbook, formulas, balancing and SpecialGYF pathways before enabling compliance scores.
