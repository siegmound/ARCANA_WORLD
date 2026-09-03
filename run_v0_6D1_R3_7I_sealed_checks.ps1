$ErrorActionPreference = "Stop"
python .\scripts\formal_audit_v0_6D1_R3_7I_SEALED.py
python -m pytest -q .\tests\test_r37i_production_promotion.py
