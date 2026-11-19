"""Read-only archive experiment and CLI. Never calls the thermal step function."""
from pathlib import Path
import argparse,json,time,shutil,statistics,resource,copy,subprocess,sys
from geo import *
from adapter import dump
BASE=REPO.parent
PREVIOUS=BASE/'ARCANA_WORLD_EVIDENCE/R6/MULTI_COLUMN_THERMAL_SCHEDULER_20261102_01'
WORLD=[-90.,90.,-180.,180.]

def hashes(root):return {str(p.relative_to(root)):sha(p) for p in Path(root).rglob('*') if p.is_file()}
def cleaned(q):
 q=copy.deepcopy(q);q.pop('query_s',None);q.pop('cache',None);return q

def open_geo(root,cat,budget=786432):return GeoReader(root,sha(Path(root)/'PLAN.json'),cat,sha(cat),budget)

def campaign(out):
 out.mkdir();start=time.perf_counter();dump(out/'CATALOG.json',make_catalog());cat=out/'CATALOG.json';catalog=json.loads(cat.read_text());tests=[];results={};orig={};copies={}
 assert catalog['cells']['C028']['bounds_south_north_west_east_deg']==[1.,2.,-152.,-151.]
 assert catalog['cells']['C139']['cell_center_lat_lon_deg']==[-76.5,-40.5]
 # Source-supported numerical owner, deliberately NOT an assumed FEG-node coordinate.
 assert 'NOT_CANONICAL' in catalog['cells']['C028']['binding_semantics']
 tests.append('original_grid_convention_and_PRE_owner')
 for count in (5,48):
  old=PREVIOUS/'run02'/str(count)/'direct';root=out/str(count);orig[count]=hashes(old);shutil.copytree(old,root);copies[count]=hashes(root);assert copies[count]==orig[count]
  bench={};examples={}
  for name,region in [('C028',[1,2,-152,-151]),('C139',[-77,-76,-41,-40]),('both',WORLD)]:
   t=time.perf_counter()
   with open_geo(root,cat) as g:
    opened=time.perf_counter()-t;q=g.query(region,564);cold=q['query_s'];assert q['status']=='AVAILABLE';warm=[]
    for _ in range(3):
     w=g.query(region,564);warm.append(w['query_s']);assert cleaned(w)==cleaned(q)
    bench[name]=dict(open_s=opened,cold_query_s=cold,warm_query_s=warm,warm_median_s=statistics.median(warm),cache=g.reader.cache_report())
    examples[name]=q
    for k,answer in q['columns'].items():
     ref=thaw_json(g.reader.by_step[564].value)['columns'][k];native=g.reader.sessions[k].restore(ref['state_id']);assert thermal.digest(native)==answer['native_sha256'];assert len(native['T_hi_K'])==len(native['T_correction_K'])==545
     assert answer['geographic_binding']['column_id']==answer['column']
   expected=2 if name=='both' else 1;assert len(q['columns'])==expected
  # Same states and temperatures as the already executed scheduler query.
  baseline=json.loads((PREVIOUS/'run02'/str(count)/'QUERY_EXAMPLE.json').read_text())
  for k,q in examples['both']['columns'].items():
   assert q['state_id']==baseline['columns'][k]['state_id'] and q['nodes']==baseline['columns'][k]['nodes']
  with open_geo(root,cat) as g:
   cases={
    'outside':(g.query([0,1,0,1],564),'NOT_SIMULATED'),
    'seam':(g.query([-90,90,170,-170],564),'NOT_SIMULATED'),
    'boundary_only':(g.query([2,3,-152,-151],564),'NOT_SIMULATED'),
    'unarchived':(g.query(WORLD,1),'TIME_NOT_ARCHIVED'),
    'unknown_process':(g.query(WORLD,564,process='HYDROLOGY'),'UNKNOWN'),
    'unknown_depth':(g.query([1,2,-152,-151],564,80001,80002),'UNKNOWN'),
    'no_nodes':(g.query([1,2,-152,-151],564,.1,.9),'AVAILABLE')}
   for name,(q,status) in cases.items():assert q['status']==status,(name,q);tests.append(str(count)+'_'+name)
   assert cases['no_nodes'][0]['columns']['C028']['status']=='NO_STORED_NODES_IN_INTERVAL'
   partial=g.query([1,2,-152,-151],564,79999,80001);assert partial['columns']['C028']['unknown_depth_intervals_m']==[[80000.,80001]]
   # Stored T0 and Moho values are selected, never reconstructed.
   t0=g.query(WORLD,0,0,0);assert all(x['nodes'][0]['temperature_K_display']==280 for x in t0['columns'].values())
   mh=g.query([1,2,-152,-151],564,27900,28100);assert [x['depth_m'] for x in mh['columns']['C028']['nodes']]==[28000.]
   dump(out/(str(count)+'_STATUS_EXAMPLES.json'),{k:q for k,(q,_) in cases.items()})
  dump(out/(str(count)+'_GEOGRAPHIC_QUERY.json'),examples)
  assert hashes(root)==copies[count];results[str(count)]=bench
 # Genuine earlier read-views from the previous interrupted execution; alter pointers on COPIES only.
 p=out/'incomplete48';shutil.copytree(PREVIOUS/'run02/48/split',p);old=json.loads((PREVIOUS/'run02/48/INCOMPLETE_AND_RECOVERY.json').read_text());pointers={}
 for key in ['epochs','columns/C028/history','columns/C139/history']:
  vdir=p/key/'.history_visibility';current=vdir/'CURRENT.json';pointers[current]=current.read_text()
  if key=='epochs':vid=old['partial']['epoch_registry_view']
  else:
   k=key.split('/')[1];wanted=set(old['initial_column_ids'][k]);matches=[]
   for f in (vdir/'views').glob('*.json'):
    if set(json.loads(f.read_text())['records']['states'])==wanted:matches.append(f.stem)
   assert len(matches)==1;vid=matches[0]
  current.write_text(json.dumps(dict(schema='ARCANA_R6_COMMITTED_READ_VIEW_V1',view_id=vid)))
 with open_geo(p,cat) as g:
  q=g.query(WORLD,288);assert q['status']=='EPOCH_INCOMPLETE';dump(out/'INCOMPLETE_QUERY.json',q)
  before=g.reader.view.view_id
  for f,txt in pointers.items():f.write_text(txt)
  assert g.query(WORLD,288)['status']=='EPOCH_INCOMPLETE' and g.reader.view.view_id==before
  assert g.refresh();q=g.query(WORLD,288);assert q['status']=='AVAILABLE';dump(out/'REFRESHED_QUERY.json',q)
 tests+=['authentic_incomplete_epoch','pinned_view_ignores_new_head','refresh_sees_complete_epoch']
 # Shared epoch/source/static/corruption guards remain effective behind geography filtering.
 negatives=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,FileNotFoundError) as e:negatives.append(dict(case=name,error_type=type(e).__name__,reason=str(e)))
  else:raise AssertionError('NEGATIVE_ACCEPTED:'+name)
 with open_geo(out/'5',cat) as g:
  for name,region in [('latitude',[-91,90,-180,180]),('empty',[0,0,0,1]),('longitude',[0,1,-181,0])]:reject(name,lambda r=region:g.query(r,564))
  reject('fractional_step',lambda:g.query(WORLD,1.5));reject('depth_order',lambda:g.query(WORLD,564,10,0))
  g.query(WORLD,564)
  rec=g.reader.by_step[564];ref=thaw_json(rec.value)['columns']['C028'];f=out/'5/columns/C028/history/states'/(ref['state_id']+'.json');saved=f.read_bytes()
  try:
   f.write_bytes(saved.replace(b'280.0',b'281.0',1));assert f.read_bytes()!=saved
   reject('warm_corrupt_dynamic',lambda:g.query(WORLD,564))
  finally:f.write_bytes(saved)
 with open_geo(out/'5',cat) as g:
  g.query(WORLD,564);rec=g.reader.by_step[564];f=out/'5/epochs/states'/(str(rec.state_id)+'.json');saved=f.read_bytes()
  try:f.write_bytes(saved+b'!');reject('warm_corrupt_epoch',lambda:g.query(WORLD,564))
  finally:f.write_bytes(saved)
 bad=copy.deepcopy(catalog);bad['cells']['C028']['bounds_south_north_west_east_deg'][0]=0;dump(out/'BAD_CATALOG.json',bad)
 reject('wrong_geographic_binding_even_with_new_SHA',lambda:open_geo(out/'5',out/'BAD_CATALOG.json'))
 reject('wrong_catalog_SHA',lambda:GeoReader(out/'5',sha(out/'5/PLAN.json'),cat,'0'*64))
 reject('wrong_plan_SHA',lambda:GeoReader(out/'5','0'*64,cat,sha(cat)))
 # No retention/state mutation or new evolution: compare every byte of the archive copies.
 for count in (5,48):assert hashes(out/str(count))==copies[count] and hashes(PREVIOUS/'run02'/str(count)/'direct')==orig[count]
 dump(out/'NEGATIVE_TESTS.json',negatives)
 # Independent Python CLI reads the same saved native state; no child continuation.
 argv=[sys.executable,str(Path(__file__).resolve()),'query','--root',str(out/'48'),'--plan-sha',sha(out/'48/PLAN.json'),'--catalog',str(cat),'--catalog-sha',sha(cat),'--step','564','--region','1','2','-152','-151','--depth','0','8']
 t=time.perf_counter();cp=subprocess.run(argv,check=True,capture_output=True,text=True);child=time.perf_counter()-t;q=json.loads(cp.stdout);assert cleaned(q)==cleaned(json.loads((out/'48_GEOGRAPHIC_QUERY.json').read_text())['C028']);dump(out/'CLI_QUERY.json',q);dump(out/'CLI_INVOCATION.json',dict(argv=argv,wall_s=child))
 dump(out/'RESULT.json',dict(marker='GEO_TEMPORAL_THERMAL_EXPLORE=PASS_OWNER_CELL_BOUND_HISTORY_QUERIES',benchmarks=results,checks=tests,negative_count=len(negatives),new_physical_steps=0,archive_bytes_unchanged=True,independent_cli_identical=True,wall_s=time.perf_counter()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 print('PASS',time.perf_counter()-start,flush=True)

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True);p=sp.add_parser('campaign');p.add_argument('--output',type=Path,required=True)
 p=sp.add_parser('query');p.add_argument('--root',type=Path,required=True);p.add_argument('--plan-sha',required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--catalog-sha',required=True);p.add_argument('--step',type=int,required=True);p.add_argument('--region',nargs=4,type=float,required=True,metavar=('S','N','W','E'));p.add_argument('--depth',nargs=2,type=float,default=[0,8]);p.add_argument('--process',default='THERMAL_1D')
 args=ap.parse_args()
 if args.mode=='campaign':campaign(args.output)
 else:
  with GeoReader(args.root,args.plan_sha,args.catalog,args.catalog_sha) as g:print(json.dumps(g.query(args.region,args.step,*args.depth,args.process),indent=2,allow_nan=False))
if __name__=='__main__':main()
