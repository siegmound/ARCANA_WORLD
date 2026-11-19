"""Source/evidence recovery for a regional physical ShellSet experiment.

Stdlib only. Does not import, launch, build, or time-step any physical provider.
A missing physical closure stays null; historical test results remain scoped.
"""
from pathlib import Path
import argparse,json,hashlib,time,resource,ast,re,copy

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();r=args.repo.resolve();o=args.output;o.mkdir();started=time.perf_counter();b=r.parent/'ARCANA_WORLD_EVIDENCE/R6';inputs={};matches=[];anchors=[]
 def read(p):
  p=Path(p);inputs[str(p)]=dict(bytes=p.stat().st_size,sha256=digest(p));return p.read_text()
 def load(p):return json.loads(read(p))
 def anchor(p,needle,context=2):
  text=read(p);lines=text.splitlines();hits=[i for i,l in enumerate(lines) if needle in l]
  assert hits,(p,needle)
  for i in hits[:3]:anchors.append(dict(path=str(p),source_sha256=inputs[str(p)]['sha256'],needle=needle,line=i+1,excerpt='\n'.join(lines[max(0,i-context):i+context+1])))
 def comparison(p,h,scope):
  read(p);matches.append(dict(path=str(p),expected_sha256=h,actual_sha256=inputs[str(p)]['sha256'],match=inputs[str(p)]['sha256']==h,scope=scope))
 shell=load(r/'R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json');models=Path(shell['evidence_files']['capacity_models']['path']);comparison(models,shell['evidence_files']['capacity_models']['sha256'],'historical upstream capacity result')
 rows=[l.split() for l in models.read_text().splitlines() if re.match(r'^\d+\s+\d+\s',l)];assert sorted(int(x[0]) for x in rows)==list(range(1,10))
 for f in shell['evidence_files'].values():comparison(Path(f['path']),f['sha256'],'historical upstream ShellSet evidence')
 orb=load(r/'R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json');orbdir=r/orb['evidence']['directory']
 for fn,h in orb['evidence']['files'].items():comparison(orbdir/fn,h,'historical OrbData input generalization')
 runtime=Path(shell['qualified_runtime']['executable']);inputs[str(runtime)]=dict(bytes=runtime.stat().st_size,sha256=digest(runtime))
 # Do not equate today's executable bytes with any historical invocation.
 runtime_observation=dict(path=str(runtime),sha256=inputs[str(runtime)]['sha256'],historical_upstream_executable_sha256=shell['qualified_runtime']['executable_sha256'],matches_historical_upstream=inputs[str(runtime)]['sha256']==shell['qualified_runtime']['executable_sha256'],invoked=False)
 pyg=load(r/'R6_PYGPLATES_STATIC_TOPOLOGY_RESOLUTION_REPORT.json');pmap=load(r/'R6_PYGPLATES_CANONICAL_MAPPING_REPORT.json');assembly=load(r/'R6_PYGPLATES_TOPOLOGY_ASSEMBLY_REPORT.json')
 g3=b/'GEODYN3C_20261028T171846Z';geodyn=load(g3/'QUALIFICATION.json');runclaims=load(g3/'RUN_IDENTITY_CLAIMS.json');compare=load(g3/'NUMERIC_COMPARISON.json')
 inv=load(b/'GEODYN_2C_SNAPSHOT_INVENTORY/20261026T234827Z_inventory/INVENTORY.json')
 a2=load(b/'GEODYN_2A_R1_FAIR_QUALIFICATION/20261027T105033Z_exact_commit/REFERENCE_COMPARISON.json')
 blank=b/'GEODYN_1F_BLANKENBACH/20261026T224533Z_case1a_ref4';assert read(blank/'RUN_EXIT_CODE.txt').strip()=='0';read(blank/'RUN_STDOUT.txt');read(blank/'INPUT_SHA256.txt');read(r/'docs/arcana/GEODYN_1G_FAIR_CLOSURE_GEODYN_2_PREPARATION.md')
 int_reports={}
 for name in ['3y_1plus2','10y_5plus5']:
  root=b/'INT10K_E2_B2_R1_FAIR_YhQ4gPTE'/name;m=load(root/'MANIFEST.json')
  for member in m['members']:
   comparison(root/member['path'],member['sha256'],'INT10K already executed '+name);assert (root/member['path']).stat().st_size==member['byte_length']
  rep=load(root/'REPORT.json');int_reports[name]={k:rep[k] for k in ['classification','status','direct_vs_split_history_equality','checkpoint_comparison','implementation_source_commit','implementation_worktree_dirty_for_measured_sources']}
 assert all(x['match'] for x in matches),[x for x in matches if not x['match']]
 kin=load(r/'R6_T0_CANONICAL_PLATE_KINEMATICS.json');law=load(r/'R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json');feg=load(r/'R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json');frame=load(r/'R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json');meta=load(r/'R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json');mat=load(r/'R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json');projection=load(r/'R6_PRE_ORBDATA_S1B_NUMERICAL_ADEQUACY.json')
 for fn in ['R6_PRE_ORBDATA_S1B_INTEGRATION_POINT_THERMAL_PROJECTION_CONTRACT.md','docs/arcana/INT0A_MULTI_PROVIDER_INTEGRATION.md','docs/arcana/B6A_POSITIVE_DURATION_KINEMATIC_AUTHORITY.md','docs/arcana/B6F_EVENT_NUMERICAL_VALIDITY_QUALIFICATION.md','docs/arcana/R6_INT10K_E0_SOURCE_AND_COUPLING_AUDIT_20261028.md','R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_CANDIDATE_B_V2.json','R6_SHELLSET_FEG_BC_CONTRACT.json','R6_PRE_ORBDATA_CHEMICAL_DENSITY_MECHANICS_AUTHORITY.json','docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json','PROJECT_LEDGER/DECISIONS.md']:
  read(r/fn)
 dat=r/'R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat';inputs[str(dat)]=dict(bytes=dat.stat().st_size,sha256=digest(dat));assert inputs[str(dat)]['sha256']==meta['runtime_data_sha256']
 fp=r/'R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg';inputs[str(fp)]=dict(bytes=fp.stat().st_size,sha256=digest(fp));assert inputs[str(fp)]['sha256']==frame['evidence']['raw_feg_sha256']
 selected=[]
 with dat.open() as f:
  next(f)
  for line in f:
   bits=line.split()
   if int(bits[0]) in [32792,32793,4823]:selected.append(dict(zip(meta['field_order'],map(float,bits))))
 assert len(selected)==3
 for path,needle in [('external/ShellSet-v1.1.0/src/MOD_Shells.f90','Computes horizontal velocity of nodes'),('external/ShellSet-v1.1.0/src/MOD_Shells.f90','CALL VBCs ('),('external/ShellSet-v1.1.0/src/MOD_Shells.f90','CALL Solver ('),('external/ShellSet-v1.1.0/src/MOD_Shells.f90','SUBROUTINE Diamnd ('),('external/ShellSet-v1.1.0/INPUT/iEarth5-049.in','aCreep'),('external/ShellSet-v1.1.0/INPUT/iEarth5-049.in','pltRef'),('src/arcana_worldsim/r6/material_rheology_provider.py','not a'),('src/arcana_worldsim/r6/material_rheology_provider.py','NOT_ASSIGNED_TO_R6_MATERIAL_ROLES'),('src/arcana_worldsim/r6/unified_multiphysics_microdomain.py','opening_rate_m_year: float = 0.01'),('src/arcana_worldsim/r6/int10k_runtime_compact.py','create_synthetic_region'),('src/arcana_worldsim/r6/functional_spatial_support.py','sides_plate_a_then_plate_b'),('src/arcana_worldsim/r6/initial_world/grid.py','southernmost')]:anchor(r/path,needle)
 inputdir=r/'external/ShellSet-v1.1.0/INPUT';bcs=[dict(path=str(p),sha256=digest(p),header=read(p).splitlines()[0]) for p in sorted(inputdir.glob('*.bcs'))]
 # An explicit missing regional assignment, not a claim that every file on HPC was searched.
 boundary_template=load(r/'R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_CANDIDATE_B_V2.json')['boundary_conditions'];assert boundary_template['artifact_path'] is None
 euler5_11=[p for p in kin['plates'] if p['plate_id'] in [5,11]]
 thermal=b/'THERMAL_CONTROLLER_EXPLORE_V3_20261102_01/run02/RESULT.json'
 # Existing archive/persistence success is reused; no old tests or histories are rerun.
 threp=read(r/'docs/arcana/R6_THERMAL_1D_HISTORY_EXPLORE_FAIR_20261102.md')
 geo=b/'GEO_TEMPORAL_THERMAL_20261103_01/run03/48_GEOGRAPHIC_QUERY.json';queries=load(geo)['both']
 capabilities=[
 dict(tool='GPlates/pyGPlates',TESTED_UPSTREAM='NOT_RECOVERED_BY_THIS_FINITE_SOURCE_AUDIT',R6_ADAPTER_TESTED='STATIC_CANONICAL_MAPPING_ONLY',R6_PHYSICAL_RUN_TESTED=False,GLOBAL_PHYSICS_READY=False,evidence=dict(static_report_decision=pyg['decision'],resolution_attempted=pyg['resolution_attempted'],resolution_succeeded=pyg['resolution_succeeded'],mapping_decision=pmap['decision'],assembly_decision=assembly['decision']),limit='Recovered records report runtime unavailable in their historical context; not a fresh environment probe and not denial of other specialist tests.'),
 dict(tool='ShellSet/SHELLS',TESTED_UPSTREAM=True,R6_ADAPTER_TESTED='T0_INPUT_CONSUMPTION_AND_SOURCE_LEVEL_S1B; NOT_FULL_REGIONAL_MECHANICS',R6_PHYSICAL_RUN_TESTED=False,GLOBAL_PHYSICS_READY=False,evidence=dict(upstream_models=len(rows),capacity=shell['qualification']['capacity_list_ex1_n10_t5'],current_binary_observation=runtime_observation),limit='Upstream Earth examples and ARCANA loading do not supply local mechanical law, BCs or transient material update.'),
 dict(tool='OrbData/PRE_ORBDATA',TESTED_UPSTREAM=True,R6_ADAPTER_TESTED=True,R6_PHYSICAL_RUN_TESTED='THERMAL_1D_ONLY; NO_MECHANICAL_REGIONAL_T1',GLOBAL_PHYSICS_READY=False,evidence=dict(input_generalization=orb['qualification'],owner_bound_nodes=meta['node_count'],material_identity=meta['material_configuration_identity']),limit='Thermal/density references complete in their scope; not composition or rheology.'),
 dict(tool='ASPECT',TESTED_UPSTREAM=True,R6_ADAPTER_TESTED='READ_ONLY_SYNTHETIC_TRAJECTORY',R6_PHYSICAL_RUN_TESTED=False,GLOBAL_PHYSICS_READY=False,evidence=dict(Blankenbach_ref4_exit=0,qualification=geodyn['status'],snapshots=inv['snapshot_count'],meshes=geodyn['numeric_mesh_sha256_comparisons'],typed_fields=geodyn['typed_field_sha256_comparisons'],last_archived_s=inv['last_snapshot_time'],solver_completion_s=inv['final_statistics_time']),limit='Synthetic Blankenbach and rigid-shear cases; no ARCANA constitutive or boundary assignment. Not required for chosen ShellSet path.'),
 dict(tool='GEODYN',TESTED_UPSTREAM='NOT_A_SEPARATE_SOLVER',R6_ADAPTER_TESTED=True,R6_PHYSICAL_RUN_TESTED=False,GLOBAL_PHYSICS_READY=False,evidence=dict(archive=geodyn['archive_id'],classification=geodyn['classification'],restart=geodyn['restart']),limit='11 saved synthetic snapshots; archive qualification does not execute mechanics or supply restart.'),
 dict(tool='INT10K',TESTED_UPSTREAM='ARCANA_ENGINEERING_OPERATORS_NOT_EXTERNAL_ENGINES',R6_ADAPTER_TESTED=True,R6_PHYSICAL_RUN_TESTED=False,GLOBAL_PHYSICS_READY=False,evidence=int_reports,limit='Real T0 columns, benchmark rheology/Maxwell and synthetic forcing/surface/Deep; ShellSet/ASPECT not invoked by this path.')]
 gaps=[
 dict(id='G1_REGIONAL_MECHANICAL_DOMAIN',status='MISSING_REGIONAL_BINDING',required='A connected regional subset of existing FEG with node/element IDs, spherical metrics, material-role mapping, retained physical support and explicitly tagged cut boundaries. If a plate boundary is included, specify mechanical accommodation/contact and a finite-width deformation model where required.',not_required='Full-planet boundary classification, faults or junctions outside the chosen region.',minimal_change='Bind one non-junction continental section, potentially the5:11 C028/C029 candidate; do not treat two1-degree cell-center spacing as physical deformation width or the whole global FEG as a regional domain.'),
 dict(id='G2_RHEOLOGY_ASSIGNMENT',status='MISSING_PHYSICAL_PARAMETERS',required='Select the constitutive law for each included crust/mantle role and its physical parameter set: applicable friction/effective-pressure terms and/or creep aCreep,bCreep,cCreep,dCreep,eCreep in the exact ShellSet conventions, with uncertainties/ranges and applicability.',not_required='Detailed mineral inventory or dry-olivine for all cells. Fault friction only if faults are explicitly represented.',minimal_change='One regional role-to-law table with source-backed or explicitly authored reference choices. Neither PRE k/rho/Cp/A nor INT10K benchmark constants determine this assignment.'),
 dict(id='G3_MECHANICAL_BC_AND_FORCING',status='MISSING_PHYSICAL_BOUNDARY_DATA',required='For each regional edge/node specify prescribed velocity components or tractions, reference/gauge and frame transform; basal load/traction or explicitly justified absence; stable rigid-mode constraints; contact policy if included. Bind time dependence over the short interval.',not_required='A measured Earth reconstruction or a global210Myr time series.',minimal_change='Use the existing authored first-segment Euler rule where applicable, project only onto identified physical regional boundaries, rotate into RX+0.5deg runtime frame, convert rad/year velocities to m/s, declare basal/contact conditions. Do not impose every interior unknown velocity or substitute Earth5R/PB2002.'),
 dict(id='G4_POSITIVE_TIME_STATE_TRANSFER',status='MISSING_TRANSIENT_CLOSURE_FOR_SELECTED_MECHANICS',required='Define how the computed velocity/strain-rate advances mesh, layer mass/thickness and material state, and which thermal feedback is retained over the interval. Preserve restart variables, energy/work ledger and boundary fluxes.',not_required='A new FEM solver, a planetary integrator, new hydrology/Deep or an automatic remesher.',minimal_change='Reuse the existing R6 time/history/controller structures; bind an isolated update/transport adapter to the chosen regional model. Existing pure-shear reduction is reusable only if its geometry, section width and imposed deformation assumptions are justified. ShellSet equilibrium alone is not T1.')]
 readiness=dict(status='BLOCKED_REGIONAL_RHEOLOGY_BOUNDARIES_AND_TRANSIENT_BINDING',selected_mechanical_operator='ShellSet/SHELLS',second_mechanical_operator_required=False,known=dict(T0_nominal_Ma=kin['time_ma'],plate_count=len(kin['plates']),kinematic_frame=kin['gauge']['name'],euler_5_11=euler5_11,first_segment=law['first_segment_policy'],rift_only_conditional_bound_years=27123.405156307464,rift_bound_is_general_topology_bound=False,mesh=feg['canonical_mesh'],runtime_frame=frame['evidence']['runtime_coordinate_frame_id'],finite_nodal_fields=feg['finite_coverage'],thermal_material_config=mat['identity'],PRE_material_field_count=len(meta['field_order']),selected_PRE_records=selected),physical_gaps=gaps,technical_follow_through='Reuse existing S1B source evaluator and material consumers in an isolated build; current tools binary is an observation, not source-to-binary qualification of this source. Compile/run only once the regional physical input packet is concrete.',source_BC_candidates=bcs,old_template_boundary_fields=boundary_template)
 template=dict(schema='REGIONAL_SHELLSET_PHYSICAL_INPUT_DRAFT_NOT_RUN',operator='ShellSet/SHELLS',T0_age_Ma=210.,maximum_explore_duration_years=10.,duration_is_a_proposed_numerical_window_not_a_new_physical_parameter=True,regional_FEG=None,regional_node_element_parent_map=None,regional_material_role_to_constitutive_parameters=None,boundary_conditions=None,basal_force_policy=None,mechanical_frame_transform=None,kinematic_validity_and_applicability=None,geometry_material_update_policy=None,thermal_feedback_policy=None,source_refs={p:v['sha256'] for p,v in inputs.items() if p.endswith(('R6_T0_CANONICAL_PLATE_KINEMATICS.json','R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json','R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json'))},status='INCOMPLETE_PHYSICAL_INPUTS_NO_LAUNCH_COMMAND')
 fallback=dict(process='THERMAL_1D_CONDUCTION_AND_RADIOGENESIS',status='ALREADY_EXECUTED_SUPPORTED_REGIONAL_PROCESS_NOT_GEODYNAMIC_ADVANCE',source=str(geo),T0_model_age_Ma=210.,T1_elapsed_years=queries['model_years'],columns={k:dict(state_id=q['state_id'],native_sha256=q['native_sha256'],Moho_m=q['geometry']['Moho_m'],base_m=q['geometry']['z_m'][-1],T_at_8m_K=q['nodes'][-1]['temperature_K_display']) for k,q in queries['columns'].items()},new_steps_executed=0,reason_not_rerun='Existing10year thermal trajectories and restart already verified. Their positive time does not satisfy a mechanical/deformation T1.')
 for name,obj in [('CAPABILITIES.json',capabilities),('INPUT_READINESS.json',readiness),('REGIONAL_INPUT_TEMPLATE.json',template),('THERMAL_FALLBACK.json',fallback),('HISTORICAL_HASH_COMPARISONS.json',matches),('SOURCE_ANCHORS.json',anchors),('INPUT_IDENTITIES.json',inputs)]:write(o/name,obj)
 # Same identities after the finite read-only audit; no originals modified.
 for p,v in inputs.items():assert digest(p)==v['sha256'],p
 write(o/'RESULT.json',dict(verdict='FIRST_PHYSICAL_GEODYNAMICS=BLOCKED_REGIONAL_MECHANICAL_INPUTS',physical_T1_created=False,selected_mechanical_operator='ShellSet/SHELLS',new_solver=False,provider_launches=0,physics_steps=0,physics_runtime_CPU_RAM='NOT_MEASURED_NO_SOLVE',source_and_input_count=len(inputs),historical_digest_comparisons=len(matches),audit_wall_s=time.perf_counter()-started,audit_user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,audit_system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,audit_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 print('BLOCKED_REGIONAL_MECHANICAL_INPUTS; read-only audit complete; no physical solve')
if __name__=='__main__':main()
