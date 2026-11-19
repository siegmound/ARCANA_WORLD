"""Existing physical-input inventory and conservative mapping, NO evolution."""
import argparse,json,hashlib,csv,time,resource,math
from pathlib import Path
import numpy as np
from .mapping import remap,admit_cover,unit_checks

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 repo=a.base/'ARCANA_WORLD_R6_GEOMETRY_R1_WORK';p0=a.base/'ARCANA_WORLD_EVIDENCE/R6/HR2_P0_20261031_01';start=time.perf_counter();u0=resource.getrusage(resource.RUSAGE_SELF)
 inputs={};payloads=json.loads((p0/'GLOBAL_T0_PAYLOADS.json').read_text())
 def auth(p,expected=None):
  p=Path(p);h=sha(p)
  if expected is not None and h!=expected:raise ValueError('SOURCE_SHA:'+str(p))
  inputs[str(p)]={'sha256':h,'bytes':p.stat().st_size};return p
 inventory=[]
 for item in payloads:
  p=auth(item['path'],item['sha256'])
  if p.suffix=='.npz':
   with np.load(p,allow_pickle=False) as z:
    fields=[]
    for name in z.files:
     x=z[name];finite=np.isfinite(x);fields.append({'name':name,'shape':list(x.shape),'dtype':x.dtype.str,
       'finite':int(finite.sum()),'nonfinite':int((~finite).sum()),'minimum':float(x[finite].min()) if finite.any() else None,
       'maximum':float(x[finite].max()) if finite.any() else None,'raw_sha256':hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()})
    inventory.append({'role':item['role'],'path':str(p),'fields':fields,'authority':'AUTHORIAL_R6_T0_MODEL_NOT_OBSERVATION','mobile_cover_field_present':False})
  else:
   manifest=auth(item['manifest'],item['manifest_sha256']);meta=json.loads(manifest.read_text());names=meta['field_order'];index={n:i for i,n in enumerate(names)}
   requested=['surface_temperature_k','surface_heat_flow_w_m2','crust_thickness_m','mantle_lithosphere_thickness_m','lab_depth_m','moho_temperature_k','lab_temperature_k','crust_density_kg_m3','crust_conductivity_w_m_k','crust_cp_j_kg_k','mantle_density_kg_m3','mantle_conductivity_w_m_k','mantle_cp_j_kg_k']
   stats={n:[math.inf,-math.inf] for n in requested};branches={};presence={n:0 for n in names if n.endswith('_present')};ids=set();owners=set();pairs=set();n=0
   with p.open() as f:
    header=f.readline().split();assert header[0]=='ARCANA_R6_PRE_ORBDATA_RUNTIME_V1'
    for line in f:
     row=list(map(float,line.split()));assert len(row)==len(names) and all(map(math.isfinite,row));n+=1;ids.add(int(row[0]));owners.add((int(row[index['owner_row']]),int(row[index['owner_column']])))
     branch=str(int(row[index['runtime_branch_code']]));branches[branch]=branches.get(branch,0)+1
     for k in requested:val=row[index[k]];stats[k][0]=min(stats[k][0],val);stats[k][1]=max(stats[k][1],val)
     for k in presence:presence[k]+=int(row[index[k]])
     pairs.add(tuple(row[index[k]] for k in ['crust_density_kg_m3','crust_conductivity_w_m_k','crust_cp_j_kg_k','mantle_density_kg_m3','mantle_conductivity_w_m_k','mantle_cp_j_kg_k']))
   assert n==64442 and len(ids)==n
   inventory.append({'role':item['role'],'path':str(p),'records':n,'unique_node_ids':len(ids),'unique_numerical_owner_cells':len(owners),'fields_per_record':len(names),
    'branch_counts':branches,'present_flag_counts':presence,'stats':stats,'material_property_combinations':sorted(pairs),
    'authority':'MODEL_RUNTIME_NUMERICAL_OWNER_NOT_CANONICAL_NODE_GEOLOGY','energy_or_area_weights_present':False,
    'geometry_mapping_blocker':'owner IDs are not physical area/heat-capacity integration weights; no lateral boundary/thin-shell binding',
    'units':meta['units'],'nullable_encoding':meta['nullable_encoding']})
 # Bind relevant actual contracts and source lines, not all unrelated historical files.
 documents=['R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json','R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json',
  'R6_T0_B_PANGAEA_LIKE_V2_OCEAN_SURFACE_CLOSURE.json','R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json',
  'R6_T0_B_PANGAEA_LIKE_V2_RUNTIME_BINDING_AND_INPUT_READJUDICATION.json','R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json',
  'R6_PRE_ORBDATA_THERMAL_REFERENCE_COLUMN_CONTRACT.json','src/arcana_worldsim/r6/initial_world/grid.py',
  'src/arcana_worldsim/r6/initial_world/materialize.py','src/arcana_worldsim/r6/geological_surface_microdomain.py',
  'src/arcana_worldsim/r6/hydrology_surface_coupling.py','src/arcana_worldsim/r6/regional_geological_evolution.py',
  'src/arcana_worldsim/r6/functional_development.py','src/arcana_worldsim/r6/pre_orbdata_t0_initializer.py']
 for n in documents:auth(repo/n)
 rows=list(csv.DictReader((p0/'INPUT_CATALOG.csv').open()))
 for row in rows:
  if row['reference'].startswith('E0/'):
   auth(row['path'],row['sha256'])
 e0=json.loads(Path(next(x['path'] for x in rows if x['reference']=='E0/RESULT.json')).read_text());case=next(x for x in e0['cases'] if x['case_id']=='UNCoupled_reference')
 cols=[]
 for name,payload in case['state_initial'].items():
  cols.append({'support':name,'time_s':payload.get('time_s'),'nodes':len(payload['temperature_k']),'temperature_K_range':[min(payload['temperature_k']),max(payload['temperature_k'])],
    'z_m_range':[min(payload['z_m']),max(payload['z_m'])],'fields':list(payload),'cover_field_present':any('cover' in k for k in payload)})
 # Map only source fields having actual semantics. No mapped array is passed to R1.
 geo=next(x for x in payloads if x['role']=='INITIAL_GEOGRAPHY_1DEG');v2=next(x for x in payloads if x['role']=='PANGAEA_V2_SURFACE_CLOSED_T0')
 mappings=[];target_lat=np.linspace(-90,90,17);target_lon=np.linspace(-180,180,33);source_lat=np.linspace(-90,90,181);source_lon=np.linspace(-180,180,361)
 for version,pp,key,maskkey in [('initial',geo['path'],'land_surface_elevation_m','elevation_support_mask'),('surface_closed_v2',v2['path'],'total_surface_elevation_m','unknown_total_ocean_elevation_mask')]:
  with np.load(pp,allow_pickle=False) as z:
   values=z[key];known=z[maskkey].astype(bool) if version=='initial' else ~z[maskkey].astype(bool)
   if (known&~np.isfinite(values)).any():raise ValueError('NONFINITE_ON_KNOWN_SUPPORT')
   data=remap(values,known,source_lat,source_lon,target_lat,target_lon,6371000.)
   extras={}
   if version=='initial':
    uncertainty=remap(np.asarray(z['synthetic_uncertainty_mask'],dtype=float),known,source_lat,source_lon,target_lat,target_lon,6371000.)
    extras['source_design_uncertainty_known_subarea_fraction']=uncertainty['mean_over_known_subarea']
  fields={k:v for k,v in data.items() if isinstance(v,np.ndarray)};np.savez(a.output/(version+'_32x16.npz'),**fields,**extras,lat_edges_deg=target_lat,lon_edges_deg=target_lon)
  # Largest complete-land square <=4 cells is a location preview, NOT a wrapped numerical subdomain.
  complete=~data['has_UNKNOWN'];region=None
  if version=='initial':
   for size in [4,3,2,1]:
    found=False
    for row in range(17-size):
     for col in range(33-size):
      if complete[row:row+size,col:col+size].all():
       region={'target_row_start':row,'target_col_start':col,'shape':[size,size],'latitude_bounds_deg':[float(target_lat[row]),float(target_lat[row+size])],
        'longitude_bounds_deg':[float(target_lon[col]),float(target_lon[col+size])],'meaning':'DATA_LOCATION_PREVIEW_ONLY; no regional boundary or cropped R1 operator assumed'};found=True;break
     if found:break
    if found:break
  admission=admit_cover('surface_elevation','m',None,None,complete,None,None)
  mappings.append({'version':version,'source_field':key,'quantity':'surface_elevation_not_mobile_cover','unit':'m relative to R6 datum','epoch_Ma':210,
    'grid':'32x16 SOUTH_TO_NORTH/WEST_TO_EAST spherical R6371000','source_representation':'piecewise constant source pixel values for remapping; not claimed original continuum cell means',
    'cells':512,'full_known_cells':int(complete.sum()),'cells_intersecting_UNKNOWN':int(data['has_UNKNOWN'].sum()),
    'source_known_area_fraction':data['source_known_area_m2']/(4*math.pi*6371000.**2),
    'relative_discrete_elevation_area_integral_residual':data['relative_discrete_integral_residual'],
    'interpretation':'conserved discrete area-elevation integral, NOT conserved sediment volume/mass',
    'region_preview':region,'R1_readiness':admission})
  assert not admission['admitted'] and abs(data['relative_discrete_integral_residual'])<2e-14
 tests=unit_checks();result={'status':'BLOCKED_R1_PHYSICAL_EVOLUTION_MOBILE_COVER_AND_DIFFUSIVITY_UNAVAILABLE','actual_inventory':inventory,'E0_columns':cols,'mappings':mappings,
  'adapter_synthetic_unit_checks':tests,'physical_evolution_steps':0,'R1_solver_imports_or_calls':0,'thermal_or_coupled_evolution_calls':0,
  'physical_missing':['source-bound mobile-cover thickness/stock','surface-process diffusivity and its physical law/units/range','substrate/terrain gradient and boundary/support interpretation'],
  'density':'not necessary for volume-only R1; needed only for material mass/energy interpretation; crust/mantle density is not mobile-cover density',
  'physical_scope_authority':'existing model-derived T0 inputs, not Earth observations; source-rich does not equal compatible with R1 scalar mobile cover',
  'wall_s':time.perf_counter()-start,'cpu_user_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime-u0.ru_utime,
  'cpu_system_s':resource.getrusage(resource.RUSAGE_SELF).ru_stime-u0.ru_stime,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 (a.output/'RESULT.json').write_text(json.dumps(result,indent=2));(a.output/'INPUT_IDENTITY.json').write_text(json.dumps(inputs,indent=2))
 assert all(sha(p)==d['sha256'] for p,d in inputs.items())
 print(json.dumps({'status':result['status'],'mappings':mappings,'wall_s':result['wall_s'],'peak_rss_kib':result['peak_rss_kib']},indent=2))
if __name__=='__main__':main()
