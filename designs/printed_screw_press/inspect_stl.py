"""Render the actual delivered meshes, not CAD preview substitutes."""
import json
import math
from pathlib import Path
import numpy as np
import trimesh
import vtk
from PIL import Image, ImageDraw, ImageFont
import model

out=model.OUT
paths=sorted((out/"stl").glob("*.stl"))
font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",16)
canvas=Image.new("RGB",(1600,math.ceil(len(paths)/4)*380),"#f1f4f6")
draw=ImageDraw.Draw(canvas)
findings=[]
for n,path in enumerate(paths):
    mesh=trimesh.load_mesh(path)
    down=(mesh.face_normals[:,2]<-math.sqrt(.5)) & (mesh.triangles_center[:,2]>.3)
    findings.append(dict(part=path.stem,overhang_area_above_bed_mm2=round(float(mesh.area_faces[down].sum()),2),
                         note="Area screening only: includes short bridges; not a support or slicing simulation."))
    reader=vtk.vtkSTLReader();reader.SetFileName(str(path));reader.Update()
    normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(reader.GetOutputPort());normals.SetFeatureAngle(35)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
    actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(.20,.51,.54)
    ren=vtk.vtkRenderer();ren.SetBackground(.945,.957,.965);ren.AddActor(actor)
    b=mesh.bounds;center=mesh.centroid;camera=ren.GetActiveCamera()
    camera.SetPosition(*(center+np.array([180,-230,180])));camera.SetFocalPoint(*center);camera.SetViewUp(0,0,1)
    camera.ParallelProjectionOn();ren.ResetCamera();camera.Zoom(.92)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.AddRenderer(ren);window.SetSize(400,320);window.Render()
    grab=vtk.vtkWindowToImageFilter();grab.SetInput(window);grab.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(out/"images"/f"part_{path.stem}.png"));writer.SetInputConnection(grab.GetOutputPort());writer.Write();window.Finalize()
    x=(n%4)*400;y=(n//4)*380
    canvas.paste(Image.open(out/"images"/f"part_{path.stem}.png"),(x,y))
    draw.text((x+12,y+321),path.stem,font=font,fill="#183844")
    draw.text((x+12,y+344)," x ".join(f"{v:.1f}" for v in mesh.extents)+" mm",font=font,fill="#183844")
canvas.save(out/"images"/"all_print_parts.png")
(out/"validation"/"overhang_screening.json").write_text(json.dumps(findings,indent=2))
print("Actual STL inspection sheet rendered")
