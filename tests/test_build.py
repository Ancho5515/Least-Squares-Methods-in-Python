import base64
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import nbformat
from tools.build import validate_notebook, notebook_markdown, verify_references, load_manifest
from tools.run_notebook import source_hash, output_hash, dependency_hash


class BuildTests(unittest.TestCase):
    def fixture(self):
        n=nbformat.v4.new_notebook(cells=[
            nbformat.v4.new_markdown_cell('# Title\n\nText and $x^2$.'),
            nbformat.v4.new_code_cell('print(1)',execution_count=1,
                outputs=[nbformat.v4.new_output('stream',name='stdout',text='1\n')])])
        n.metadata['execution']={'source_sha256':source_hash(n),
                                 'output_sha256':output_hash(n),
                                 'dependency_sha256':dependency_hash()}
        return n

    def test_rejects_stale_or_unexecuted_notebook(self):
        n=self.fixture();validate_notebook(n)
        n.cells[1].source='print(2)'
        with self.assertRaises(ValueError):validate_notebook(n)
        n=self.fixture();n.cells[1].execution_count=None
        with self.assertRaises(ValueError):validate_notebook(n)

    def test_rejects_saved_errors(self):
        n=self.fixture();n.cells[1].outputs=[nbformat.v4.new_output('error',ename='X',evalue='bad',traceback=[])]
        with self.assertRaises(ValueError):validate_notebook(n)

    def test_rejects_removed_or_altered_output(self):
        n=self.fixture();n.cells[1].outputs=[]
        with self.assertRaises(ValueError):validate_notebook(n)
        n=self.fixture();n.cells[1].outputs[0].text='incorrect output'
        with self.assertRaises(ValueError):validate_notebook(n)

    def test_rejects_changed_shared_execution_input(self):
        n=self.fixture()
        with patch('tools.build.dependency_hash',return_value='changed'):
            with self.assertRaises(ValueError):validate_notebook(n)

    def test_export_contains_code_actual_output_and_display_math(self):
        n=self.fixture()
        with tempfile.TemporaryDirectory() as d:
            text=notebook_markdown(n,'chapter',Path(d),skip_setup=True)
        self.assertIn('print(1)',text)
        self.assertIn('1\n',text)
        self.assertIn('$x^2$',text)
        self.assertIn('# Title',text)

    def test_setup_is_only_hidden_for_pdf(self):
        n=self.fixture();n.cells[1].metadata['tags']=['setup']
        with tempfile.TemporaryDirectory() as d:
            self.assertNotIn('print(1)',notebook_markdown(n,'chapter',Path(d),True))
            self.assertIn('print(1)',notebook_markdown(n,'chapter',Path(d),False))

    def test_safe_exported_image_names(self):
        from PIL import Image
        import io
        b=io.BytesIO();Image.new('RGB',(2,2),'white').save(b,format='PNG')
        n=self.fixture()
        n.cells[1].outputs.append(nbformat.v4.new_output('display_data',
            data={'image/png':base64.b64encode(b.getvalue()).decode()},metadata={}))
        with tempfile.TemporaryDirectory() as d:
            text=notebook_markdown(n,'chapter',Path(d),True)
            self.assertEqual(len(list(Path(d).glob('*.png'))),1)
            self.assertIn('.png',text)
            with self.assertRaises(ValueError):notebook_markdown(n,'../../bad',Path(d),True)

    def test_manifest_has_exactly_approved_order_and_no_workflows(self):
        root=Path(__file__).resolve().parents[1]
        chapters=load_manifest(root)['chapters']
        self.assertEqual(len(chapters),20)
        self.assertTrue(chapters[0].startswith('notebooks/00-'))
        self.assertTrue(chapters[-1].startswith('notebooks/D-'))
        self.assertFalse((root/'.github/workflows').exists())

    def test_archive_checksums(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(verify_references(root),45)


if __name__=='__main__':unittest.main()
