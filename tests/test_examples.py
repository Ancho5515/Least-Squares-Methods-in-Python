"""Exercise the actual PWM function stored in the authoritative notebook."""
import ast
from pathlib import Path
import unittest
import nbformat
import numpy as np


def calibration_function():
    path=Path(__file__).resolve().parents[1]/'notebooks/15-pwm-xyz.ipynb'
    for cell in nbformat.read(path,as_version=4).cells:
        if cell.cell_type!='code':
            continue
        for node in ast.parse(cell.source).body:
            if isinstance(node,ast.FunctionDef) and node.name=='calibrate':
                ns={'np':np,
                    'simulator':lambda p:(np.asarray(p,dtype=float)-96)/3999,
                    'measure':lambda p:(np.asarray(p,dtype=float)-96)/3999,
                    'measured_jacobian':lambda p:np.eye(3)/3999}
                exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
                return ns['calibrate']
    raise AssertionError('calibrate not found')


class PWMTests(unittest.TestCase):
    def test_final_attempt_success_is_reported(self):
        solve=calibration_function()
        p,status,_=solve(np.zeros(3),np.full(3,196.),max_iter=1)
        self.assertEqual(status,'target_reached')
        self.assertTrue(np.all(p==96))

    def test_tolerance_applies_below_reachable_box(self):
        _,status,_=calibration_function()(np.array([-1e-8,0,0]),np.full(3,96.))
        self.assertEqual(status,'target_reached')

    def test_invalid_inputs_fail_before_measurement(self):
        solve=calibration_function()
        for target,start,kw in [
            ([np.nan,0,0],[96,96,96],{}),
            ([0,0],[96,96,96],{}),
            ([0,0,0],[np.nan,96,96],{}),
            ([0,0,0],[96,96,96],{'max_iter':0}),
            ([0,0,0],[96,96,96],{'tolerance':np.inf}),
        ]:
            with self.subTest(target=target,start=start,kw=kw):
                with self.assertRaises(ValueError):solve(target,start,**kw)


if __name__=='__main__':unittest.main()
