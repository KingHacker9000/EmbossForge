"""Independent mesh Boolean checks for service paths and actual working dies."""
import json
import numpy as np
import cadquery as cq
import trimesh
import model
from review import render


def mesh(wp):
    vertices,faces=wp.val().tessellate(.025,.10)
    return trimesh.Trimesh(vertices=[(v.x,v.y,v.z) for v in vertices],faces=faces,process=True)


def collide(a,b):
    if not np.all(np.minimum(a.bounds[1],b.bounds[1])-np.maximum(a.bounds[0],b.bounds[0])>1e-5):return 0.
    return float(trimesh.boolean.intersection([a,b],engine="manifold").volume)


class MeshDisplay:
    def __init__(self,m):self.m=m
    def val(self):return self
    def tessellate(self,*args):return ([cq.Vector(*v) for v in self.m.vertices],self.m.faces.tolist())


def main():
    out=model.OUT
    parts=model.build()
    report={"threshold_mm3":.03,"actual_die_interferences":[],"removal_interferences":[],
            "paper_path_interferences":[],"gauge_interferences":[]}
    die_dir=out/"test_dies"/"diamond_commissioning"
    for opening in [0,10]:
        items=model.assembly(parts,opening)
        items={k:v for k,v in items.items() if "ENVELOPE" not in k}
        mm={k:mesh(v) for k,v in items.items()}
        dies=[]
        for kind,z,rot in [("male",39.5,False),("female",45.6+opening,True)]:
            m=trimesh.load_mesh(die_dir/f"diamond_commissioning_{kind}.stl")
            assert m.is_watertight and m.is_winding_consistent and m.volume>0
            if rot:m.apply_transform(np.diag([-1,1,-1,1]))
            m.apply_translation([.3,0,z]);dies.append(m)
            for name,p in mm.items():
                v=collide(m,p)
                if v>.03:report["actual_die_interferences"].append([opening,kind,name,v])
            items[f"{kind}_actual_die"]=MeshDisplay(m)
        report[f"actual_die_pair_overlap_at_{opening}_mm3"]=collide(*dies)
        render(items,out/"images"/f"{('closed' if opening==0 else 'open')}_actual_dies.png",
               title="Original all-PLA press | actual commissioning die meshes | untested physical prototype")
    open_parts={k:mesh(v) for k,v in model.assembly(parts,10).items()}
    for which in ["lower","upper"]:
        names=[f"{which}_tray",f"{which}_clamp",f"{which}_clamp_screw",f"{which}_die_ENVELOPE_NOT_PRINT"]
        fixed={k:v for k,v in open_parts.items() if k not in names and k!=f"{which}_tray_retainer"}
        for distance in np.linspace(0,110,23):
            for name in names:
                moving=open_parts[name].copy();moving.apply_translation([0,-distance,0])
                for other,p in fixed.items():
                    v=collide(moving,p)
                    if v>.03:report["removal_interferences"].append([which,float(distance),name,other,v])
    for yc in [-150,-120,-90,-60,-30]:
        sheet=trimesh.creation.box(extents=[210,120,.15]);sheet.apply_translation([0,yc,44.075])
        for name,p in open_parts.items():
            v=collide(sheet,p)
            if v>.03:report["paper_path_interferences"].append([yc,name,v])
    gauge=mesh(parts["16_alignment_gauge_TOOL"]);gauge.apply_translation([.3,0,39.5])
    for name,part in model.assembly(parts,9.9).items():
        if "ENVELOPE" in name:continue
        v=collide(gauge,mesh(part))
        if v>.03:report["gauge_interferences"].append([name,v])
    report["die_axis_centers_mm"]={"male":[.3,0],"female":[.3,0]}
    report["open_paper_gap_above_male_relief_mm"]=52.6-42.95
    report["opening_stop_contact_z_mm"]=106.
    (out/"validation"/"assembly_service_checks.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":main()
