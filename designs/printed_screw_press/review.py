"""Validate actual STL exports and CAD assembly; render exact modeled surfaces."""
import itertools
import json
from pathlib import Path
import math
import numpy as np
import cadquery as cq
import trimesh
import vtk
import model


def overlaps(a, b):
    a, b = a.BoundingBox(), b.BoundingBox()
    return all(min(hi1, hi2) - max(lo1, lo2) > .001 for lo1, hi1, lo2, hi2 in
               [(a.xmin, a.xmax, b.xmin, b.xmax), (a.ymin, a.ymax, b.ymin, b.ymax),
                (a.zmin, a.zmax, b.zmin, b.zmax)])


def render(items, path, view="iso", title=""):
    ren = vtk.vtkRenderer()
    ren.SetBackground(.94, .95, .96)
    colors = {"frame_left":(.24,.32,.38), "frame_right":(.30,.39,.45),
              "power_screw":(.92,.57,.18), "power_nut":(.20,.52,.53),
              "guided_ram":(.20,.52,.53), "lower_tray":(.35,.68,.66),
              "upper_tray":(.35,.68,.66)}
    for name, wp in items.items():
        verts, tris = wp.val().tessellate(.10, .2)
        points=vtk.vtkPoints()
        for v in verts: points.InsertNextPoint(v.x,v.y,v.z)
        cells=vtk.vtkCellArray()
        for t in tris:
            cells.InsertNextCell(3)
            for i in t: cells.InsertCellPoint(i)
        pd=vtk.vtkPolyData(); pd.SetPoints(points); pd.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(pd);normals.SetFeatureAngle(35)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*(colors.get(name, (.93,.76,.34) if "ENVELOPE" in name else (.68,.71,.73))))
        actor.GetProperty().SetSpecular(.15);actor.GetProperty().SetSpecularPower(20)
        ren.AddActor(actor)
    camera=ren.GetActiveCamera()
    pos={"iso":(260,-340,240), "side":(350,0,100), "front":(0,-400,100), "top":(0,0,450)}[view]
    camera.SetPosition(*pos);camera.SetFocalPoint(0,0,95);camera.SetViewUp(0,0,1 if view!="top" else 0)
    if view=="top":camera.SetViewUp(0,1,0)
    camera.ParallelProjectionOn();ren.ResetCamera();camera.Zoom(1.08)
    if title:
        label=vtk.vtkTextActor();label.SetInput(title);label.SetPosition(24,24)
        label.GetTextProperty().SetFontSize(22);label.GetTextProperty().SetColor(.15,.20,.24)
        ren.AddActor2D(label)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.AddRenderer(ren);window.SetSize(1300,1100)
    window.Render()
    grab=vtk.vtkWindowToImageFilter();grab.SetInput(window);grab.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(grab.GetOutputPort());writer.Write()
    window.Finalize()


def main():
    out=model.OUT
    parts=model.build()
    findings={"stl":[], "interferences":[]}
    for path in sorted((out/"stl").glob("*.stl")):
        mesh=trimesh.load_mesh(path)
        r=dict(part=path.stem,watertight=bool(mesh.is_watertight), winding=bool(mesh.is_winding_consistent),
               components=len(mesh.split()), positive_volume=bool(mesh.volume>0),
               extents_mm=mesh.extents.tolist(), fits_220=bool(max(mesh.extents)<=220),
               on_bed=bool(abs(mesh.bounds[0,2])<.001))
        findings["stl"].append(r)
    for stroke in [0,2.5,5,7.5,10]:
        items=model.assembly(parts,stroke)
        for (a,wa),(b,wb) in itertools.combinations(items.items(),2):
            sa,sb=wa.val(),wb.val()
            if not overlaps(sa,sb):continue
            inter=sa.intersect(sb)
            vol=inter.Volume()
            if vol>.03:
                r=dict(stroke=stroke,a=a,b=b,volume_mm3=round(vol,4))
                findings["interferences"].append(r);print(r,flush=True)
    (out/"validation"/"geometry_review.json").write_text(json.dumps(findings,indent=2))
    for state,stroke in [("open",10),("closed",0)]:
        items=model.assembly(parts,stroke)
        render(items,out/"images"/f"{state}.png",title=f"All-PLA screw press | {state} | CAD, untested prototype")
        render(items,out/"images"/f"{state}_side.png","side",title=f"{state} | section-free side view")
    render(model.assembly(parts,0,True),out/"images"/"exploded.png",title="Exploded assembly | CAD, untested prototype")
    print("Review complete",flush=True)


if __name__=="__main__":main()
