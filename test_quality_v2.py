"""Regression tests for the non-destructive DXF quality screening."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import ezdxf
from gyf_engine_v2 import inspect_dxf


def drawing(*, overlap=False, open_contour=False, duplicate=False):
    doc = ezdxf.new('R2013')
    doc.header['$INSUNITS'] = 6
    ms = doc.modelspace()
    ms.add_lwpolyline([(0,0),(20,0),(20,20),(0,20)], close=True, dxfattribs={'layer':'VERDIQ_PLOT'})
    ms.add_lwpolyline([(1,1),(8,1),(8,8),(1,8)], close=True, dxfattribs={'layer':'bed_unbuilt'})
    if overlap:
        ms.add_lwpolyline([(6,6),(12,6),(12,12),(6,12)], close=True, dxfattribs={'layer':'bed_other'})
    if open_contour:
        ms.add_lwpolyline([(3,3),(4,3),(4,4)], close=False, dxfattribs={'layer':'bed_unbuilt'})
    if duplicate:
        for _ in range(2):
            ms.add_point((5,5),dxfattribs={'layer':'trees'})
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / 'fixture.dxf'
        doc.saveas(file)
        return file.read_bytes()

class QualityTests(unittest.TestCase):
    def test_open_contour_preserved_and_flagged(self):
        x = inspect_dxf(drawing(open_contour=True),'Stockholm','2021-02-01', mapping={'bed_unbuilt':'bed_unbuilt'})
        self.assertAlmostEqual(x.quantities['bed_unbuilt'],49)
        self.assertTrue(any(f.code=='OPEN_CONTOUR' for f in x.findings))
        self.assertTrue(any(r['measurement_status']=='Open contour' for r in x.object_evidence))
    def test_spatial_overlap_detected(self):
        from gyf_engine_v2 import load_selected
        rb,_ = load_selected('Stockholm','2021-02-01')
        # Two ground partition factor ids from the selected rulebook, when available.
        ids = [fid for fid in (rb.spatial.ground_partition if rb.spatial else []) if fid in {f.id for f in rb.factors}]
        if len(ids)<2:self.skipTest('No two ground partition factors in this rulebook')
        x=inspect_dxf(drawing(overlap=True),'Stockholm','2021-02-01',mapping={'bed_unbuilt':ids[0],'bed_other':ids[1]})
        self.assertTrue(any(f.code=='GROUND_OVERLAP' for f in x.findings))
    def test_repeated_symbols_flagged(self):
        from gyf_engine_v2 import load_selected
        rb,_=load_selected('Stockholm','2021-02-01')
        fid=next(f.id for f in rb.factors if f.measure=='count')
        x=inspect_dxf(drawing(duplicate=True),'Stockholm','2021-02-01',mapping={'trees':fid})
        self.assertTrue(any(f.code=='POSSIBLE_DUPLICATE_SYMBOL' for f in x.findings))
        self.assertEqual(len([r for r in x.object_evidence if r['factor_id']==fid]),2)
        # Unreviewed possible duplicates are not silently removed.
        self.assertEqual(x.quantities[fid],2)

if __name__=='__main__':unittest.main()
