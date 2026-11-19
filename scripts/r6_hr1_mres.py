#!/usr/bin/env python3
"""HR1-MRES: synthetic array/storage workload, NEVER global physical evolution."""
import argparse
from collections import defaultdict
from contextlib import contextmanager
import hashlib,json,math,os,resource,struct,sys,time,zlib
from pathlib import Path
import numpy as np
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.state import DomainStateEnvelope,TimeSupport,SpatialSupport,SupportClass,AuthorityClass
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.identity import HistoryId,BranchId,content_hash,thaw_json

SCHEMA='ARCANA_R6_HR1_MRES_SYNTHETIC_ARRAY_V1'
TIERS=[('Preview',256,128),('SD',512,256),('480eq',854,427),('720eq',1280,640),('FullHDeq',1920,960),('2K',2048,1024)]
TILE=128;RADIUS=6371000.;SECONDS_PER_YEAR=31557600

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
def file_sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(path,v):
    with Path(path).open('xb') as f:f.write(canonical(v)+b'\n');f.flush();os.fsync(f.fileno())
def require(v,msg):
    if not v:raise ValueError(msg)
def rss():
    s=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    return {k:s[k].strip() for k in ['VmRSS','VmHWM','Threads']}
def cpu():
    r=resource.getrusage(resource.RUSAGE_SELF);return r.ru_utime,r.ru_stime
def disk(root):
    paths=[p for p in Path(root).rglob('*') if p.is_file()]
    return {'files':len(paths),'logical_bytes':sum(p.stat().st_size for p in paths),'allocated_bytes':sum(p.stat().st_blocks*512 for p in paths)}

def config(width,height,years,payload=64,event_period=10000):
    require(type(width) is int and type(height) is int and width==2*height and height>1,'GRID_MUST_BE_2_TO_1')
    require(type(years) is int and years>0,'YEARS_INVALID')
    require(payload in (64,256,1024) and event_period>0,'PROFILE_INVALID')
    return {'schema':SCHEMA,'width':width,'height':height,'years':years,'payload_bytes':payload,
        'fields':payload//8,'dtype':'<f8','order':'C_CELL_FIELD','tile_edge':TILE,'compression':'byte_shuffle_then_zlib_level1',
        'changed_cell_fraction':1.0,'event_period_cells':event_period,'event_timestamp_null_policy':'alternating_event_ordinal',
        'checkpoint_interval_years':10,'journal_fsync_interval_years':1,'external_step_years':1,
        'seconds_per_model_year':SECONDS_PER_YEAR,'radius_m':RADIUS,'scope':'SYNTHETIC_WORKLOAD_ONLY',
        'field_units':'dimensionless_counter_fixture','physical_state_fields':'ABSENT_UNAVAILABLE_NOT_ZERO',
        'mask_bytes_per_cell':1,'mask_semantics':'bit0 synthetic-valid;bit1 south pole row;bit2 north pole row;bit3 west seam;bit4 east seam'}

def geometry(cfg):
    w,h=cfg['width'],cfg['height'];bounds=np.linspace(-math.pi/2,math.pi/2,h+1,dtype=np.float64)
    areas=RADIUS**2*(2*math.pi/w)*np.diff(np.sin(bounds))
    total=float(areas.sum()*w);sphere=4*math.pi*RADIUS**2
    require(np.all(areas>0) and math.isclose(total,sphere,rel_tol=5e-15),'SPHERICAL_AREA_CLOSURE')
    return {'radius_m':RADIUS,'longitude_bounds_deg':[-180.,180.],'latitude_bounds_deg':[-90.,90.],
        'row_order':'south_to_north','column_order':'west_to_east_periodic','delta_lon_deg':360/w,'delta_lat_deg':180/h,
        'row_cell_areas_m2':areas.tolist(),'total_area_m2':total,'analytic_sphere_area_m2':sphere,'area_residual_m2':total-sphere,
        'equatorial_angular_scale_m':RADIUS*2*math.pi/w,
        'polar_policy':'latitude faces stop at poles; zero-length polar face; no latitude wrap; no physical flux operator',
        'row_col_cell_id':'global_cell_id=row*width+column','crs':'EPSG:4326 coordinate semantics, spherical metric'}

