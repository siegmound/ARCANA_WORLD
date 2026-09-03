from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from arcana_worldsim.state_query.r57_block_closure import seal_block, FINAL_STATUS


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    result = seal_block(Path(args.root))
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == FINAL_STATUS and result.get("sealed") is True else 1


if __name__ == "__main__":
    sys.exit(main())
