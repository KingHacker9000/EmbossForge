"""Original Pocket Cam 42 prototype. Dimensions in mm; no legacy press imports.
Run: .venv/Scripts/python designs/pocket_cam_press/model.py
CadQuery 2.8, trimesh, numpy. STLs are placed in their recommended print orientation.
"""
from pathlib import Path
import math, json, csv
import cadquery as cq
import numpy as np
import trimesh

OUT = Path('build/pocket_cam_press')
BASE = 9.0
DIE_D = 42.0
POCKET_D = 42.6
KEY_W = 6.3
AXIS_Z = 31.35
ECC = 2.0
CAM_R = 11.5
CLOSED_ANGLE = math.degrees(math.acos(.125))
PIN_R = 7.0
GUIDE_GAP = .30
LOCATOR_RADIAL_CLEARANCE = .20
DENSITY = .00124  # g/mm3

def box(x,y,z,at=(0,0,0)):
    return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(at)

def cyl(r,h,at=(0,0,0)):
    return cq.Workplane('XY').circle(r).extrude(h).translate(at)

def along_x(shape):
    return shape.rotate((0,0,0),(0,1,0),90)

def die_envelope():
    return cyl(21,3).union(box(6,3,3,(0,22,0)))

def holder(body, floor):
    """Cup + two hard radial datums + cantilever acting on the back of the key.
    A through slot isolates the clamp; nothing projects above the die base face.
    """
    body = body.union(cyl(24,3,(0,0,floor)))
    body = body.union(box(29,14,3,(0,25,floor)))
    cavity = cyl(POCKET_D/2,3.2,(0,0,floor))
    cavity = cavity.union(box(KEY_W,4,3.2,(0,22,floor)))
    body = body.cut(cavity)
    # Clearance around clamp. Cantilever attaches only at its left end.
    body = body.cut(box(18,7,floor+3.4,(-3,25.5,-.1)))
    beam = box(16,2.5,floor+3,(-4,25.35,0))
    nub = box(5,1.5,floor+3,(1.5,23.7,0))
    # Face of nub y=22.95: nominal tab at23.5 gives0.55 deflection;
    # after seating circle on the datums, approximately0.48mm remains.
    body = body.union(beam).union(nub)
    for angle in (225,315):
        a=math.radians(angle)
        boss=box(3,1.4,3,(0,21.75,floor)).rotate((0,0,0),(0,0,1),angle-90)
        body=body.union(boss)
    # Finger push-through access, outside the artwork-bearing central region.
    body=body.cut(cyl(3.2,floor+.1,(0,-16,-.05)))
    return body

def frame():
    f=cyl(27,BASE).union(box(71,45,BASE,(0,22.5,0)))
    f=holder(f,BASE)
    # Closing locators sit behind the paper edge, so broad sheets remain insertable.
    for x in (-18,18):
        f=f.union(cyl(4.5,3,(x,30,BASE)))
        f=f.union(cq.Workplane(obj=cq.Solid.makeCone(3,1,2,cq.Vector(x,30,12))))
    for s in (-1,1):
        # Broad rear columns and overhead cheeks; paper goes under the cheeks.
        f=f.union(box(9.7,20,35.5,(s*30.65,35,BASE)))
        f=f.union(box(9.7,73,19.5,(s*30.65,8.5,25)))
        # Local vertical guides engage the carrier without closing the paper throat.
        for yy,ll in ((-22,8),(26,16)):
            f=f.union(box(3.0,ll,10,(s*27.3,yy,15)))
        # Rear keys guide Y without obstructing the squeezing handle at the front.
        f=f.union(box(3.3,3,10,(s*24.15,21.5,15)))
    # D seat prevents axle rotation; its flat is on +Y, away from bearing loads.
    bore=cq.Workplane('YZ').circle(7.25).extrude(90,both=True)
    bore=bore.cut(box(190,30,40,(0,20.75,-20))).translate((0,0,AXIS_Z))
    return f.cut(bore)

def carrier():
    c=holder(box(51,60,5,(0,4,0)).union(box(16,4,2,(0,-28,0))),5)
    for s in (-1,1): c=c.cut(box(4,3.6,9,(s*24.2,21.5,-.1)))
    for x in (-18,18):
        c=c.union(cyl(4.5,3,(x,30,5)))
        # At0.1mm paper gap: 0.20mm radial clearance on the 45-degree locators.
        c=c.cut(cq.Workplane(obj=cq.Solid.makeCone(.9+LOCATOR_RADIAL_CLEARANCE,
                        2.9+LOCATOR_RADIAL_CLEARANCE,2,cq.Vector(x,30,6))))
    return c