def neighbors(row,col,width,height):
    require(0<=row<height and 0<=col<width,'CELL_OUT_OF_RANGE')
    return tuple([(row,(col-1)%width),(row,(col+1)%width)]+([(row-1,col)] if row else [])+([(row+1,col)] if row+1<height else []))

def tiles(cfg):
    for r in range(0,cfg['height'],TILE):
        for c in range(0,cfg['width'],TILE):yield r,c,min(TILE,cfg['height']-r),min(TILE,cfg['width']-c)

def expected_tile(cfg,r,c,nr,nc,year):
    # Independent integer construction: exact dyadic closed form, no physical units.
    ids=(np.arange(r,r+nr,dtype=np.uint64)[:,None]*cfg['width']+np.arange(c,c+nc,dtype=np.uint64)).reshape(-1,1)
    fields=np.arange(cfg['fields'],dtype=np.uint64)[None,:]
    numerator=ids+fields*np.uint64(16384)+np.uint64(year)*(fields+np.uint64(1))
    return numerator.astype('<f8')/1048576.

def masks(cfg):
    result=np.ones((cfg['height'],cfg['width']),dtype=np.uint8)
    result[0,:]|=2;result[-1,:]|=4;result[:,0]|=8;result[:,-1]|=16
    return result

def source_identity():
    root=Path(__file__).resolve().parents[1]
    names=[Path(__file__).resolve(),*[root/'src/arcana_worldsim/r6'/n for n in ['store.py','state.py','identity.py','checkpoint.py','read_view.py']]]
    return {'schema':SCHEMA,'sources':{str(p.relative_to(root)):file_sha(p) for p in names if p.is_file()},
        'numpy':np.__version__,'zlib':zlib.ZLIB_RUNTIME_VERSION,'python':sys.version.split()[0]}

@contextmanager
def timed(costs,key):
    tick=time.perf_counter()
    try:yield
    finally:costs[key]+=time.perf_counter()-tick

def encode_tile(values,mask,costs):
    with timed(costs,'serialization_shuffle_s'):
        flat=np.ascontiguousarray(values,dtype='<f8').reshape(-1,values.shape[-1])
        n=flat.shape[0];bpc=flat.shape[1]*8
        packed=np.empty((n,bpc+1),dtype=np.uint8);packed[:,:bpc]=flat.view(np.uint8).reshape(n,bpc);packed[:,bpc]=np.asarray(mask).reshape(-1)
        raw=packed.tobytes();shuffled=packed.T.copy().tobytes()
    with timed(costs,'raw_hash_s'):raw_sha=hashlib.sha256(raw).hexdigest()
    with timed(costs,'compression_s'):compressed=zlib.compress(shuffled,1)
    with timed(costs,'compressed_hash_s'):compressed_sha=hashlib.sha256(compressed).hexdigest()
    return compressed,raw_sha,compressed_sha,len(raw)

def decode_tile(blob,meta,fields):
    require(hashlib.sha256(blob).hexdigest()==meta['compressed_sha256'],'COMPRESSED_TILE_CORRUPT')
    shuffled=zlib.decompress(blob);n=meta['rows']*meta['columns'];bpc=fields*8
    require(len(shuffled)==n*(bpc+1),'TILE_LENGTH_INVALID')
    packed=np.frombuffer(shuffled,dtype=np.uint8).reshape(bpc+1,n).T.copy()
    require(hashlib.sha256(packed.tobytes()).hexdigest()==meta['raw_sha256'],'RAW_TILE_CORRUPT')
    values=np.ascontiguousarray(packed[:,:bpc]).view('<f8').reshape(meta['rows'],meta['columns'],fields)
    return values,packed[:,bpc].reshape(meta['rows'],meta['columns']).copy()

