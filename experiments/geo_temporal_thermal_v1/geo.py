"""Geographic selection over pinned, existing R6 thermal histories; no evolution."""
from pathlib import Path
import sys,json,math,time,copy
REPO=Path(__file__).resolve().parents[2]
for sub in ('src','experiments/thermal_1d_history_v1','experiments/thermal_controller_history_v1','experiments/thermal_controller_v2','experiments/thermal_controller_v3','experiments/multi_column_thermal_v1'):
 sys.path.insert(0,str(REPO/sub))
import thermal
from adapter import sha
from reader import query_state
from scheduler import Scheduler,CoordinatedReader
from arcana_worldsim.r6.identity import thaw_json
from arcana_worldsim.r6.state import SpatialSupport
from arcana_worldsim.r6.initial_world.grid import GlobalGrid1Degree
DAT_SHA='2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584'
META_SHA='876a9365ae76ad7a6fa10470317d754e08b82b9fc69cac8d72203e06a8ee7ce0'
OWNERS={'C028':(91,28,32792),'C139':(13,139,4823)}

def region_parts(region):
 """BBox south,north,west,east; west>east crosses seam. Positive-area overlap."""
 if len(region)!=4 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in region):raise ValueError('REGION_NUMBERS')
 s,n,w,e=region
 if not -90<=s<n<=90 or not -180<=w<=180 or not -180<=e<=180 or w==e or (w==180 and e==-180):raise ValueError('REGION_BOUNDS')
 return s,n,[(w,e)] if w<e else [(w,180.),(-180.,e)]

def intersection_area(region,cell,radius):
 s,n,parts=region_parts(region);a,b,w,e=cell
 lo,hi=max(s,a),min(n,b)
 if hi<=lo:return 0.
 width=sum(max(0.,min(y,e)-max(x,w)) for x,y in parts)
 return radius**2*math.radians(width)*(math.sin(math.radians(hi))-math.sin(math.radians(lo)))

def make_catalog():
 grid=GlobalGrid1Degree();dp=REPO/'R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat';mp=dp.with_suffix('.json')
 if sha(dp)!=DAT_SHA or sha(mp)!=META_SHA:raise ValueError('PRE_IDENTITY')
 meta=json.loads(mp.read_text());selected={}
 with dp.open() as f:
  next(f)
  for line in f:
   vals=line.split()
   if not vals:continue
   node=int(vals[0])
   if node in {v[2] for v in OWNERS.values()}:selected[node]=dict(zip(meta['field_order'],map(float,vals)))
 cells={};areas=grid.cell_areas_m2()
 for k,(r,c,node) in OWNERS.items():
  pre=selected[node]
  if pre['owner_row']!=r or pre['owner_column']!=c:raise ValueError('PRE_OWNER')
  bounds=[float(grid.lat_bounds_deg[r]),float(grid.lat_bounds_deg[r+1]),float(grid.lon_bounds_deg[c]),float(grid.lon_bounds_deg[c+1])]
  area=intersection_area(bounds,bounds,grid.radius_m)
  if not math.isclose(area,float(areas[r,c]),rel_tol=2e-14):raise ValueError('INDEPENDENT_AREA')
  support=SpatialSupport(grid.grid_id,(grid.cell_id(r,c),),'1-degree runtime owner cell; no resolved horizontal thermal field')
  cells[k]=dict(column_id=grid.cell_id(r,c),PRE_node_id=node,PRE_record=pre,bounds_south_north_west_east_deg=bounds,cell_center_lat_lon_deg=[float(grid.lat_centers_deg[r]),float(grid.lon_centers_deg[c])],cell_area_m2=float(areas[r,c]),independent_area_m2=area,spatial_support=support.to_dict(),subcell_column_location='UNKNOWN',horizontal_field='NOT_SIMULATED',binding_semantics=meta['numerical_owner_authority'])
 return dict(schema='EXPERIMENTAL_R6_GEOGRAPHIC_COLUMN_CATALOG_V1',grid=grid.metadata(),source_sha256={'grid.py':sha(REPO/'src/arcana_worldsim/r6/initial_world/grid.py'),'PRE.dat':DAT_SHA,'PRE.json':META_SHA},owner_rule=meta['numerical_ownership_rule'],authority_disclaimer=meta['physical_authority_disclaimer'],cells=cells,coverage='Two independent vertical model columns associated with owner cells; no areal thermal interpolation or global field')

