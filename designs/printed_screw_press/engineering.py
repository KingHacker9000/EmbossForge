"""Auditable screening calculations. NOT FEA, a load certification, or a test."""
import json
import math
from pathlib import Path
import model

out=model.OUT/"validation"
out.mkdir(parents=True,exist_ok=True)
pi=math.pi
rows=[]
for load in [300,500,750]:
    for mu in [.15,.25,.35]:
        # 45-degree half angle follows the custom printable trapezoidal flanks.
        dm=26.;lead=6.;alpha=pi/4
        tl=lead/(pi*dm);m=mu/math.cos(alpha)
        t_thread=load*dm/2*(tl+m)/(1-m*tl)
        # Uniform pressure on flat radius-12 foot: mean friction radius = 2R/3.
        t_foot=load*mu*8
        torque=(t_thread+t_foot)/1000
        hand=torque/.08
        rows.append(dict(load_N=load,mu=mu,torque_Nm=round(torque,3),
                         tangential_hand_N=round(hand,2),force_ratio=round(load/hand,2)))

E=1800.;b=72.;arm_t=28.;bottom_t=32.;spine_t=40.;L=36.;H=80.
I=b*arm_t**3/12;Ib=b*bottom_t**3/12;Is=b*spine_t**3/12
screen=[]
for f in [500,750]:
    rootstress=f*L/(b*arm_t**2/6)
    spine=f*56/(b*spine_t**2/6)
    # Two cantilever arms + spine rotation estimate, deliberately approximate.
    arms=f*L**3/(3*E)*(1/I+1/Ib)
    spine_rotation=f*56*H/(E*Is)
    opening=arms+spine_rotation*L
    thread_area=pi*24*28*.5
    shear=f/thread_area*3 # first turns take disproportionate load
    bearing=f/(pi*12**2)
    flange_area=2*(34**2-28**2)
    screen.append(dict(load_N=f,arm_nominal_MPa=round(rootstress,3),
       arm_with_Kt_2_5_MPa=round(rootstress*2.5,3),spine_nominal_MPa=round(spine,3),
       opening_estimate_mm=round(opening,3),spine_rotation_deg=round(math.degrees(spine_rotation),3),
       thread_shear_with_3x_concentration_MPa=round(shear,3),
       flat_foot_pressure_MPa=round(bearing,3),nut_flange_bearing_MPa=round(f/flange_area,3)))
data=dict(status="screening estimates; not rated or physically tested",properties=dict(E_MPa=E,
    in_plane_screening_allowable_MPa=8,interlayer_shear_screening_allowable_MPa=5,
    density_g_cm3=1.24),force_cases=rows,structure=screen,
    gross_area_scaled_paper_force_N=round(1000*pi*21**2/3600,2),
    ideal_force_ratio=round(2*pi*80/6,2),thread_turns_engaged=round(28/6,3),
    self_locking_mu_threshold=round(6/(pi*26)*math.cos(pi/4),4))
(out/"engineering_calculations.json").write_text(json.dumps(data,indent=2))
print(json.dumps(data,indent=2))
