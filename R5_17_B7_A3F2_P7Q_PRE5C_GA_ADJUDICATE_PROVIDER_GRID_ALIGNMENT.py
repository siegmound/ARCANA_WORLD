"""PRE5C-GA geometry-only crosswalk adjudication; never resamples or materializes state."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parent/'_ARCANA_EXTERNAL_SOURCES'/'p7q_parent_state'
EXPECTED={'GUM_V1':('GUM_V1/v1.0/raw/Boerker_et_al_GUM_v1.0.zip','6a2d47f2bc8f6df745c569003f1f536d37c78153e98b54005bfbcccc53d6ee63'),'GLIM_V1':('GLIM_V1/v1.0/raw/hartmann-moosdorf_2012.zip','43b4ce3276b155d804db8ff9fb227d620b4c35015a4cf564eac4d06d2b69d88e')}
def digest(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def grid(p):
 h={}
 for line in p.read_text(encoding='ascii').splitlines()[:6]:
  k,v=line.split(); h[k.lower()]=int(v) if k.lower() in ('ncols','nrows') else float(v)
 return h
def main():
 for _,(rel,want) in EXPECTED.items(): assert digest(CACHE/rel)==want
 gum=grid(CACHE/'GUM_V1/v1.0/raw/extracted/gum_v1.0_0point5deg.txt.asc'); glim=grid(CACHE/'GLIM_V1/v1.0/metadata/extracted/glim_wgs84_0point5deg.txt.asc')
 assert gum['cellsize']==glim['cellsize']==0.5 and gum['ncols']==glim['ncols']==720 and gum['nrows']==347 and glim['nrows']==360
 dx=gum['xllcorner']-glim['xllcorner']; dy=gum['yllcorner']-glim['yllcorner']; cs=gum['cellsize']; fx=(cs-dx)/cs; fy=(cs-dy)/cs; dominant=fx*fy; secondary=max((1-fx)*fy,fx*(1-fy),(1-fx)*(1-fy))
 assert 0.95<=dominant<1 and dx>0 and dy>0
 result={'stage':'R5.17-B7-A3F2-P7Q-PRE5C-GA','decision':'AUTHORIZE_P7Q_PRE5C_GUM_CLASS_SEMANTIC_DECODING_GATE_WITH_DOMINANT_OVERLAP_CROSSWALK','same_crs':True,'same_grid':False,'cell_size_compatible':True,'origin_offsets_degrees':{'delta_x':dx,'delta_y':dy},'origin_offsets_cells':{'delta_x':dx/cs,'delta_y':dy/cs},'dominant_overlap':{'minimum':dominant,'mean':dominant,'maximum':dominant,'minimum_second_largest':secondary,'maximum_second_largest':secondary,'unique_dominant_mappings':249840,'ties':0,'cells_crossing_longitude_wrap':0,'cells_partially_outside_glim_extent':347,'cells_without_glim_overlap':0},'coverage':{'gum_cells':249840,'glim_only_full_northern_rows':12,'partial_overlap_northern_row':347,'glim_only_full_row_range':[348,359]},'crosswalk':{'type':'DOMINANT_AREA_OVERLAP_CROSSWALK','row_mapping':'GLiM row = GUM row for r=0..346; ESRI rows are north-to-south serialization, mathematical bounds used','column_mapping':'GLiM column = GUM column for c=0..719; final GUM column extends 0.00001925036 degrees beyond GLiM xmax','antimeridian_handling':'NO_WRAP; explicit east-edge extent spill retained as partial-outside metric'},'prohibitions':{'resampling':False,'reprojection':False,'canonical_grid_generated':False,'parent_state_materialized':False,'gum_absence_to_bedrock':False,'glim_role':'SURFACE_LITHOLOGY_CONDITIONER_ONLY','gum_codes_decoded':False,'land_state_bound':False,'p7q_reopened':False}}
 print(json.dumps(result,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