class GeoReader:
 def __init__(self,root,plan_sha,catalog,catalog_sha,budget=786432):
  self.path=Path(catalog)
  if sha(self.path)!=catalog_sha:raise ValueError('CATALOG_SHA')
  self.catalog=json.loads(self.path.read_text());self.catalog_sha=catalog_sha
  self.s=Scheduler(root,plan_sha);self.reader=CoordinatedReader(self.s,budget)
  if self.catalog['source_sha256']['grid.py']!=sha(REPO/'src/arcana_worldsim/r6/initial_world/grid.py'):raise ValueError('GRID_SOURCE')
  if set(self.catalog['cells'])!=set(OWNERS):raise ValueError('CATALOG_COLUMNS')
  grid=GlobalGrid1Degree()
  for k,(r,c,node) in OWNERS.items():
   b=self.catalog['cells'][k];ctx=self.s.controllers[k].ctx;pre=b['PRE_record'];g=self.s.controllers[k].static['geometry']
   expected=[float(grid.lat_bounds_deg[r]),float(grid.lat_bounds_deg[r+1]),float(grid.lon_bounds_deg[c]),float(grid.lon_bounds_deg[c+1])]
   if b['column_id']!=ctx['column'] or b['column_id']!=grid.cell_id(r,c) or b['PRE_node_id']!=node or b['bounds_south_north_west_east_deg']!=expected or b['spatial_support']['cell_ids']!=[ctx['column']] or b['spatial_support']['grid_id']!=grid.grid_id or b['cell_area_m2']!=float(grid.cell_areas_m2()[r,c]):raise ValueError('CATALOG_GEOGRAPHY')
   if ctx['PRE_DAT_sha256']!=DAT_SHA or self.catalog['source_sha256']['PRE.dat']!=DAT_SHA or self.catalog['source_sha256']['PRE.json']!=META_SHA or pre['node_id']!=node or pre['owner_row']!=r or pre['owner_column']!=c or g['Moho_m']!=pre['crust_thickness_m'] or g['z_m'][-1]!=pre['lab_depth_m'] or (ctx['Dirichlet_K'][0]!=pre['surface_temperature_k'] or abs(ctx['Dirichlet_K'][1]-pre['lab_temperature_k'])>math.ulp(pre['lab_temperature_k'])):raise ValueError('GEOGRAPHIC_PHYSICAL_BINDING')
 def __enter__(self):self.reader.__enter__();return self
 def __exit__(self,*a):return self.reader.__exit__(*a)
 def refresh(self):return self.reader.refresh()
 def query(self,region,step,low=0.,high=8.,process='THERMAL_1D'):
  started=time.perf_counter();s,n,parts=region_parts(region)
  if type(step)is not int:raise ValueError('INTEGER_ACCEPTED_STEP')
  if not all(math.isfinite(v) for v in (low,high)) or low<0 or low>high:raise ValueError('DEPTH_BOUNDS')
  if sha(self.path)!=self.catalog_sha:raise ValueError('CATALOG_CHANGED')
  rd=self.reader;rd._check();radius=self.catalog['grid']['radius_m'];selected={k:b for k,b in self.catalog['cells'].items() if intersection_area(region,b['bounds_south_north_west_east_deg'],radius)>0}
  region_area=radius**2*sum(math.radians(y-x) for x,y in parts)*(math.sin(math.radians(n))-math.sin(math.radians(s)))
  answer=dict(status='AVAILABLE',process=process,region_south_north_west_east_deg=list(region),step=step,epoch_registry_view=rd.view.view_id,catalog_sha256=self.catalog_sha,columns={},interpolated=False,region_area_m2=region_area,selected_owner_cells=list(selected),coverage_semantics=self.catalog['coverage'],horizontal_thermal_field='NOT_SIMULATED')
  answer['selected_owner_cell_overlap_m2']=sum(intersection_area(region,b['bounds_south_north_west_east_deg'],radius) for b in selected.values())
  answer['region_outside_selected_owner_cells_m2']=max(0.,region_area-answer['selected_owner_cell_overlap_m2'])
  answer['actual_horizontal_thermal_coverage_area_m2']=None
  if process!='THERMAL_1D':answer.update(status='UNKNOWN',reason='PROCESS_NOT_IN_THIS_CATALOG');return answer
  if not selected:answer.update(status='NOT_SIMULATED',reason='NO_SIMULATED_COLUMN_OWNER_CELL_INTERSECTS_REGION');return answer
  if step not in self.s.plan['snapshot_steps']:answer.update(status='TIME_NOT_ARCHIVED',archived_steps=self.s.plan['snapshot_steps']);return answer
  if step not in rd.by_step:answer.update(status='EPOCH_INCOMPLETE',reason='SHARED_EPOCH_NOT_COMMITTED_IN_PINNED_VIEW');return answer
  epoch=rd.by_step[step];value=thaw_json(epoch.value);answer.update(epoch_state_id=str(epoch.state_id),epoch_parent_state_ids=list(epoch.parent_state_ids),time_s=step*self.s.plan['dt_s'],model_years=step*self.s.plan['dt_s']/thermal.YEAR)
  for k,binding in selected.items():
   session=rd.sessions[k];ref=value['columns'][k];state=session.restore(ref['state_id'])
   if ref['column_id']!=session.c.ctx['column'] or ref['static_sha256']!=session.c.job['static_sha256'] or ref['history_id']!=session.c.history_id or ref['branch_id']!=session.c.branch_id or thermal.digest(state)!=ref['native_sha256'] or state['step']!=step or state['time_s']!=step*self.s.plan['dt_s']:raise ValueError('EPOCH_COLUMN_REFERENCE')
   rec=session.store.read_state(ref['state_id']);g=state['geometry'];bottom=g['z_m'][-1]
   q=query_state(state,ref['state_id'],ref['column_id'],state['time_s']/thermal.YEAR,low,high,started);q.pop('read_restore_query_s')
   unknown=[]
   if high>bottom:unknown.append([max(low,bottom),high])
   if low>bottom:q.update(status='UNKNOWN',reason='DEPTH_OUTSIDE_VERTICAL_SUPPORT')
   q.update(PRE_vs_stored_base_temperature_difference_K=state['context']['Dirichlet_K'][1]-binding['PRE_record']['lab_temperature_k'],unknown_depth_intervals_m=unknown,native_sha256=ref['native_sha256'],parent_state_ids=list(rec.parent_state_ids),history_id=ref['history_id'],branch_id=ref['branch_id'],column_read_view=session.view.view_id,geographic_binding=copy.deepcopy(binding),geometry=copy.deepcopy(g),physical_conditions=copy.deepcopy(state['context']),provenance=session.store.trace_provenance(rec))
   answer['columns'][k]=q
  if all(q['status']=='UNKNOWN' for q in answer['columns'].values()):answer['status']='UNKNOWN'
  answer.update(cache=rd.cache_report(),query_s=time.perf_counter()-started)
  return answer
