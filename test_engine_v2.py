import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ezdxf
from gyf_engine_v2 import load_selected,inspect_dxf,assess_readiness


def fixture(unit=6):
    doc=ezdxf.new('R2013')
    doc.header['$INSUNITS']=unit
    ms=doc.modelspace()
    ms.add_lwpolyline([(0,0),(20,0),(20,20),(0,20)],close=True,dxfattribs={'layer':'VERDIQ_PLOT'})
    ms.add_lwpolyline([(0,0),(10,0),(10,10),(0,10)],close=True,dxfattribs={'layer':'bed_unbuilt'})
    ms.add_lwpolyline([(5,5),(15,5),(15,15),(5,15)],close=True,dxfattribs={'layer':'bed_unbuilt'})
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'a.dxf';doc.saveas(p);return p.read_bytes()

class EngineTests(unittest.TestCase):
    def test_all_schema_rulebooks(self):
        for muni,version in [('Stockholm','2021-02-01'),('Stockholm','2015-06-17'),('Nacka','2019-10'),('SGBC Miljöbyggnad','2026')]:
            rb,sha=load_selected(muni,version)
            self.assertTrue(rb.factors)
            self.assertEqual(len(sha),12)

    def test_unknown_municipality_blocked(self):
        with self.assertRaisesRegex(ValueError,'No executable municipal rulebook'):
            load_selected('Täby','2017-04-25')

    def test_unitless_block(self):
        x=inspect_dxf(fixture(0),'Stockholm','2021-02-01')
        self.assertEqual(assess_readiness(x),'BLOCKED')
        self.assertEqual(x.quantities,{})
        self.assertTrue(any(f.code=='UNCONFIRMED_UNITS' for f in x.findings))

    def test_explicit_scale_and_polygon_union(self):
        rb,_=load_selected('Stockholm','2021-02-01')
        fid=next(f.id for f in rb.factors if f.measure=='area')
        x=inspect_dxf(fixture(),'Stockholm','2021-02-01', mapping={'bed_unbuilt':fid})
        self.assertAlmostEqual(x.quantities[fid],175.,places=2)
        self.assertAlmostEqual(x.plot_area_m2,400.,places=2)
        self.assertEqual(assess_readiness(x),'REVIEW_REQUIRED')

    def test_manual_units_allow_unknown(self):
        rb,_=load_selected('Stockholm','2021-02-01')
        fid=next(f.id for f in rb.factors if f.measure=='area')
        x=inspect_dxf(fixture(0),'Stockholm','2021-02-01', units_to_m=1.,mapping={'bed_unbuilt':fid})
        self.assertAlmostEqual(x.quantities[fid],175.,places=2)

if __name__=='__main__':unittest.main()
