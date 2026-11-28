"""Documentary-only T0/G15 source inventory. No model/trajectory execution."""
from pathlib import Path
import ast
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
import arcana_g45_distributed_amr_cbf as c


def main():
    dev=Path.cwd();sources={}
    def source(name):
        p=dev/name
        if p.exists():sources[name]={'sha256':c.sha(p),'bytes':p.stat().st_size,'authority':'SOURCE_BYTES_VERIFIED_SCOPE_SEPARATELY_ADJUDICATED'}
        else:sources[name]={'exists':False,'authority':'UNAVAILABLE_HERE_NOT_PROOF_OF_GLOBAL_ABSENCE'}
        return p
    candidates=c.read(c.EV/'R6_G43_T0_MANTLE_HANDOFF_NEW01/SOURCE_DISCOVERY.json')['filename_candidates']
    for name in candidates:source(name)
    for name in ('docs/arcana/B6K_ISOLATED_FIRST_CANDIDATE_STATE.md','outputs/r6_b6k_isolated_first_candidate_state/B6K_STATE_TRANSFER.json','outputs/r6_b6k_isolated_first_candidate_state/B6K_SYSTEM_MEMORY.json','outputs/r6_b6k_isolated_first_candidate_state/B6K_SOURCE_FREEZE.json','R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json','experiments/r6_thermo_provider_pilot_v1/arcana_g15_midpoint_coupling.py','experiments/r6_thermo_provider_pilot_v1/arcana_g30_regional_metric_regression.py','experiments/r6_thermo_provider_pilot_v1/arcana_g31_corrected_direct_csr.py'):source(name)
    b6=dev/'outputs/r6_b6k_isolated_first_candidate_state';bm=c.read(b6/'B6K_ARTIFACT_MANIFEST.json');checks=[]
    for row in bm['artifacts']:
        p=dev/row['relative_path'];checks.append({'path':row['relative_path'],'exists':p.exists(),'sha_match':p.exists() and c.sha(p)==row['sha256']})
    world=c.read(dev/'R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json');g43=c.read(c.EV/'R6_G43_T0_MANTLE_HANDOFF_NEW01/REPORT.json')
    docparents=[]
    for fragment,pin in (('G15_MIDPOINT_COUPLING_NEW01','5dc476169e04a2bc31f79addfb04ee8804209e677efa2ee4c4ce5de0edc7d619'),('G30','3298f0b7ef41083068ada52e71d62a0238a96076372625cc8fa42dd210d7cee2'),('G31','28ebbee110fa1e3e96f1842e7542deef6c26277cac9ee0ec535b3a267f9ee7fb')):
        options=[p for p in c.EV.iterdir() if p.is_dir() and fragment in p.name and (p/'MANIFEST.json').is_file() and c.sha(p/'MANIFEST.json')==pin]
        if len(options)==1:
            m=c.old.g38.verified_bundle(options[0],pin);docparents.append({'path':str(options[0]),'manifest_sha256':pin,'complete_inventory_verified':True,'members':len(m['files'])})
        else:docparents.append({'fragment':fragment,'pin':pin,'status':'NOT_UNIQUELY_LOCATED_NO_PROMOTION'})
    g15=c.EV/'R6_THERMO_G15_MIDPOINT_COUPLING_NEW01';prior=c.read(g15/'G15_REPORT.json');index=c.read(g15/'ACCEPTED_CHECKPOINT_INDEX.json');policy=c.read(g15/'POLICY.json')
    constants={}
    tree=ast.parse((dev/'experiments/r6_thermo_provider_pilot_v1/arcana_g15_midpoint_coupling.py').read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for name in node.targets:
                if isinstance(name,ast.Name) and name.id in ('START','TARGET','MAX_TRIALS','MAX_SOLVES','MIN_STEP','G14_PIN','CP_PIN'):constants[name.id]=ast.literal_eval(node.value)
    fields=[
      {'field':'outer geometry/radius and surface gravity','status':'SOURCE_BOUND_DESIGN_BASELINE','source':'R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json#/planetary_constants','available':world['planetary_constants'],'gap':'surface gravity is not a radial gravity/mass profile; outer radius does not determine CMB'},
      {'field':'CMB/core geometry and deep interfaces','status':'UNBOUND_FOR_MANTLE_INITIALIZER','value':None,'gap':'author/source-bound internal geometry required; Earth CMB cannot be adopted from shell analogy'},
      {'field':'thermal state','status':'CONDITIONAL_SHALLOW_SUPPORT_ONLY','source':'G43_REPORT.audit','available':g43['audit'],'gap':'0–300km PRE-derived support, nearly radial under LAB; no admitted full-mantle 3D convective state'},
      {'field':'composition/water/redox/phases/EOS','status':'UNSELECTED_OR_UNBOUND_SPATIAL_AUTHORITY','source':'m01_mantle_experimental_design_candidate_v1.json','value':None,'gap':'terrestrial DM reference and M01 design are not ARCANA assignments; authorial selection null, engine executions authorized0'},
      {'field':'pressure','status':'ABSOLUTE_REFERENCE_UNBOUND','value':None,'gap':'source delta-P must not be relabeled absolute pressure; compressible EOS and reference/gauge consistency required'},
      {'field':'rheology','status':'DOMAIN_AND_PARAMETERS_NOT_BOUND_FULL_MANTLE','value':None,'gap':'source-supported viscosity/compressibility/phase/water/stress dependence with applicability/uncertainty; no invented default'},
      {'field':'boundary flux/core coupling/heating','status':'UNBOUND_FOR_FULL_MANTLE','value':None,'gap':'core/top thermal conditions, basal/internal/radiogenic flux budgets and mechanical coupling source-bound'},
      {'field':'initial velocity/3D perturbation/spin-up','status':'GENERATION_CONTRACT_REQUIRED','value':None,'gap':'initialization/seed/statistics and relaxation budgets require explicit source/author authority; no prescribed static mantle or invented anomalies'},
      {'field':'B6K interior candidate','status':'GEOMETRY_ONLY_ISOLATED_CANDIDATE_NOT_MANTLE_STATE','source':'outputs/r6_b6k_isolated_first_candidate_state/B6K_INTERIOR_CANDIDATE.json','available':c.read(b6/'B6K_INTERIOR_CANDIDATE.json'),'gap':'INTERIOR means plate-interior support; no T/composition/pressure/velocity volume. Field transfer retains reference/asynchronous/UNKNOWN; canonical publication false'},
      {'field':'uncertainty/masks/anchors','status':'PRESERVE_SOURCE_MASKS_NO_IMPUTATION','value':None,'gap':'D12 exclusions, mixed/unknown source masks;12anchors/CHA-1/H0 and source validity/lineage must constrain any future initialization'}]
    report={'status':'DOCUMENTARY_DESIGN_ONLY_NO_PHYSICAL_ASSIGNMENT','screen_pass':True,'scope':'bounded adjudication of cited G43 discovery and B6K/G15 sources, not exhaustive proof that no other authority exists','source_files':sources,'B6K_artifact_checks':checks,'documentary_parent_inventories':docparents,'mantle_T0_authorities':fields,
      'G15':{'original_constants':constants,'original_policy':policy,'accepted_index':index,'original_report':prior,'corrected_trajectory_qualified':False,'new_G15_runs':0,
        'future_requalification':['Recover original T0 and accepted temporal partition through162yr; retain original uncorrected verdict as historical engineering evidence','Rebuild isolated corrected slopey/sinA FB2 band and CSR from G30/G31 verified sources, no arbitrary RHS/torque correction','Do not promote old wrong-metric112yr/162yr checkpoint to corrected initial state; replay corrected chain from earliest unaffected authoritative state','Compare corrected band/CSR on matched time grids, one step/two halves and additional refinement; independently calibrated norms and budgets before new runs','Same-process and fresh-process restart with complete geometry/material/thermal/stress/dissipation/gauge/clock/source identities; preserve predictor exclusion from accepted energy ledger','Mass/energy/heat and stress/dissipation feedback, D12 ridge/contact masks and event horizon; no long/global run without explicit separate authorization']},
      'WORLD_HISTORY':{'target':'210Ma->0ka including late200ka','domains':['geometry/lithology','natural resources','climate/hydrology/soils','Deep','flora','fauna','populations/settlements/civilizations'],'constraints':['12anchors','CHA-1/H0','500GB provisional','causal checkpoints/states/events/provenance','region/time/process queries','derived refinement branch with restart/convergence/endpoint uncertainty'],'Physical_T1':'milestone only'},**c.SCOPE}
    c.write(c.ROOT/'T0_G15_AUTHORITY_INVENTORY.json',report)
    lines=['# G45 — inventario documentale T0 completo e G15 corretto','', 'Nessuna nuova assegnazione, esecuzione M01 o traiettoria G15. Fonti lette direttamente e hash conservati nel JSON omonimo; inventario circoscritto alle fonti citate, non prova di assenza globale.','','| Famiglia | Autorità verificata / limite |','|---|---|']
    for row in fields:lines.append('| '+row['field']+' | '+row['status']+': '+row['gap']+' |')
    lines+=['','B6K_INTERIOR_CANDIDATE riguarda geometria plate-local e supporti di nodi, non un volume termochimico mantellare. Il trasferimento B6K esegue soltanto geometria Euler; SYSTEM_MEMORY e UNKNOWN rimangono espliciti. Le costanti di superficie dichiarate nel manifest iniziale sono distinte da un profilo gravitazionale e dalla geometria del nucleo.','','## Riqualificazione G15 futura','']
    lines += [str(i)+'. '+s for i,s in enumerate(report['G15']['future_requalification'],1)]
    lines +=['','G15 originale:112→162anni,6solve meccanici storici; indice e policy originali conservati senza eseguire codice di traiettoria. Il PASS originale non certifica la traiettoria corretta. G30/G31 sono regressioni di operatore/endpoint.','','## Storia completa','', 'D-024: iniziare dal minimo sottoinsieme fisicamente chiuso, poi risorse naturali e Deep, clima/idrologia/suoli, flora/fauna e popolazioni/civiltà. HistoryStore conserva causalità e query regione/epoca/processo; zoom con lineage e incertezza. Physical T1 non sostituisce WORLD_HISTORY210Ma→0ka, con attenzione agli ultimi200ka,12anchor,CHA-1/H0 e budget500GB.']
    (c.ROOT/'T0_G15_AUTHORITY_INVENTORY.md').write_text('\n'.join(lines)+'\n');print('DOCUMENTARY_INVENTORY_READY',len(sources),len(docparents),flush=True)
if __name__=='__main__':main()