def cam():
    # Twin broad lobes put reactions near the cheeks. A lighter central spool
    # and 45-degree transitions avoid a large unsupported flange while printing.
    c=along_x(cyl(CAM_R,9,(0,0,-25))).translate((0,0,-ECC))
    c=c.union(along_x(cyl(CAM_R,9,(0,0,16))).translate((0,0,-ECC)))
    c=c.union(along_x(cyl(9.5,24,(0,0,-12))))
    left=(cq.Workplane('YZ',origin=(-16,0,-ECC)).circle(CAM_R)
          .workplane(offset=4).center(0,ECC).circle(9.5).loft())
    right=(cq.Workplane('YZ',origin=(12,0,0)).circle(9.5)
           .workplane(offset=4).center(0,-ECC).circle(CAM_R).loft())
    c=c.union(left).union(right)
    lever=box(50,69,5,(0,-34.5,-2.5)).rotate((0,0,0),(1,0,0),CLOSED_ANGLE)
    c=c.union(lever)
    bore=along_x(cyl(7.25,52,(0,0,-26)))
    c=c.cut(bore)
    # Recessed grip reduces mass. A 1.2mm web supports the opposite rail when
    # printed on its side; a through opening here would require a 42mm bridge.
    cut=box(32,42,8,(0,-39,-4)).rotate((0,0,0),(1,0,0),CLOSED_ANGLE)
    web=box(32,42,1.2,(0,-39,-.6)).rotate((0,0,0),(1,0,0),CLOSED_ANGLE)
    return c.cut(cut).union(web)

def axle():
    a=cq.Workplane('YZ').circle(PIN_R).extrude(76).translate((-35.5,0,0))
    a=a.union(box(2.5,20,18,(-36.75,0,-9)))
    a=a.cut(box(100,30,40,(0,20.5,-20)))
    # External groove is outside the loaded right cheek. No bending load on clip.
    sleeve=along_x(cyl(11,3,(0,0,36))).cut(along_x(cyl(5,3,(0,0,36))))
    # Hollow axle preserves bending stiffness; a 6mm bore is a short bridge
    # in the supplied flat print orientation, and removes nearly3g.
    return a.cut(sleeve).cut(along_x(cyl(3,82,(0,0,-40))))

def clip():
    # Flat U fork with long arms and small retaining bumps, not a brittle closed ring.
    c=box(16,20,2.7,(0,2,0))
    slot=cyl(5.2,3,(0,0,-.1)).union(box(10.4,16,3,(0,8,-.1)))
    c=c.cut(slot)
    for s in (-1,1):
        bump=cq.Workplane('XY').polyline([(s*5.2,3),(s*4.8,5),(s*5.2,7)]).close().extrude(2.7)
        c=c.union(bump)
    return c

def installed_clip():
    # Local clip XY -> world YZ, extrusion -> world X.
    return clip().rotate((0,0,0),(0,1,0),90).rotate((0,0,0),(1,0,0),90).translate((36.15,0,AXIS_Z+.25))

def assembly(theta=CLOSED_ANGLE):
    # Bearing clearances are taken up in the direction of the embossing reaction.
    ztop=AXIS_Z+.50-CAM_R-ECC*math.cos(math.radians(theta))
    return {
        'frame':frame(),
        'carrier':carrier().rotate((0,0,0),(0,1,0),180).translate((0,0,ztop)),
        'cam_lever':cam().rotate((0,0,0),(1,0,0),-theta).translate((0,0,AXIS_Z+.50)),
        'axle':axle().translate((0,0,AXIS_Z+.25)),
        'axle_clip':installed_clip(),
        'lower_die_ENVELOPE':die_envelope().translate((0,0,BASE)),
        'upper_die_ENVELOPE':die_envelope().rotate((0,0,0),(0,1,0),180).translate((0,0,ztop-5)),
    }

def print_shapes():
    shapes={'frame':frame(),'carrier':carrier(),
            'cam_lever':cam().rotate((0,0,0),(0,1,0),-90),
            'axle':axle().rotate((0,0,0),(1,0,0),-90),'axle_clip':clip()}
    return {n:s.translate((0,0,-s.val().BoundingBox().zmin)) for n,s in shapes.items()}

def overlap(a,b):
    aa=a.val().BoundingBox(); bb=b.val().BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-5 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-5 for k in 'xyz'):return 0.
    return a.intersect(b).val().Volume() if a.intersect(b).vals() else 0.