class Workload:
    def __init__(self,root,cfg,*,resume=False,fault=None):
        self.root=Path(root);self.cfg=cfg;self.source=source_identity();self.fault=fault
        self.history_id=str(HistoryId.from_payload({'hr1':cfg,'source':self.source}))
        self.branch_id=str(BranchId.from_payload({'history':self.history_id}))
        self.state=None;self.year=0;self.parent=None;self.last_head='0'*64;self.pending=[];self.commits=[]
        self.costs=defaultdict(float);self.total_bytes=defaultdict(int)
        if resume:
            require(self.root.is_dir() and json.loads((self.root/'CONFIG.json').read_bytes())==cfg,'RESUME_CONFIG_MISMATCH')
        else:
            self.root.mkdir(parents=True,exist_ok=False)
            (self.root/'years').mkdir();save(self.root/'CONFIG.json',cfg);save(self.root/'SOURCE.json',self.source);save(self.root/'GEOMETRY.json',geometry(cfg))
        require(json.loads((self.root/'SOURCE.json').read_bytes())==self.source,'RESUME_SOURCE_MISMATCH')
        self.store=HistoryStore(self.root/'b0',_fault_injector=fault)
        with self.store.read_view() as view:self.parent_view=view.view_id
        self.mask=masks(cfg)
        if not resume:
            with timed(self.costs,'array_initialization_s'):
                self.state=np.empty((cfg['height'],cfg['width'],cfg['fields']),dtype='<f8')
                for r,c,nr,nc in tiles(cfg):self.state[r:r+nr,c:c+nc]=expected_tile(cfg,r,c,nr,nc,0).reshape(nr,nc,cfg['fields'])
            self.write_year();self.publish()
        else:
            reader=Reader(root,cfg);reader.verify_prefix()
            self.year=reader.year;self.state=reader.load(self.year)
            self.last_head=reader.descriptors[self.year]['committed_head']
            self.parent=reader.checkpoint_ids[self.year];self.parent_view=reader.view_id

    def write_year(self):
        cfg=self.cfg;y=self.year;stem=f'{y:04d}';data_path=self.root/'years'/(stem+'.bin')
        index_path=self.root/'years'/(stem+'.index.jsonl');events_path=self.root/'years'/(stem+'.events.jsonl')
        metadata=[];stream_sha=hashlib.sha256();idx_sha=hashlib.sha256();events_sha=hashlib.sha256();raw_bytes=0;compressed_bytes=0
        with data_path.open('xb') as data,index_path.open('xb') as index:
            for r,c,nr,nc in tiles(cfg):
                compressed,raw_sha,compressed_sha,raw_n=encode_tile(self.state[r:r+nr,c:c+nc],self.mask[r:r+nr,c:c+nc],self.costs)
                with timed(self.costs,'tile_index_metadata_s'):
                    row={'schema':SCHEMA,'year':y,'row':r,'column':c,'rows':nr,'columns':nc,
                        'offset':data.tell(),'length':len(compressed),'raw_bytes':raw_n,'raw_sha256':raw_sha,'compressed_sha256':compressed_sha}
                    line=canonical(row)+b'\n';metadata.append(row)
                with timed(self.costs,'write_stream_hash_s'):
                    data.write(compressed);stream_sha.update(compressed);index.write(line);idx_sha.update(line)
                raw_bytes+=raw_n;compressed_bytes+=len(compressed)
            with timed(self.costs,'journal_fsync_s'):
                for f in (data,index):f.flush();os.fsync(f.fileno())
        with timed(self.costs,'event_generation_serialization_s'):
            ids=np.arange(y%cfg['event_period_cells'],cfg['width']*cfg['height'],cfg['event_period_cells'],dtype=np.uint64) if y else np.empty(0,dtype=np.uint64)
            event_lines=[canonical({'schema':SCHEMA,'event_id':f'HR1:{cfg["width"]}x{cfg["height"]}:Y{y}:C{int(cell)}',
                'kind':'SYNTHETIC_COUNTER_EVENT','global_cell_id':int(cell),'context_year':y,
                'time_year':None if j%2==0 else y,'scope':'SYNTHETIC_WORKLOAD_ONLY'})+b'\n' for j,cell in enumerate(ids)]
        with events_path.open('xb') as events:
            with timed(self.costs,'event_write_hash_s'):
                for line in event_lines:events.write(line);events_sha.update(line)
            with timed(self.costs,'journal_fsync_s'):events.flush();os.fsync(events.fileno())
        with timed(self.costs,'journal_fsync_s'):HistoryStore._fsync_directory(data_path.parent)
        body={'schema':SCHEMA,'year':y,'time_end_s':y*SECONDS_PER_YEAR,'parent_head':self.last_head,
            'data_sha256':stream_sha.hexdigest(),'index_sha256':idx_sha.hexdigest(),'events_sha256':events_sha.hexdigest(),
            'tiles':len(metadata),'events':len(ids),'null_events':(len(ids)+1)//2,'array_payload_bytes':cfg['width']*cfg['height']*cfg['payload_bytes'],
            'raw_bytes_with_mask':raw_bytes,'compressed_bytes':compressed_bytes}
        self.last_head=digest(body);descriptor={**body,'head':self.last_head}
        with timed(self.costs,'year_descriptor_s'):
            save(self.root/'years'/(stem+'.json'),descriptor)
            HistoryStore._fsync_directory(data_path.parent)
        self.pending.append(descriptor)
        for key in ['array_payload_bytes','raw_bytes_with_mask','compressed_bytes','events','null_events']:self.total_bytes[key]+=body[key]
        return descriptor

    def advance(self):
        require(self.state is not None and self.year<self.cfg['years'],'ADVANCE_OUT_OF_RANGE')
        with timed(self.costs,'synthetic_array_update_s'):
            # Stateful real array work. It is not temperature, mass, climate or any physical law.
            self.state+=(np.arange(1,self.cfg['fields']+1,dtype='<f8')/1048576.)
        self.year+=1
        return self.write_year()

    def publish(self):
        require(self.pending,'NO_PENDING_JOURNAL');started=time.perf_counter()
        descriptor={'schema':SCHEMA,'scope':'SYNTHETIC_WORKLOAD_ONLY','year':self.year,
            'year_descriptor_sha256':file_sha(self.root/'years'/f'{self.year:04d}.json'),
            'committed_head':self.last_head,'first_pending_year':self.pending[0]['year'],'last_pending_year':self.year,
            'parent_checkpoint_id':self.parent,'config_sha256':digest(self.cfg),'source':self.source,
            'pending_descriptors_sha256':digest(self.pending),'grid_cells':self.cfg['width']*self.cfg['height']}
        with timed(self.costs,'checkpoint_metadata_s'):
            state=DomainStateEnvelope.create(history_id=self.history_id,branch_id=self.branch_id,domain='HR1_MRES_SYNTHETIC_ARRAY_RESTART',
                time_support=TimeSupport(f'YEAR_{self.year}','SYNTHETIC_MODEL_YEARS'),
                spatial_support=SpatialSupport(f'HR1_{self.cfg["width"]}x{self.cfg["height"]}',selector_kind='GLOBAL'),
                support_class=SupportClass.FIXTURE_ONLY,authority_class=AuthorityClass.FIXTURE_ONLY,value=descriptor)
            cp=CheckpointEnvelope.create(history_id=self.history_id,branch_id=self.branch_id,time_key=f'YEAR_{self.year}',
                restart_state_ids=(str(state.state_id),),retained_history_state_ids=(str(state.state_id),),runtime_identity=self.source,
                configuration=self.cfg,seed_lineage={'kind':'DETERMINISTIC_DYADIC_COUNTER_FIXTURE_NOT_PHYSICS'},parent_checkpoint_id=self.parent,
                output_manifest={'descriptor_sha256':content_hash(descriptor)},restart_compatibility={'schema':SCHEMA})
        with timed(self.costs,'b0_atomic_publication_s'):
            self.store.append_transaction((state,cp),expected_parent_view_id=self.parent_view)
        self.parent=str(cp.checkpoint_id)
        with self.store.read_view() as view:self.parent_view=view.view_id
        self.pending=[];self.commits.append({'year':self.year,'total_s':time.perf_counter()-started,'checkpoint_id':self.parent})
        return cp

