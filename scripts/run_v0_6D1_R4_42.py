from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r442_geonomics_multi_transition_bounded_replay_production_queue_authorization import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R442_") else 3)
