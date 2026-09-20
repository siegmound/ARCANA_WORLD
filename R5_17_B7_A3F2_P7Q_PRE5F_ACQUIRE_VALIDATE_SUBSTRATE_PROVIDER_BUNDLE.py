from __future__ import annotations
import datetime as dt, hashlib, json, os, re, zipfile, ssl, subprocess, sys, importlib.metadata
from pathlib import Path
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parent/'_ARCANA_EXTERNAL_SOURCES/p7q_parent_state/PRE5F_SUBSTRATE_PROVIDER_BUNDLE'
SBASE='https://files.isric.org/soilgrids/former/2017-03-10/data/'
SHANG=['BDRICM_M_250m_ll.tif','BDRLOG_M_250m_ll.tif','BDTICM_M_250m_ll.tif']
PEL='https://data.ornldaac.earthdata.nasa.gov/protected/bundle/Global_Soil_Regolith_Sediment_1304.zip'
PEL_SIZE=944551751
EXPECTED={'BDTICM_M_250m_ll.tif':8480439859,'BDRICM_M_250m_ll.tif':1443918663,'BDRLOG_M_250m_ll.tif':2599020881}
def earthdata_args():
 home=Path(os.environ.get('USERPROFILE',str(Path.home())))
 netrc=Path(os.environ.get('EARTHDATA_NETRC',str(home/'_netrc')))
 cookies=Path(os.environ.get('EARTHDATA_COOKIE_JAR',str(home/'.urs_cookies')))
 if not netrc.exists() or not cookies.exists(): return []
 return ['--netrc-file',str(netrc),'--cookie',str(cookies),'--cookie-jar',str(cookies),'--max-redirs','10']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def curl_probe(url):
 try:
  p=subprocess.run(['curl.exe','--location','--fail','--show-error','--head',url],capture_output=True,text=True,timeout=60)
  return {'transport':'curl.exe','returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-2000:],'success':p.returncode==0}
 except Exception as e: return {'transport':'curl.exe','success':False,'error':type(e).__name__}
def range_probe(url,outdir):
 outdir.mkdir(parents=True,exist_ok=True); body=outdir/'BDRICM_range_1MiB.bin'; hdr=outdir/'BDRICM_range_headers.txt'
 cmd=['curl.exe','--location','--fail','--show-error','--range','0-1048575','--max-filesize','2097152','--connect-timeout','30','--max-time','180','--dump-header',str(hdr),'--output',str(body),'--write-out','http=%{http_code};version=%{http_version};final=%{url_effective};size=%{size_download};speed=%{speed_download};dns=%{time_namelookup};connect=%{time_connect};appconnect=%{time_appconnect};start=%{time_starttransfer};total=%{time_total};remote=%{remote_ip};redirects=%{num_redirects}\n',url]
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=220); raw=body.read_bytes() if body.exists() else b''; h=hdr.read_text(errors='replace') if hdr.exists() else ''; magic=raw[:4] in (b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+') ; return {'transport':'curl.exe','command_class':'range_1MiB','returncode':p.returncode,'stderr':p.stderr[-2000:],'write_out':p.stdout.strip(),'headers':h[-8000:],'bytes_received':len(raw),'magic_hex':raw[:8].hex(),'tiff_magic':magic,'success':p.returncode==0 and len(raw)==1048576 and magic}
 except Exception as e: return {'transport':'curl.exe','command_class':'range_1MiB','success':False,'error':type(e).__name__}
def tiff_signature(p):
 try:
  return p.open('rb').read(4) in (b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+')
 except OSError: return False
def download(url,dst,expected_size=None,require_tiff=False):
 if dst.exists() and dst.stat().st_size and (expected_size is None or (dst.stat().st_size==expected_size and (not require_tiff or tiff_signature(dst)))): return {'status':'REUSED_VALIDATED_OR_UNSIZED','bytes':dst.stat().st_size}
 part=dst.with_suffix(dst.suffix+'.part')
 def accepted():
  if not part.exists() or part.stat().st_size == 0: return False
  if expected_size is not None and part.stat().st_size != expected_size: return False
  return not require_tiff or tiff_signature(part)
 if not part.exists():
  try:
   with requests.get(url,stream=True,timeout=60,allow_redirects=True) as r:
    if r.status_code in (401,403): return {'status':'AUTHENTICATION_REQUIRED','http_status':r.status_code}
    if r.status_code!=200: return {'status':'HTTP_ERROR','http_status':r.status_code}
    with part.open('wb') as f:
     for b in r.iter_content(4<<20):
      if b: f.write(b)
   if accepted(): return {'status':'DOWNLOAD_COMPLETE_UNVALIDATED','transport':'python','bytes':part.stat().st_size}
   return {'status':'PAYLOAD_INTEGRITY_FAILURE','bytes':part.stat().st_size if part.exists() else 0,'expected_bytes':expected_size}
  except requests.exceptions.SSLError:
   pass
  except requests.RequestException as e:
   return {'status':'HTTP_OR_TRANSPORT_ERROR','error':type(e).__name__}
 try:
  attempts=[]
  if expected_size is not None:
   chunk=256<<20; checkpoint=part.with_suffix(part.suffix+'.checkpoint.json')
   part.parent.mkdir(parents=True,exist_ok=True)
   if not part.exists(): part.touch()
   try: checkpoint_records=json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else []
   except Exception: checkpoint_records=[]
   while part.stat().st_size < expected_size:
    start=part.stat().st_size; end=min(expected_size-1,start+chunk-1); seg=part.with_suffix(part.suffix+'.segment'); hdr=seg.with_suffix(seg.suffix+'.headers')
    if seg.exists(): seg.unlink()
    if hdr.exists(): hdr.unlink()
    args=['curl.exe','--http1.1','--location','--fail','--show-error','--retry','10','--retry-delay','5','--retry-all-errors','--connect-timeout','30','--range',f'{start}-{end}','--dump-header',str(hdr),'--output',str(seg),'--write-out','http=%{http_code};version=%{http_version};size=%{size_download};speed=%{speed_download};dns=%{time_namelookup};connect=%{time_connect};appconnect=%{time_appconnect};start=%{time_starttransfer};total=%{time_total};remote=%{remote_ip};redirects=%{num_redirects}\n',url]
    if url == PEL: args[3:3] = earthdata_args()
    p=subprocess.run(args,capture_output=True,text=True,timeout=1800)
    got=seg.stat().st_size if seg.exists() else 0; hs=hdr.read_text(errors='replace') if hdr.exists() else ''
    attempt={'start':start,'end':end,'returncode':p.returncode,'stderr':p.stderr[-2000:],'write_out':p.stdout.strip(),'bytes':got,'content_range':next((x.strip() for x in hs.splitlines() if x.lower().startswith('content-range:')),None)}; attempts.append(attempt)
    if p.returncode!=0 or got!=(end-start+1) or not attempt['content_range'] or f'bytes {start}-{end}/{expected_size}' not in attempt['content_range']:
     return {'status':'PAYLOAD_TRANSFER_FAILURE','transport':'curl.exe','curl_segments':attempts,'bytes':part.stat().st_size if part.exists() else 0,'expected_bytes':expected_size}
    part_before=part.stat().st_size; chunk_hash=sha(seg)
    with part.open('ab') as out, seg.open('rb') as src:
     for b in iter(lambda:src.read(4<<20),b''): out.write(b)
    part_after=part.stat().st_size
    checkpoint_records.append({'chunk_index':len(checkpoint_records),'range_start':start,'range_end':end,'range_bytes':got,'http_status':p.stdout.strip().split(';')[0] if p.stdout.strip() else None,'content_range':attempt['content_range'],'curl_exit_code':p.returncode,'write_out':p.stdout.strip(),'chunk_sha256':chunk_hash,'part_size_before':part_before,'part_size_after':part_after,'timestamp_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'APPENDED_VERIFIED'})
    checkpoint.write_text(json.dumps(checkpoint_records,indent=2)+'\n',encoding='utf-8')
    seg.unlink(missing_ok=True); hdr.unlink(missing_ok=True)
  if accepted(): return {'status':'DOWNLOAD_COMPLETE_UNVALIDATED','transport':'curl.exe','bytes':part.stat().st_size,'curl_segments':attempts}
  return {'status':'PAYLOAD_INTEGRITY_FAILURE','transport':'curl.exe','curl_segments':attempts,'bytes':part.stat().st_size if part.exists() else 0,'expected_bytes':expected_size}
  args=['curl.exe','--http1.1','--location','--fail','--show-error','--retry','10','--retry-delay','5','--retry-all-errors','--connect-timeout','30','--continue-at','-','--output',str(part),'--write-out','http=%{http_code};version=%{http_version};size=%{size_download};speed=%{speed_download};dns=%{time_namelookup};connect=%{time_connect};appconnect=%{time_appconnect};start=%{time_starttransfer};total=%{time_total};remote=%{remote_ip};redirects=%{num_redirects}\n',url]
  p=subprocess.run(args,capture_output=True,text=True,timeout=3600)
  attempt={'returncode':p.returncode,'stderr':p.stderr[-2000:],'write_out':p.stdout.strip(),'bytes':part.stat().st_size if part.exists() else 0}
  if accepted(): part.replace(dst); return {'status':'DOWNLOAD_SUCCESS','transport':'curl.exe','bytes':dst.stat().st_size,'curl':attempt}
  return {'status':'PAYLOAD_TRANSFER_FAILURE','transport':'python+curl','python_error':'SSLError','curl':attempt,'bytes':part.stat().st_size if part.exists() else 0,'expected_bytes':expected_size}
 except subprocess.TimeoutExpired as e:
  return {'status':'PAYLOAD_TRANSFER_FAILURE','transport':'curl.exe','error':'TIMEOUT','bytes':part.stat().st_size if part.exists() else 0,'expected_bytes':expected_size}
 except Exception as e: return {'status':'PAYLOAD_TRANSFER_FAILURE','transport':'curl.exe','error':type(e).__name__,'bytes':part.stat().st_size if part.exists() else 0,'expected_bytes':expected_size}
def tiff_meta(p):
 d={'bytes':p.stat().st_size,'sha256':sha(p),'path':str(p),'read_status':'READ_FAILED','validation_status':'FAILED'}
 try:
  Image.MAX_IMAGE_PIXELS=None
  with Image.open(p) as im:
   d.update({'driver':'PIL_TIFF_READER','dimensions':[im.width,im.height],'band_count':getattr(im,'n_frames',1),'dtype':str(im.mode),'compression':str(im.info.get('compression','UNKNOWN')),'read_status':'METADATA_READ'})
  d['validation_status']='METADATA_VALIDATED'
 except Exception as e: d['error']=type(e).__name__
 return d
def pelletier_validate_and_extract(part, archive, root):
 out={'archive_bytes':part.stat().st_size,'archive_sha256':sha(part),'zip_magic':False,'central_directory_valid':False,'crc_integrity_pass':False,'safe_extraction_pass':False,'entry_count':0,'total_uncompressed_bytes':0,'extracted_file_count':0,'products':{}}
 with part.open('rb') as f: out['zip_magic']=f.read(4)==b'PK\x03\x04'
 if not out['zip_magic'] or not zipfile.is_zipfile(part): return out
 ex=root/'extracted'; ex.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(part) as z:
  infos=sorted(z.infolist(),key=lambda x:x.filename); out['entry_count']=len(infos); out['central_directory_valid']=True; out['total_uncompressed_bytes']=sum(i.file_size for i in infos)
  bad=z.testzip(); out['crc_integrity_pass']=bad is None
  for i in infos:
   n=i.filename.replace('\\','/'); q=Path(n)
   if q.is_absolute() or '..' in q.parts or q.drive: raise ValueError('UNSAFE_ARCHIVE_MEMBER')
   if i.is_dir(): continue
   target=ex/q; target.parent.mkdir(parents=True,exist_ok=True)
   with z.open(i) as src, target.open('wb') as dst:
    for b in iter(lambda:src.read(4<<20),b''): dst.write(b)
   out['extracted_file_count']+=1
  products={}
  for p in sorted(x for x in ex.rglob('*') if x.is_file() and x.suffix.lower()=='.tif'):
   low=p.name.lower()
   key='SOIL_THICKNESS' if 'soil_thickness' in low else 'INTACT_REGOLITH_THICKNESS' if 'regolith_thickness' in low else 'SEDIMENTARY_DEPOSIT_THICKNESS' if 'sedimentary_deposit_thickness' in low else None
   if key and key not in products:
    Image.MAX_IMAGE_PIXELS=None
    with Image.open(p) as im:
     scale=im.tag_v2.get(33550); tie=im.tag_v2.get(33922); crs='EPSG:4326' if 34735 in im.tag_v2 and 34737 in im.tag_v2 else 'NOT_REPORTED'; resolution=[float(scale[0]),float(scale[1])] if scale else 'NOT_REPORTED'; extent=[float(tie[3]),float(tie[4])-float(scale[1])*im.height,float(tie[3])+float(scale[0])*im.width,float(tie[4])] if scale and tie else 'NOT_REPORTED'; nodata=im.tag_v2.get(42113,'NOT_REPORTED')
     meta={'filename':str(p.relative_to(ex)).replace('\\','/'),'semantic_variable':key,'units':'NOT_REPORTED','dimensions':[im.width,im.height],'band_count':getattr(im,'n_frames',1),'CRS':crs,'resolution':resolution,'extent':extent,'dtype':str(im.mode),'nodata':str(nodata),'scale_offset':'NOT_REPORTED','bytes':p.stat().st_size,'sha256':sha(p),'read_status':'RASTER_METADATA_READ'}
    products[key]=meta
  out['products']=products; out['safe_extraction_pass']=True
 if part != archive: part.replace(archive)
 out['archive_status']='ACQUIRED_VALIDATED'; return out
def main():
 stamp=dt.datetime.now(dt.timezone.utc).isoformat(); shdir=CACHE/'SHANGGUAN_DTB_2017'; raw=shdir/'raw'; meta=shdir/'metadata'; raw.mkdir(parents=True,exist_ok=True); meta.mkdir(exist_ok=True)
 xml_url=SBASE+'BDRICM_M_250m_ll.tif.xml'; diag={'stage':'R5.17-B7-A3F2-P7Q-PRE5F','attempt_1':{'transport':'Python HTTPS client','shangguan':'SSLError','pelletier':'SSLError','payload_acquired':False,'interpretation':'CLIENT_TLS_TRANSPORT_FAILURE'},'python':{'version':sys.version,'openssl':ssl.OPENSSL_VERSION,'requests':importlib.metadata.version('requests'),'urllib3':importlib.metadata.version('urllib3'),'certifi':importlib.metadata.version('certifi'),'certifi_ca_bundle':__import__('certifi').where(),'ssl_default_verify_paths':{k:str(getattr(ssl.get_default_verify_paths(),k)) for k in ('cafile','capath','openssl_cafile','openssl_capath')},'environment':{k:os.environ.get(k) for k in ('SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE') if os.environ.get(k)}},'isric_xml':{'url':xml_url,'python_probe':None,'curl_probe':curl_probe(xml_url)},'pelletier_probe':curl_probe(PEL)}
 try:
  with requests.get(xml_url,stream=True,timeout=30) as q: diag['isric_xml']['python_probe']={'status':q.status_code,'final_url':q.url,'content_length':q.headers.get('Content-Length')}
 except Exception as e: diag['isric_xml']['python_probe']={'error':type(e).__name__}
 try: diag['curl_version']=subprocess.run(['curl.exe','--version'],capture_output=True,text=True,timeout=20).stdout
 except Exception as e: diag['curl_version']=type(e).__name__
 diag['isric_range_probe']=range_probe(SBASE+'BDRICM_M_250m_ll.tif',meta/'transport_probe')
 if not diag['isric_range_probe'].get('success'): os.environ['PRE5F_DIAGNOSTIC_ONLY']='1'
 (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_TRANSPORT_DIAGNOSTICS.json').write_text(json.dumps(diag,indent=2)+'\n',encoding='utf-8')
 sh=[]
 for name in SHANG:
  p=raw/name; part=p.with_suffix(p.suffix+'.part'); outcome=({'status':'EXISTING_CANDIDATE','bytes':p.stat().st_size} if p.exists() else {'status':'PARTIAL_PRESERVED','bytes':part.stat().st_size if part.exists() else 0}) if os.environ.get('PRE5F_DIAGNOSTIC_ONLY')=='1' else download(SBASE+name,p,EXPECTED[name],True)
  if outcome.get('status')=='DOWNLOAD_COMPLETE_UNVALIDATED' and part.exists():
   checked=tiff_meta(part); outcome['metadata_validation']=checked
   if checked.get('validation_status')=='METADATA_VALIDATED': part.replace(p); outcome['status']='ACQUIRED_VALIDATED'
   else: outcome['status']='PAYLOAD_VALIDATION_FAILURE'
  entry={'provider_id':'SHANGGUAN_DTB_2017','source_url':SBASE+name,'retrieval_timestamp_utc':stamp,'original_filename':name,'expected_source_index_size':EXPECTED[name],'acquisition':outcome}
  if p.exists(): entry.update(tiff_meta(p)); entry['semantic_variable']={'BDTICM_M_250m_ll.tif':'absolute depth to bedrock','BDRICM_M_250m_ll.tif':'censored depth to bedrock ~0-200 cm','BDRLOG_M_250m_ll.tif':'R-horizon occurrence/probability ~200 cm'}[name]; entry['units']='cm' if name!='BDRLOG_M_250m_ll.tif' else 'provider metadata required; no normalization'; entry['temporal_semantics']='GEOLOGICAL_PRESENT'; entry['source_role']='DERIVED_STRUCTURAL_EVIDENCE / EXPOSURE_LIKELIHOOD_EVIDENCE';
  sh.append(entry)
  x=raw/(name+'.xml'); xo=download(SBASE+name+'.xml',x); (meta/(name+'.xml.json')).write_text(json.dumps({'source_url':SBASE+name+'.xml','outcome':xo,'sha256':sha(x) if x.exists() else None},indent=2)+'\n')
  if not (p.exists() and entry.get('validation_status')=='METADATA_VALIDATED'):
   break
 pelldir=CACHE/'PELLETIER_ORNL_DAAC_1304'; (pelldir/'raw').mkdir(parents=True,exist_ok=True); pp=pelldir/'raw/Global_Soil_Regolith_Sediment_1304.zip'; po={'status':'ENDPOINT_REACHABLE_PAYLOAD_NOT_ACQUIRED','transport':'curl.exe','authentication_required':False} if os.environ.get('PRE5F_DIAGNOSTIC_ONLY')=='1' else download(PEL,pp,PEL_SIZE); pellet={'provider_id':'PELLETIER_ORNL_DAAC_1304','source_url':PEL,'retrieval_timestamp_utc':stamp,'archive':{'path':str(pp),'outcome':po,'bytes':pp.stat().st_size if pp.exists() else None,'sha256':sha(pp) if pp.exists() else None},'validation_status':po['status'],'identified_variables':[]}
 ppart=pp.with_suffix(pp.suffix+'.part')
 if po.get('status') in ('DOWNLOAD_COMPLETE_UNVALIDATED','REUSED_VALIDATED_OR_UNSIZED') and (ppart.exists() or pp.exists()):
  try:
   candidate=ppart if ppart.exists() else pp; pv=pelletier_validate_and_extract(candidate,pp,pelldir); pellet['archive'].update(pv); pellet['validation_status']='ACQUIRED_VALIDATED' if pv.get('archive_status')=='ACQUIRED_VALIDATED' and pv.get('crc_integrity_pass') and pv.get('safe_extraction_pass') else 'PAYLOAD_VALIDATION_FAILURE'; pellet['identified_variables']=sorted(pv.get('products',{})); pellet['products']=pv.get('products',{})
  except Exception as e: pellet['validation_status']='PAYLOAD_VALIDATION_FAILURE'; pellet['archive']['validation_error']=type(e).__name__
 glim=ROOT.parent/'_ARCANA_EXTERNAL_SOURCES/p7q_parent_state/GLIM_V1/v1.0/raw/hartmann-moosdorf_2012.zip'; glimv={'provider_id':'GLIM_V1','path':str(glim),'bytes':glim.stat().st_size if glim.exists() else None,'sha256':sha(glim) if glim.exists() else None,'expected_sha256':'43b4ce3276b155d804db8ff9fb227d620b4c35015a4cf564eac4d06d2b69d88e','role':'SURFACE_LITHOLOGY_CONDITIONER_ONLY','validation_status':'LOCAL_CACHE_REUSED_VALIDATED' if glim.exists() and sha(glim)=='43b4ce3276b155d804db8ff9fb227d620b4c35015a4cf564eac4d06d2b69d88e' else 'LOCAL_CACHE_REUSED_FAILED'}
 inventory={'stage':'R5.17-B7-A3F2-P7Q-PRE5F','shangguan':sh,'pelletier':pellet,'glim':glimv,'classified_cells':0,'bedrock_exposed_assigned':0,'residual_regolith_assigned':0,'saprolite_assigned':0,'crosswalk_performed':False,'thresholds_defined':False,'external_payload_acquired':False}
 shok=all(x.get('validation_status')=='METADATA_VALIDATED' for x in sh); pelok=pellet['validation_status']=='ACQUIRED_VALIDATED' and bool(pellet.get('identified_variables')); bundle=shok and pelok and glimv['validation_status']=='LOCAL_CACHE_REUSED_VALIDATED'
 inventory['SHANGGUAN_COMPLETE']=shok; inventory['PELLETIER_COMPLETE']=pelok; inventory['SUBSTRATE_PROVIDER_BUNDLE_COMPLETE']=bundle
 (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_ACQUIRED_PAYLOAD_INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n'); (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_SHANGGUAN_VALIDATION.json').write_text(json.dumps({'provider_id':'SHANGGUAN_DTB_2017','files':sh,'complete':shok,'encoding_note':'BDRLOG encoding must be read from official metadata; no normalization performed.'},indent=2)+'\n'); (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_PELLETIER_VALIDATION.json').write_text(json.dumps(pellet,indent=2)+'\n'); (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_GLIM_CACHE_VALIDATION.json').write_text(json.dumps(glimv,indent=2)+'\n'); (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_PROVIDER_DEPENDENCY_RECONCILIATION.json').write_text(json.dumps({'stage':'R5.17-B7-A3F2-P7Q-PRE5F','shangguan_covariates':['GLiM lithology','topography','remote sensing','climate/land-surface covariates'],'pelletier_role':'related structural evidence / thickness provider','independent_vote_rule':'Do not count dependent providers as independent evidence votes.','classification_performed':False},indent=2)+'\n')
 remote_unavailable=any(x.get('acquisition',{}).get('status')=='REMOTE_PROVIDER_UNAVAILABLE' for x in sh) or pellet['validation_status']=='REMOTE_PROVIDER_UNAVAILABLE'
 auth_blocked=pellet['validation_status']=='AUTHENTICATION_REQUIRED'
 tls_blocked=any(x.get('acquisition',{}).get('status') in ('LOCAL_TLS_TRUST_FAILURE','CLIENT_TLS_STACK_FAILURE','HTTP_OR_TRANSPORT_ERROR','PAYLOAD_TRANSFER_FAILURE') for x in sh) or pellet['validation_status'] in ('LOCAL_TLS_TRUST_FAILURE','CLIENT_TLS_STACK_FAILURE','HTTP_OR_TRANSPORT_ERROR','ENDPOINT_REACHABLE_PAYLOAD_NOT_ACQUIRED')
 incomplete=any(x.get('acquisition',{}).get('status') in ('PARTIAL_PRESERVED','PAYLOAD_TRANSFER_FAILURE','PAYLOAD_VALIDATION_FAILURE') for x in sh)
 decision='AUTHORIZE_P7Q_PRE5G_SUBSTRATE_PROVIDER_SOURCE_CONTRACT_AND_GRID_ALIGNMENT_GATE' if bundle else 'BLOCKED_P7Q_PRE5F_PELLETIER_AUTHENTICATION_REQUIRED' if auth_blocked else 'BLOCKED_P7Q_PRE5F_PROVIDER_SOURCE_UNAVAILABLE' if remote_unavailable else 'BLOCKED_P7Q_PRE5F_ACQUISITION_INCOMPLETE' if tls_blocked or incomplete else 'BLOCKED_P7Q_PRE5F_PROVIDER_PAYLOAD_VALIDATION_FAILED'
 verdict='PASS_P7Q_PRE5F_SUBSTRATE_PROVIDER_BUNDLE_ACQUISITION_VALIDATED' if bundle else 'BLOCKED_P7Q_PRE5F_ACQUISITION_INCOMPLETE'
 adj={'stage':'R5.17-B7-A3F2-P7Q-PRE5F','decision':decision,'verdict':verdict,'inventory':inventory,'p7q_reopened':False,'canonical_parent_created':False,'physical_soil_created':False,'new_simulation':False,'scientific_authority_register_mutated':False,'canonical_maturity':'L1_SOURCE_BOUND_PARTIAL','prototype_maturity':'L2_STATIC_STATE_CANDIDATE_PARTIAL'}
 (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_ADJUDICATION.json').write_text(json.dumps(adj,indent=2)+'\n'); (ROOT/'R5_17_B7_A3F2_P7Q_PRE5F_ADJUDICATION.md').write_text(f'# R5.17-B7-A3F2-P7Q-PRE5F\n\nAcquisition/validation only. Classified cells: `0`. Crosswalk: `false`. Thresholds: `false`.\n\nDecision: `{decision}`\n\nVerdict: `{verdict}`\n',encoding='utf-8'); print(json.dumps(adj,indent=2))
if __name__=='__main__': main()
