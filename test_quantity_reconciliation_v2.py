import pytest
from quantity_reconciliation_v2 import (
    reconcile, can_confirm, confirmed_snapshot, quantity_context,
)

FACTORS = [
    {"id": "A", "label": {"en": "Planting"}, "measure": "area", "section": "green"},
    {"id": "B", "label": {"en": "Trees"}, "measure": "count", "section": "trees"},
]


def test_manual_and_dxf_conflict_blocks_confirmation():
    rows = reconcile(FACTORS, {"A": 80}, {"A": 100})
    assert rows[0].source == "Unresolved"
    assert rows[0].final is None
    assert not can_confirm(rows)[0]


def test_explicit_dxf_choice_does_not_add_manual():
    rows = reconcile(FACTORS, {"A": 80}, {"A": 100}, choices={"A": "DXF"})
    assert rows[0].final == 100
    assert can_confirm(rows)[0]


def test_manual_choice_and_override():
    rows = reconcile(FACTORS, {"A": 80}, {"A": 100}, choices={"A": "Manual"})
    assert rows[0].final == 80
    rows = reconcile(FACTORS, {"A": 80}, {"A": 100},
                     choices={"A": "Override"}, overrides={"A": 65})
    assert rows[0].final == 65


def test_dxf_missing_blocks_confirmation():
    rows = reconcile(FACTORS, {"A": 0}, {"A": 0}, choices={"A": "DXF"})
    assert rows[0].status == "DXF_QUANTITY_MISSING"
    assert not can_confirm(rows)[0]


def test_count_fraction_rejected():
    with pytest.raises(ValueError):
        reconcile(FACTORS, {"B": 1.5}, {})


def test_nonfinite_rejected():
    for invalid in (float('nan'), float('inf'), -1):
        with pytest.raises(ValueError):
            reconcile(FACTORS, {"A": invalid}, {})


def test_context_changes_with_mapping_drawing_rulebook_and_units():
    base = quantity_context('Stockholm', '2021-02-01', 'drawing1', 'rule1', {'L': 'A'}, 1.0)
    assert base != quantity_context('Stockholm', '2021-02-01', 'drawing1', 'rule1', {'L': 'B'}, 1.0)
    assert base != quantity_context('Stockholm', '2021-02-01', 'drawing2', 'rule1', {'L': 'A'}, 1.0)
    assert base != quantity_context('Stockholm', '2021-02-01', 'drawing1', 'rule2', {'L': 'A'}, 1.0)
    assert base != quantity_context('Stockholm', '2021-02-01', 'drawing1', 'rule1', {'L': 'A'}, .001)


def test_confirmation_captures_single_source_and_evidence():
    rows = reconcile(FACTORS, {'A': 80}, {'A': 100}, choices={'A': 'DXF'})
    snapshot = confirmed_snapshot(rows, context='123')
    assert snapshot['quantities']['A'] == 100
    assert snapshot['evidence'][0]['manual'] == 80
    assert snapshot['evidence'][0]['source'] == 'DXF'
    assert snapshot['status'] == 'USER_CONFIRMED_QUANTITIES_UNVERIFIED_ELIGIBILITY'


def test_blocking_dxf_error_prevents_confirmation():
    rows = reconcile(FACTORS, {}, {'A': 10}, choices={'A': 'DXF'})
    assert not can_confirm(rows, blocking_findings=True)[0]