COLORS={'frame':(.25,.36,.48),'carrier':(.93,.62,.19),'cam_lever':(.24,.67,.60),
        'axle':(.75,.78,.81),'axle_clip':(.85,.30,.20),
        'lower_die_ENVELOPE':(.7,.55,.81),'upper_die_ENVELOPE':(.7,.55,.81)}

def export_assembly(parts,name):
    a=cq.Assembly(name=name)
    for n,s in parts.items(): a.add(s,name=n,color=cq.Color(*COLORS[n]))
    a.export(str(OUT/'step'/f'{name}.step'))

def render(parts,path):
    import vtk
    ren=vtk.vtkRenderer();ren.SetBackground(.96,.97,.99)
    for name,shape in parts.items():
        vv,ff=shape.val().tessellate(.08,.18)
        p=vtk.vtkPoints();cells=vtk.vtkCellArray()
        for v in vv:p.InsertNextPoint(v.x,v.y,v.z)
        for f in ff:
            cells.InsertNextCell(3)
            for i in f:cells.InsertCellPoint(i)
        poly=vtk.vtkPolyData();poly.SetPoints(p);poly.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(35)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*COLORS[name]);ren.AddActor(actor)
    camera=ren.GetActiveCamera();camera.SetPosition(150,-210,150);camera.SetFocalPoint(0,0,20);camera.SetViewUp(0,0,1);camera.ParallelProjectionOn()
    ren.ResetCamera();camera.Zoom(.92)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1200,1000);win.AddRenderer(ren);win.Render()
    filt=vtk.vtkWindowToImageFilter();filt.SetInput(win);filt.Update()
    w=vtk.vtkPNGWriter();w.SetFileName(str(path));w.SetInputConnection(filt.GetOutputPort());w.Write();win.Finalize()

def main():
    for d in ('stl','step','views','validation'): (OUT/d).mkdir(parents=True,exist_ok=True)
    records=[]
    for n,s in print_shapes().items():
        cq.exporters.export(s,str(OUT/'stl'/f'{n}.stl'),tolerance=.025,angularTolerance=.10)
        cq.exporters.export(s,str(OUT/'step'/f'{n}.step'))
        m=trimesh.load_mesh(OUT/'stl'/f'{n}.stl')
        records.append(dict(part=n,quantity=1,solid_upper_mass_g=round(m.volume*DENSITY,2),
            dimensions_mm=m.extents.round(3).tolist(),valid_brep=s.val().isValid(),
            solids=len(s.solids().vals()),watertight=bool(m.is_watertight),
            winding_consistent=bool(m.is_winding_consistent),mesh_bodies=len(m.split()),
            fits_220=bool(np.all(m.extents<=220)),bed_z=float(m.bounds[0,2])))
        print(n,records[-1],flush=True)
    collisions=[]
    # Nominal undeformed models intentionally include clamp interference with each die.
    for theta in (CLOSED_ANGLE,100,120,140,160,180):
        parts=assembly(theta)
        names=list(parts)
        for i,n in enumerate(names):
            for p in names[i+1:]:
                v=overlap(parts[n],parts[p])
                if v>.03: collisions.append(dict(angle=theta,a=n,b=p,overlap_mm3=round(v,4)))
        if theta in (CLOSED_ANGLE,180):
            tag='closed' if theta==CLOSED_ANGLE else 'open'
            export_assembly(parts,tag)
            render(parts,OUT/'views'/f'{tag}.png')
    parts=assembly()
    shifts={'frame':(0,0,0),'carrier':(0,-10,40),'cam_lever':(0,0,75),
            'axle':(-75,0,55),'axle_clip':(50,0,-12),
            'lower_die_ENVELOPE':(0,-55,15),'upper_die_ENVELOPE':(0,-55,40)}
    exploded={n:s.translate(shifts[n]) for n,s in parts.items()}
    export_assembly(exploded,'exploded');render(exploded,OUT/'views'/'exploded.png')
    compound=cq.Compound.makeCompound([s.val() for s in parts.values()]);b=compound.BoundingBox()
    report=dict(parts=records,solid_upper_mass_total_g=round(sum(r['solid_upper_mass_g'] for r in records),2),
        closed_dimensions_xyz_mm=[b.xlen,b.ylen,b.zlen],collisions=collisions,
        note='Rigid CAD, not physical proof. Die envelopes omit artwork. Clamp interference must be reviewed separately.')
    (OUT/'validation'/'geometry.json').write_text(json.dumps(report,indent=2))
    print('REPORT',json.dumps(report),flush=True)

if __name__=='__main__':main()
