"""Execute one ordinary Python notebook in a fresh, socket-free IPython process.

Invoked as a subprocess by build.py: each chapter has an isolated namespace.
Rich display uses IPython's real display publisher, including inline figures.
This intentionally supports synchronous Python cells, not kernel widgets/input().
"""
from pathlib import Path
import hashlib
import json
import os
import platform
import sys
import nbformat
import matplotlib
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from matplotlib_inline.backend_inline import configure_inline_support

ROOT = Path(__file__).resolve().parents[1]


def source_hash(nb):
    sources = [(c.cell_type, c.source) for c in nb.cells]
    return hashlib.sha256(json.dumps(sources,ensure_ascii=False).encode()).hexdigest()


def output_hash(nb):
    values=[(c.execution_count,c.outputs) for c in nb.cells if c.cell_type=='code']
    return hashlib.sha256(json.dumps(values,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def dependency_hash(root=ROOT):
    root=Path(root)
    paths=sorted((root/'lsq').glob('*.py'))+sorted((root/'data').glob('*.csv'))
    paths += [root/'requirements.txt',root/'tools/run_notebook.py']
    values={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def execute(path):
    path = Path(path).resolve()
    nb = nbformat.read(path, as_version=4)
    matplotlib.use('module://matplotlib_inline.backend_inline')
    shell = InteractiveShell.instance()
    configure_inline_support(shell, 'inline')
    os.chdir(ROOT)
    count = 0
    for cell in nb.cells:
        if cell.cell_type != 'code':
            continue
        count += 1
        with capture_output(stdout=True, stderr=True, display=True) as captured:
            result = shell.run_cell(cell.source, store_history=False)
            # Flush figures created without an explicit show(), as Jupyter does.
            from matplotlib_inline.backend_inline import flush_figures
            flush_figures()
        error = result.error_before_exec or result.error_in_exec
        if error is not None:
            raise RuntimeError(f'{path.name} code cell {count}: {error}') from error
        outputs = []
        if captured.stdout:
            outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
        if captured.stderr:
            outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
        for item in captured.outputs:
            outputs.append(nbformat.v4.new_output('display_data',data=item.data,
                                                  metadata=item.metadata))
        cell.execution_count = count
        cell.outputs = outputs
    nb.metadata['execution'] = {'engine':'isolated-ipython-process',
                               'python':platform.python_version(),
                               'source_sha256':source_hash(nb),
                               'output_sha256':output_hash(nb),
                               'dependency_sha256':dependency_hash()}
    nbformat.validate(nb)
    temporary = path.with_suffix('.ipynb.tmp')
    nbformat.write(nb, temporary)
    temporary.replace(path)
    print(f'{path.name}: {count} cells executed')


if __name__ == '__main__':
    execute(sys.argv[1])
