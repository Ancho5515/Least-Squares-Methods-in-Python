"""Local-only notebook verification, execution and Chinese book generation."""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import nbformat

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from tools.run_notebook import source_hash, output_hash, dependency_hash


def load_manifest(root=ROOT):
    root=Path(root).resolve()
    manifest=json.loads((root/'book.json').read_text(encoding='utf-8'))
    chapters=manifest['chapters']
    if not chapters or len(chapters)!=len(set(chapters)):
        raise ValueError('empty or duplicate notebook manifest')
    for name in chapters:
        path=(root/name).resolve()
        if not path.is_relative_to(root/'notebooks') or not path.is_file():
            raise ValueError(f'invalid notebook path: {name}')
    return manifest


def validate_notebook(nb):
    nbformat.validate(nb)
    if nb.metadata.get('execution',{}).get('source_sha256')!=source_hash(nb):
        raise ValueError('notebook source changed or has never been executed')
    if nb.metadata.execution.get('output_sha256')!=output_hash(nb):
        raise ValueError('saved outputs changed; execute notebook again')
    if nb.metadata.execution.get('dependency_sha256')!=dependency_hash():
        raise ValueError('shared solver/data/execution inputs changed; execute notebook again')
    for cell in nb.cells:
        if cell.cell_type=='code':
            if cell.execution_count is None:
                raise ValueError('unexecuted code cell')
            if any(o.output_type=='error' for o in cell.outputs):
                raise ValueError('saved execution error')


def verify_references(root=ROOT):
    base=Path(root)/'references/nonlinear-least-squares'
    manifest=json.loads((base/'SHA256SUMS.json').read_text(encoding='utf-8'))
    for name,expected in manifest.items():
        p=(base/name).resolve()
        if not p.is_relative_to(base.resolve()):
            raise ValueError('unsafe archive manifest path')
        actual=hashlib.sha256(p.read_bytes()).hexdigest()
        if actual!=expected:
            raise ValueError(f'reference checksum mismatch: {name}')
    return len(manifest)


def _crosslinks(text):
    text=re.sub(r'第([0-9]{2})章',r'[第\1章](#ch-\1)',text)
    return re.sub(r'附录([A-D])(?![：:])',r'[附录\1](#ch-\1)',text)


def notebook_markdown(nb,slug,output_dir,skip_setup=True):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',slug):
        raise ValueError('unsafe notebook slug')
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    parts=[]
    for ci,cell in enumerate(nb.cells):
        if cell.cell_type=='markdown':
            parts.append(_crosslinks(cell.source))
        elif cell.cell_type=='code':
            if skip_setup and 'setup' in cell.metadata.get('tags',[]):
                continue
            parts.append('~~~~python\n'+cell.source+'\n~~~~')
            for oi,output in enumerate(cell.outputs):
                if output.output_type=='error':
                    raise ValueError('cannot export an error output')
                data=output.get('data',{})
                if 'image/png' in data:
                    name=f'{slug}-{ci}-{oi}.png'
                    raw=base64.b64decode(data['image/png'],validate=True)
                    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
                        raise ValueError('invalid PNG output')
                    path=output_dir/name;path.write_bytes(raw)
                    caption=cell.metadata.get('figure_caption','实验结果')
                    parts.append(f'![{caption}]({path.as_posix()}){{width=88%}}')
                else:
                    value=output.get('text',data.get('text/plain',''))
                    if value:
                        if isinstance(value,list):
                            value=''.join(value)
                        value=re.sub(r'\x1b\[[0-9;]*m','',value).strip()
                        parts.append('~~~~text\n'+value+'\n~~~~')
    return '\n\n'.join(parts)+'\n'


