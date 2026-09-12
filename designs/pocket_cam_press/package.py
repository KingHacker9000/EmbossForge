"""Render the actual print STLs, write BOM, and create the deliverable ZIP."""
from pathlib import Path
import json,csv,shutil,zipfile,hashlib
import vtk
from PIL import Image,ImageDraw,ImageFont

OUT=Path('build/pocket_cam_press');SRC=Path(__file__).parent
NAMES=['frame','carrier','cam_lever','axle','axle_clip']
COLORS=[(.25,.36,.48),(.93,.62,.19),(.24,.67,.60),(.75,.78,.81),(.85,.30,.20)]

def main():
    g=json.loads((OUT/'validation'/'geometry.json').read_text())
    v=json.loads((OUT/'validation'/'exported_mesh_checks.json').read_text())
    assert v['mesh_checks_pass'] and v['assembly_paths_pass'], 'Validation failed'
    for p in g['parts']:
        assert all(p[k] for k in ('valid_brep','watertight','winding_consistent','fits_220'))
        assert p['solids']==p['mesh_bodies']==1
    for c in g['collisions']:
        assert (c['a'],c['b']) in [('frame','lower_die_ENVELOPE'),('carrier','upper_die_ENVELOPE')]
        assert abs(c['overlap_mm3']-6.6)<.01
    assert max(g['closed_dimensions_xyz_mm'])<130 and g['solid_upper_mass_total_g']<150
    (OUT/'source').mkdir(exist_ok=True)
    for p in SRC.glob('*.py'):shutil.copy2(p,OUT/'source'/p.name)
    for n in ('README.md','ENGINEERING.md','requirements.txt'):shutil.copy2(SRC/n,OUT/n)
    with (OUT/'BOM.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['part','quantity','estimated_PLA_g','solid_upper_PLA_g','file'])
        for n in NAMES:
            m=next(r for r in v['mass'] if r['part']==n)
            w.writerow([n,1,m['estimated_g'],m['solid_upper_g'],f'stl/{n}.stl'])
        w.writerow(['PRESS TOTAL',5,v['total_estimate_g'],g['solid_upper_mass_total_g'],'dies/supports excluded'])
        w.writerow(['External hardware required',0,0,0,'NONE'])
    board=Image.new('RGB',(1500,1000),'#f5f7fa');draw=ImageDraw.Draw(board)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    except OSError:font=ImageFont.load_default()
    for i,(name,color) in enumerate(zip(NAMES,COLORS)):
        rd=vtk.vtkSTLReader();rd.SetFileName(str(OUT/'stl'/f'{name}.stl'));rd.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(rd.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*color)
        ren=vtk.vtkRenderer();ren.SetBackground(.96,.97,.99);ren.AddActor(actor)
        b=rd.GetOutput().GetBounds();cx=(b[0]+b[1])/2;cy=(b[2]+b[3])/2;cz=(b[4]+b[5])/2
        cam=ren.GetActiveCamera();cam.SetPosition(cx+100,cy-150,cz+100);cam.SetFocalPoint(cx,cy,cz);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();ren.ResetCamera();cam.Zoom(.9)
        win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(500,425);win.AddRenderer(ren);win.Render()
        fl=vtk.vtkWindowToImageFilter();fl.SetInput(win);fl.Update()
        wr=vtk.vtkPNGWriter();path=OUT/'views'/f'print_{name}.png';wr.SetFileName(str(path));wr.SetInputConnection(fl.GetOutputPort());wr.Write();win.Finalize()
        x=(i%3)*500;y=(i//3)*500
        board.paste(Image.open(path).convert('RGB'),(x,y))
        dims=next(p['dimensions_mm'] for p in g['parts'] if p['part']==name)
        draw.text((x+15,y+428),f'{name} — print 1',font=font,fill='#17283a')
        draw.text((x+15,y+458),' x '.join(f'{d:.1f}' for d in dims)+' mm',font=font,fill='#17283a')
    draw.text((1020,555),'Pocket Cam 42\nActual exported print meshes\n5 pieces • 0 external hardware\nFrame requires supports\nPLA / 0.4mm nozzle',font=font,fill='#17283a',spacing=14)
    board.save(OUT/'views'/'print_orientations.png')
    (OUT/'validation'/'package_checks.json').write_text(json.dumps(dict(
        all_checks_pass=True,mesh_pair_and_paper_checks=len(v['mesh_checks']),
        assembly_path_samples=len(v['assembly_path_checks']),printed_parts=5,
        external_hardware=0,physical_validation=False),indent=2))
    manifest={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256.json'}
    (OUT/'SHA256.json').write_text(json.dumps(manifest,indent=2))
    destination=OUT.parent/'Pocket-Cam-42-Prototype.zip'
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
        for p in OUT.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,Path('Pocket-Cam-42')/p.relative_to(OUT))
    with zipfile.ZipFile(destination) as z:assert z.testzip() is None
    print(json.dumps(dict(package=str(destination.resolve()),estimated_mass=v['total_estimate_g'],
                         solid_upper_mass=g['solid_upper_mass_total_g'],files=len(manifest)),indent=2))

if __name__=='__main__':main()
