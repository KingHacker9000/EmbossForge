"""Assemble a portable, checksummed release; reject failed geometry reports."""
import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
import model

out=model.OUT
src=Path(__file__).resolve().parent
g=json.loads((out/'validation/geometry_review.json').read_text())
assert not g['interferences']
assert len(g['stl'])==16
assert all(r['watertight'] and r['winding'] and r['components']==1 and r['fits_220'] and r['on_bed'] for r in g['stl'])
s=json.loads((out/'validation/assembly_service_checks.json').read_text())
assert all(not v for k,v in s.items() if k.endswith('interferences'))
assert s['actual_die_pair_overlap_at_0_mm3']==0
for name in ['MANUAL.md','RESEARCH.md','ENGINEERING.md','VALIDATION.md']:
    shutil.copy2(src/name,out/name)
(out/'source').mkdir(exist_ok=True)
for p in src.iterdir():
    if p.suffix in ['.py','.svg'] and p.name!='package_release.py':shutil.copy2(p,out/'source'/p.name)
shutil.copy2(model.ROOT/'LICENSE',out/'LICENSE')
(out/'source'/'requirements.txt').write_text('cadquery==2.8.0\ntrimesh==5.1.0\nmanifold3d==3.5.3\nnumpy>=1.26\nPillow>=10\nvtk>=9.3\n')
(out/'START_HERE.md').write_text('''# Original all-PLA screw embosser

External hardware required: **0**. This is a CAD-reviewed first physical prototype.

1. Read **MANUAL.md** for slicing, quantities, assembly, alignment and commissioning.
2. Print the small **fit_trials/** before committing to the complete machine.
3. Production parts are in **stl/**. Print the two working dies from
   **test_dies/diamond_commissioning/**. Assembly STLs are VIEW ONLY.
4. Named open/closed/exploded assemblies are in **assemblies/** as STEP files.
5. Research, calculations and limitations are in the other Markdown reports.

The package includes 24 mechanism pieces, two dies, and one alignment tool.
About 1.32 kg solid PLA before dies, fit trials, support and brims; budget around
1.5 kg for a first article. There is no verified print-time or physical force rating.

## Editable source

Use Python 3.11 and install `source/requirements.txt` in a virtual environment.
From this package root, `python source/model.py` regenerates the press here;
`python source/review.py`, `python source/assembly_checks.py` and
`python source/inspect_stl.py` recreate checks and images. `engineering.py`
recalculates the screening estimates. The commissioning SVG and generated SCAD
are editable too. `test_dies.py` additionally requires the EmbossForge repository's
shared backend installed in the environment; it never duplicates die rules.

Read VALIDATION.md for the native Windows shutdown-exit caveat and unperformed
physical tests. No prior EmbossForge press geometry is used in the new model.
''')
# Portable SCAD asset references, without changing any geometry.
valid_die=out/'test_dies'/'diamond_commissioning'
for p in valid_die.glob('*.scad'):
    text=p.read_text()
    art=valid_die/'diamond_commissioning_normalized.svg'
    text=text.replace(art.resolve().as_posix(),art.name)
    p.write_text(text)
rows=json.loads((out/'bom.json').read_text())['parts']
complete=[dict(part=r['part'],quantity=r['quantity'],file=f"stl/{r['part']}.stl") for r in rows]
for kind in ['male','female']:
    complete.append(dict(part=f'diamond_commissioning_{kind}',quantity=1,
        file=f'test_dies/diamond_commissioning/diamond_commissioning_{kind}.stl'))
with (out/'COMPLETE_BOM.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['part','quantity','file']);w.writeheader();w.writerows(complete)
files=[]
for p in out.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(out)
    if any(x in rel.parts for x in ['research','__pycache__','commissioning_pair']):continue
    if p.name=='SHA256SUMS.txt':continue
    files.append(p)
hashes='\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(out).as_posix() for p in sorted(files))+'\n'
(out/'SHA256SUMS.txt').write_text(hashes)
files.append(out/'SHA256SUMS.txt')
zip_path=out.parent/'All-PLA-42mm-Embosser-RevA.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(files):z.write(p,p.relative_to(out))
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    assert not any('commissioning_pair/' in n or 'research/' in n for n in z.namelist())
print(f'PACKAGE: {zip_path}\nFILES: {len(files)}\nBYTES: {zip_path.stat().st_size}\nPRINT PIECES: {sum(r["quantity"] for r in complete)}',flush=True)