def build_pdf(manifest):
    for binary in ('pandoc','xelatex','latexmk'):
        if not shutil.which(binary):
            raise RuntimeError(f'{binary} is required; see README installation instructions')
    work=ROOT/'.build/book';work.mkdir(parents=True,exist_ok=True)
    fragments=[]
    for name in manifest['chapters']:
        p=ROOT/name;nb=nbformat.read(p,as_version=4);validate_notebook(nb)
        text=notebook_markdown(nb,p.stem,work/'figures',skip_setup=True)
        identifier=p.stem.split('-')[0]
        lines=text.splitlines()
        title=lines[0][2:]
        if identifier in 'ABCD' and len(identifier)==1:
            title=re.sub(r'^附录[A-D]：','',title)
        attrs=f'{{#ch-{identifier}'+(' .unnumbered' if identifier=='00' else '')+'}'
        lines[0]='# '+title+' '+attrs
        if identifier=='A':
            fragments.append('\\appendix\n')
        fragments.append('\n'.join(lines))
    markdown=work/'book.md';markdown.write_text('\n\n'.join(fragments),encoding='utf-8')
    command=['pandoc',str(markdown),'-o',str(work/'book.tex'),'--standalone',
             '--template',str(ROOT/'tools/book-template.tex'),'--top-level-division=chapter',
             '--number-sections','--toc','--listings','--from=markdown+raw_tex',
             '-V','title='+manifest['title'],'-V','subtitle='+manifest['subtitle']]
    subprocess.run(command,check=True,cwd=ROOT)
    env=os.environ.copy();env.setdefault('SOURCE_DATE_EPOCH','1793635200')
    proc=subprocess.run(['latexmk','-xelatex','-interaction=nonstopmode','-halt-on-error',
                         'book.tex'],cwd=work,env=env,stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,text=True)
    (work/'compile-output.txt').write_text(proc.stdout,encoding='utf-8')
    if proc.returncode:
        raise RuntimeError('PDF build failed; see .build/book/compile-output.txt\n'+proc.stdout[-4500:])
    from pypdf import PdfReader
    reader=PdfReader(work/'book.pdf')
    if len(reader.pages)<20 or not reader.outline:
        raise RuntimeError('book is unexpectedly short or lacks bookmarks')
    destination=ROOT/'pdf/Least-Squares-Methods-in-Python-zh.pdf'
    destination.parent.mkdir(exist_ok=True)
    shutil.copyfile(work/'book.pdf',destination)
    print(f'PDF: {len(reader.pages)} pages -> {destination.relative_to(ROOT)}',flush=True)
    return destination,len(reader.pages)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',help='execute each chapter in a fresh IPython process')
    parser.add_argument('--pdf',action='store_true',help='compile the saved notebook results to Chinese PDF')
    parser.add_argument('--test',action='store_true',help='run the unittest suite before delivery')
    args=parser.parse_args()
    manifest=load_manifest()
    archived=verify_references()
    if args.execute:
        for name in manifest['chapters']:
            subprocess.run([sys.executable,str(ROOT/'tools/run_notebook.py'),str(ROOT/name)],
                           cwd=ROOT,check=True,timeout=180)
    records=[]
    for name in manifest['chapters']:
        nb=nbformat.read(ROOT/name,as_version=4);validate_notebook(nb)
        records.append({'file':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),
                        'code_cells':sum(c.cell_type=='code' for c in nb.cells),
                        'figures':sum('image/png' in o.get('data',{})
                                      for c in nb.cells for o in c.get('outputs',[])),
                        'engine':nb.metadata.execution.get('engine','unknown')})
    tested=False
    if args.test:
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],
                       cwd=ROOT,check=True)
        tested=True
    pdf_record=None
    if args.pdf:
        path,pages=build_pdf(manifest)
        pdf_record={'file':str(path.relative_to(ROOT)),'pages':pages,
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    record={'version':'0.1','notebooks':records,'reference_files_verified':archived,
            'test_suite_ran_in_this_build':tested,'pdf':pdf_record,
            'versions':{p:importlib.metadata.version(p) for p in
                        ['numpy','scipy','matplotlib','nbformat','ipython','pypdf']},
            'execution_note':'Separate socket-free IPython processes. Jupyter kernel protocol not exercised in restricted host.',
            'limits':['Synthetic engineering data only.','Full hybrid/secant and sparse solvers not implemented in v0.1.']}
    if args.pdf:
        (ROOT/'docs/validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Checked {len(records)} notebooks, {sum(x["code_cells"] for x in records)} code cells, '
          f'{sum(x["figures"] for x in records)} figures, {archived} archived files.',flush=True)


if __name__=='__main__':
    main()