class Reader:
    def __init__(self,root,cfg):
        self.root=Path(root);self.cfg=cfg;self.source=source_identity()
        require(json.loads((self.root/'CONFIG.json').read_bytes())==cfg,'READER_CONFIG_MISMATCH')
        require(json.loads((self.root/'SOURCE.json').read_bytes())==self.source,'READER_SOURCE_MISMATCH')
        self.store=HistoryStore(self.root/'b0');self.descriptors={};self.checkpoint_ids={};self.tile_cache={};self.index_cache={}
        with self.store.read_view() as view:
            self.view_id=view.view_id;cps=self.store.checkpoints()
            require(cps,'NO_COMMITTED_CHECKPOINT')
            parents={cp.parent_checkpoint_id for cp in cps};leaves=[cp for cp in cps if str(cp.checkpoint_id) not in parents]
            require(len(leaves)==1,'AMBIGUOUS_CHECKPOINT_LINEAGE')
            mapping={str(cp.checkpoint_id):cp for cp in cps};cp=leaves[0];seen=set()
            while cp is not None:
                require(str(cp.checkpoint_id) not in seen,'CYCLIC_LINEAGE');seen.add(str(cp.checkpoint_id))
                require(dict(cp.runtime_identity)==self.source and cp.configuration_sha256==content_hash(cfg),'CHECKPOINT_SOURCE_CONFIG_MISMATCH')
                require(len(cp.restart_state_ids)==1,'CHECKPOINT_DESCRIPTOR_INVALID')
                value=thaw_json(self.store.read_state(cp.restart_state_ids[0]).value)
                require(value['parent_checkpoint_id']==cp.parent_checkpoint_id and value['config_sha256']==digest(cfg)
                    and value['source']==self.source and thaw_json(cp.output_manifest)=={'descriptor_sha256':content_hash(value)},'CHECKPOINT_BINDING_MISMATCH')
                self.descriptors[value['year']]=value
                self.checkpoint_ids[value['year']]=str(cp.checkpoint_id)
                if cp.parent_checkpoint_id is not None:
                    require(cp.parent_checkpoint_id in mapping,'MISSING_PARENT_CHECKPOINT')
                    cp=mapping[cp.parent_checkpoint_id]
                else:cp=None
            require(len(seen)==len(cps),'DISCONNECTED_LINEAGE')
        self.year=max(self.descriptors)

    def verify_prefix(self):
        head='0'*64;pending=[];total_events=null_events=0
        for year in range(self.year+1):
            p=self.root/'years'/f'{year:04d}.json';row=json.loads(p.read_bytes());body={k:v for k,v in row.items() if k!='head'}
            require(row['year']==year and row['parent_head']==head and digest(body)==row['head'],'JOURNAL_CHAIN_INVALID')
            stem=f'{year:04d}'
            for suffix,key in [('bin','data_sha256'),('index.jsonl','index_sha256'),('events.jsonl','events_sha256')]:
                require(file_sha(self.root/'years'/(stem+'.'+suffix))==row[key],'COMMITTED_FILE_CORRUPT')
            with (self.root/'years'/(stem+'.events.jsonl')).open('rb') as f:
                events=[json.loads(line) for line in f]
            require(len(events)==row['events'] and sum(e['time_year'] is None for e in events)==row['null_events'],'EVENT_COUNT_OR_NULL_MISMATCH')
            for j,e in enumerate(events):
                require(e['context_year']==year and e['time_year']==(None if j%2==0 else year)
                    and e['kind']=='SYNTHETIC_COUNTER_EVENT' and e['scope']=='SYNTHETIC_WORKLOAD_ONLY','EVENT_SEMANTICS_CHANGED')
                expected_cell=year%self.cfg['event_period_cells']+j*self.cfg['event_period_cells']
                require(e['global_cell_id']==expected_cell and e['event_id']==f'HR1:{self.cfg["width"]}x{self.cfg["height"]}:Y{year}:C{expected_cell}',
                        'EVENT_IDENTITY_CHANGED')
            total_events+=len(events);null_events+=row['null_events'];pending.append(row);head=row['head']
            if year in self.descriptors:
                cp=self.descriptors[year]
                require(cp['committed_head']==head and cp['year_descriptor_sha256']==file_sha(p)
                    and cp['first_pending_year']==pending[0]['year'] and cp['pending_descriptors_sha256']==digest(pending),'COMMITTED_PAIR_HIGH_WATER_INVALID')
                pending=[]
        require(not pending,'UNCOMMITTED_PREFIX_SELECTED')
        return {'years':self.year,'head':head,'events':total_events,'null_events':null_events,'paired_checkpoints':len(self.descriptors)}

    def index(self,year):
        require(0<=year<=self.year,'QUERY_UNCOMMITTED_YEAR')
        if year not in self.index_cache:
            p=self.root/'years'/f'{year:04d}.index.jsonl'
            descriptor=json.loads((self.root/'years'/f'{year:04d}.json').read_bytes())
            require(file_sha(p)==descriptor['index_sha256'],'QUERY_INDEX_CORRUPT')
            self.index_cache[year]=[json.loads(line) for line in p.open('rb')]
        return self.index_cache[year]

    def tile(self,year,meta,*,cached=False):
        key=(year,meta['row'],meta['column'])
        if cached and key in self.tile_cache:return self.tile_cache[key]
        with (self.root/'years'/f'{year:04d}.bin').open('rb') as f:f.seek(meta['offset']);blob=f.read(meta['length'])
        values,mask=decode_tile(blob,meta,self.cfg['fields'])
        if cached:self.tile_cache={key:(values,mask)}
        return values,mask

    def point(self,year,row,col,*,cached=False):
        require(0<=row<self.cfg['height'] and 0<=col<self.cfg['width'],'QUERY_CELL_INVALID')
        meta=next(v for v in self.index(year) if v['row']<=row<v['row']+v['rows'] and v['column']<=col<v['column']+v['columns'])
        values,mask=self.tile(year,meta,cached=cached)
        return values[row-meta['row'],col-meta['column']].copy(),int(mask[row-meta['row'],col-meta['column']])

    def load(self,year,*,validate_expected=True):
        state=np.empty((self.cfg['height'],self.cfg['width'],self.cfg['fields']),dtype='<f8')
        seen=np.zeros((self.cfg['height'],self.cfg['width']),dtype=np.uint8);expected_mask=masks(self.cfg)
        for meta in self.index(year):
            r,c,nr,nc=(meta[k] for k in ['row','column','rows','columns']);values,mask=self.tile(year,meta)
            require(not seen[r:r+nr,c:c+nc].any(),'TILE_OVERLAP')
            require(np.array_equal(mask,expected_mask[r:r+nr,c:c+nc]),'MASK_CHANGED')
            if validate_expected:require(np.array_equal(values.reshape(-1,self.cfg['fields']),expected_tile(self.cfg,r,c,nr,nc,year)),'SYNTHETIC_VALUES_CHANGED')
            state[r:r+nr,c:c+nc]=values;seen[r:r+nr,c:c+nc]=1
        require(seen.all(),'TILE_COVERAGE_MISSING');return state

