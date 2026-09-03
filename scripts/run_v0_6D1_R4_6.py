from __future__ import annotations

from pathlib import Path
import argparse
import json
import threading
import time

from arcana_worldsim.scientific_engines.r46_targeted_causal_counterfactual import run

p = argparse.ArgumentParser()
p.add_argument("--root", default=".")
a = p.parse_args()
root = Path(a.root).resolve()

stop = threading.Event()
t0 = time.time()

def heartbeat() -> None:
    while not stop.wait(30.0):
        print(f"  R4.6 diagnostic counterfactual still running ({time.time()-t0:.0f}s elapsed)", flush=True)

th = threading.Thread(target=heartbeat, daemon=True)
th.start()
try:
    result, _ = run(root, execute_counterfactual=True)
finally:
    stop.set()
print(json.dumps(result, indent=2), flush=True)
raise SystemExit(0 if result.get("status", "").startswith("PASS_") else 3)
