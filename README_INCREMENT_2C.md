# VERDIQ_V2 — Increment 2C: Unified Quantity Reconciliation

## GitHub upload (three files only)

1. **Replace** root `pages.py`.
2. **Add** root `quantity_reconciliation_v2.py`.
3. **Add** root `test_quantity_reconciliation_v2.py` (optional at runtime, recommended for regression testing).

Do not replace `dxf_viewer.py`, `styles.css`, `manual_proforma.py`, `gyf_engine_v2.py`, or the YAML rulebooks. This increment expects the previously deployed Increment 2B modules and the path fix to already be in the repository.

## User workflow

- **Manual entry**: Project Setup → Manual GYF Calculation → enter factor quantities; use the Continue button to open **Plan & Quantities**.
- **DXF entry**: Project Setup → upload DXF → Layer Mapping → choose units and map layers → Extract provisional GYF quantities → open **Plan & Quantities**.
- **Combined entry**: Enter manual quantities and extract the DXF in the same Streamlit session. The workbench displays both inputs. For factors with values from both sources, explicitly choose **DXF**, **Manual**, **Override**, or **Exclude**. Inputs are not added implicitly.
- **Confirmation**: Confirm reviewed factor quantities. Changes to factor choices or values invalidate the confirmation. Confirming is **not** municipal eligibility approval or GYF assessment.

## Design safeguards

- Context fingerprint includes municipality, version, rulebook hash, drawing hash, layer mappings, and units.
- Changing the municipality/version discards the previous ledger selection from the active view.
- The last matching extraction snapshot remains available when Streamlit unmounts the DXF upload widget during page navigation.
- If extraction has error-level findings, confirmation of DXF-based quantities is blocked. The user can select Manual or Override instead.
- Invalid or fractional count quantities are rejected.
- No arithmetic sum of overlapping manual and DXF inputs.
- No calculated GYF scores or claims of verified municipal compliance.
- Session-only state: NO durable storage, downloadable report, or audit export yet.

## Verification

`pytest -q test_quantity_reconciliation_v2.py`

Nine focused reconciliation tests passed. A broader local run of the existing DXF/QA suites and these tests passed (17 total). Streamlit browser rendering is not yet tested in this environment.