def run(root,cfg):
    started=time.perf_counter();u0=cpu();work=Workload(root,cfg);initialization=time.perf_counter()-started
    annual=[]
    with (Path(root)/'ANNUAL.jsonl').open('xb') as f:
        for _ in range(cfg['years']):
            tick=time.perf_counter();c0=cpu();before=dict(work.costs);row=work.advance()
            if work.year%cfg['checkpoint_interval_years']==0 or work.year==cfg['years']:work.publish()
            c1=cpu();sample={'year':work.year,'wall_s':time.perf_counter()-tick,'cpu_user_s':c1[0]-c0[0],'cpu_system_s':c1[1]-c0[1],
                'phases_s':{k:v-before.get(k,0) for k,v in work.costs.items()},'memory':rss(),'events':row['events'],
                'null_events':row['null_events'],'raw_array_payload_bytes':row['array_payload_bytes'],'compressed_bytes':row['compressed_bytes']}
            f.write(canonical(sample)+b'\n');f.flush();annual.append(sample)
            if work.year in (1,10,100,1000):print('PROGRESS',cfg['width'],cfg['height'],cfg['payload_bytes'],work.year,flush=True)
    c1=cpu();result={'status':'PASS_SYNTHETIC_WORKLOAD_ONLY','configuration':cfg,'initialization_s':initialization,
        'wall_pre_receipt_s':time.perf_counter()-started,'cpu_user_s':c1[0]-u0[0],'cpu_system_s':c1[1]-u0[1],
        'phases_s':dict(work.costs),'total_written_including_t0':dict(work.total_bytes),'memory':rss(),
        'commits':work.commits,'disk_pre_receipt':disk(root),'physical_advances':0,'synthetic_cell_years':cfg['width']*cfg['height']*cfg['years']}
    save(Path(root)/'RESULT.json',result);return result

