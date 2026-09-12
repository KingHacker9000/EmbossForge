"""Independent exported-mesh checks and approximate shell/infill mass estimate."""
from pathlib import Path
import json, math
import numpy as np
import trimesh
from scipy.ndimage import minimum_filter
import model

OUT=model.OUT
def trans(x=0,y=0,z=0):
    m=np.eye(4);m[:3,3]=[x,y,z];return m
def rot(angle,axis):return trimesh.transformations.rotation_matrix(math.radians(angle),axis)
def overlap(a,b):
    if np.any(a.bounds[1]<=b.bounds[0]+1e-5) or np.any(b.bounds[1]<=a.bounds[0]+1e-5):return 0.
    v=trimesh.boolean.intersection([a,b],engine='manifold')
    return max(0,float(v.volume)) if len(v.faces) else 0.

def main():
    meshes={p.stem:trimesh.load_mesh(p) for p in (OUT/'stl').glob('*.stl')}
    checks=[];masses=[]
    for name,m in meshes.items():
        # Conservative rectilinear erosion. Five0.45mm walls and six0.20mm skins.
        # Voxel estimate, NOT slicer output. Normalize to exact mesh solid volume.
        pitch=.5
        v=m.voxelized(pitch).fill().matrix
        core=minimum_filter(v.astype(np.uint8),size=(11,11,7),mode='constant',cval=0)>0
        core_fraction=float(core.sum()/v.sum())
        est=m.volume*.00124*(1-.85*core_fraction)
        # Axle: seven walls; approximate full material because 14mm diameter.
        if name=='axle':est=m.volume*.00124
        masses.append(dict(part=name,quantity=1,estimated_g=round(est,1),solid_upper_g=round(m.volume*.00124,2),
                           method='0.5mm voxel shell/core estimate; axle conservatively solid'))
    for theta in (model.CLOSED_ANGLE,100,120,140,160,180):
        top=model.AXIS_Z+.5-model.CAM_R-model.ECC*math.cos(math.radians(theta))
        transforms={
            'frame':np.eye(4),
            'carrier':trans(z=top)@rot(180,[0,1,0]),
            'cam_lever':trans(z=model.AXIS_Z+.5)@rot(-theta,[1,0,0])@rot(90,[0,1,0])@trans(z=-25),
            'axle':trans(z=model.AXIS_Z+.25)@rot(90,[1,0,0])@trans(z=-5.5),
            'axle_clip':trans(x=36.15,z=model.AXIS_Z+.25)@rot(90,[1,0,0])@rot(90,[0,1,0])}
        placed={n:m.copy().apply_transform(transforms[n]) for n,m in meshes.items()}
        names=list(placed)
        for i,n in enumerate(names):
            for nn in names[i+1:]:
                volume=overlap(placed[n],placed[nn])
                checks.append(dict(angle=theta,a=n,b=nn,overlap_mm3=round(volume,4),pass_check=volume<.03))
        paper=trimesh.creation.box(extents=[210,124,.1],transform=trans(y=-38,z=12.05))
        for n,m in placed.items():
            volume=overlap(m,paper)
            checks.append(dict(angle=theta,a=n,b='210mm wide paper corridor',overlap_mm3=round(volume,4),pass_check=volume<.03))
    # Basic insertion: carrier, cam and axle can be installed in sequence.
    # These are rigid translation sweeps, with the die-retention flexures excluded.
    closed=model.assembly()
    assembly_checks=[]
    for dz in (0,5,15,30,60):
        volume=model.overlap(closed['carrier'].translate((0,0,dz)),closed['frame'])
        assembly_checks.append(dict(operation='carrier drop-in before cam',displacement_mm=dz,overlap_mm3=round(volume,4)))
    for dz in (0,10,30,60):
        volume=model.overlap(closed['cam_lever'].translate((0,0,dz)),closed['frame'])
        assembly_checks.append(dict(operation='cam drop-in before axle',displacement_mm=dz,overlap_mm3=round(volume,4)))
    for dx in (-100,-60,-20,0):
        moved=closed['axle'].translate((dx,0,0))
        volume=sum(model.overlap(moved,closed[n]) for n in ('frame','carrier','cam_lever'))
        assembly_checks.append(dict(operation='axle insertion from left',displacement_mm=dx,overlap_mm3=round(volume,4)))
    result=dict(mesh_checks=checks,mesh_checks_pass=all(c['pass_check'] for c in checks),
        assembly_path_checks=assembly_checks,assembly_paths_pass=all(c['overlap_mm3']<.03 for c in assembly_checks),
        mass=masses,total_estimate_g=round(sum(m['estimated_g'] for m in masses),1),
        warning='Nominal CAD only. Mass excludes supports/brim, dies; no sliced time or fatigue validation.')
    (OUT/'validation'/'exported_mesh_checks.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='mesh_checks'},indent=2),flush=True)

if __name__=='__main__':main()
