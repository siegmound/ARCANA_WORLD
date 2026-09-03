from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r454_non_geonomics_exact_seed_readout_dry_run_authorization import build
out=build(Path.cwd())
print(json.dumps(out,indent=2,ensure_ascii=False))
raise SystemExit(0 if str(out.get("status","")).startswith("PASS_R454_") else 3)