def probe(root,cfg):
    started=time.perf_counter();u0=cpu();tick=time.perf_counter();reader=Reader(root,cfg);reopen=time.perf_counter()-tick
    tick=time.perf_counter();integrity=reader.verify_prefix();integrity_s=time.perf_counter()-tick
    y=reader.year;r,c=cfg['height']//2,cfg['width']//2
    tick=time.perf_counter();current=reader.load(y);full_cold=time.perf_counter()-tick;del current
    tick=time.perf_counter();current=reader.load(y);full_warm=time.perf_counter()-tick;del current
    tick=time.perf_counter();point,mask=reader.point(y,r,c,cached=True);point_cold=time.perf_counter()-tick
    expected=expected_tile(cfg,r,c,1,1,y)[0];require(np.array_equal(point,expected),'POINT_QUERY_MISMATCH')
    tick=time.perf_counter();again,_=reader.point(y,r,c,cached=True);point_warm=time.perf_counter()-tick;require(np.array_equal(point,again),'WARM_POINT_CHANGED')
    historical_queries=[]
    for year in sorted({0,y//2,y}):
        for row,col in [(0,0),(r,c),(cfg['height']-1,cfg['width']-1)]:
            actual,valid=reader.point(year,row,col)
            require(np.array_equal(actual,expected_tile(cfg,row,col,1,1,year)[0]),'HISTORICAL_POINT_MISMATCH')
            historical_queries.append({'year':year,'row':row,'column':col,'value_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),'mask':valid})
    # Restore an actual preceding B0 snapshot, advance one synthetic increment,
    # compare against persisted next-year arrays (never regenerate a physics model).
    prior=max(v for v in reader.descriptors if v<y)
    tick=time.perf_counter();restored=reader.load(prior);restore_s=time.perf_counter()-tick
    tick=time.perf_counter();restored+=(np.arange(1,cfg['fields']+1,dtype='<f8')/1048576.)
    for meta in reader.index(prior+1):
        a,b,nr,nc=(meta[k] for k in ['row','column','rows','columns']);values,_=reader.tile(prior+1,meta)
        require(np.array_equal(restored[a:a+nr,b:b+nc],values),'RESTART_CONTINUATION_MISMATCH')
    replay_s=time.perf_counter()-tick;del restored
    c1=cpu()
    return {'status':'PASS_EXACT_QUERY_AND_SYNTHETIC_RESTART','integrity':integrity,'reopen_b0_s':reopen,'prefix_integrity_s':integrity_s,
        'point_application_cold_s':point_cold,'point_decoded_tile_cached_s':point_warm,'full_grid_first_s':full_cold,
        'full_grid_repeat_s':full_warm,'restart_from_year':prior,'restore_arrays_s':restore_s,'next_step_compare_s':replay_s,
        'wall_pre_receipt_s':time.perf_counter()-started,'cpu_user_s':c1[0]-u0[0],'cpu_system_s':c1[1]-u0[1],'memory':rss(),
        'historical_query_witnesses':historical_queries,
        'cold_semantics':'first full-grid query in fresh process after prefix integrity, index cache initially empty; OS page cache uncontrolled; repeat full-grid redecodes; warm point alone caches one decoded tile',
        'physical_advances':0,'new_persisted_synthetic_years':0}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['run','probe'])
    p.add_argument('--root',type=Path,required=True);p.add_argument('--width',type=int,required=True);p.add_argument('--height',type=int,required=True)
    p.add_argument('--years',type=int,required=True);p.add_argument('--payload-bytes',type=int,default=64);p.add_argument('--event-period',type=int,default=10000)
    args=p.parse_args();cfg=config(args.width,args.height,args.years,args.payload_bytes,args.event_period)
    print(json.dumps(run(args.root,cfg) if args.mode=='run' else probe(args.root,cfg),sort_keys=True),flush=True)
if __name__=='__main__':main()
