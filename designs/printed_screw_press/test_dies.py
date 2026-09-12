"""Generate the optional working die pair ONLY via the shared generator."""
from pathlib import Path
import json
import sys
import model
ROOT=model.ROOT
sys.path.insert(0,str(ROOT))
from embossforge.generator import DieGenerationRequest,generate_die
from embossforge.config import adventurer_5m_profile
r=generate_die(DieGenerationRequest(
    artwork=Path(__file__).with_name("commissioning_mark.svg"),
    output_root=model.OUT/"test_dies",
    name="diamond_commissioning", relief_height_mm=.45,
    printer_profile=adventurer_5m_profile(), enforce_mating=True,
))
print(r.manifest)
print(r.validation.to_dict())
