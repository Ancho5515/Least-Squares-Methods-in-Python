import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import nbformat

RUNNER = Path(__file__).resolve().parents[1]/'tools/run_notebook.py'


class ExecutionTests(unittest.TestCase):
    def run_notebook(self, source):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.ipynb'
            nbformat.write(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(source)]),p)
            proc=subprocess.run([sys.executable,str(RUNNER),str(p)],capture_output=True,text=True)
            return proc,nbformat.read(p,as_version=4)

    def test_real_stdout_and_figure_are_captured(self):
        proc,nb=self.run_notebook("print(2+3)\nimport matplotlib.pyplot as plt\nplt.plot([1,2]);plt.show()")
        self.assertEqual(proc.returncode,0,proc.stderr)
        outputs=nb.cells[0].outputs
        self.assertIn('5', ''.join(o.get('text','') for o in outputs))
        self.assertTrue(any('image/png' in o.get('data',{}) for o in outputs))

    def test_error_stops_and_does_not_save_partial_result(self):
        proc,nb=self.run_notebook("print('before')\nraise ValueError('expected failure')")
        self.assertNotEqual(proc.returncode,0)
        self.assertIn('expected failure',proc.stderr)
        self.assertEqual(nb.cells[0].outputs,[])

    def test_processes_do_not_share_namespace(self):
        first,_=self.run_notebook('sentinel=123')
        second,_=self.run_notebook("assert 'sentinel' not in globals()")
        self.assertEqual(first.returncode,0,first.stderr)
        self.assertEqual(second.returncode,0,second.stderr)


if __name__=='__main__':unittest.main()
