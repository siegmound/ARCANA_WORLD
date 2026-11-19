"""Explicit staged R1-I0: rational patch,16x8,32x16; fail closed, no retry."""
import argparse,csv,hashlib,json,pathlib,sys,time,resource,traceback


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False,default=lambda x:x.tolist());f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--source-contract',required=True);parser.add_argument('--expected-contract-sha256',required=True);parser.add_argument('--execute-i0',action='store_true');a=parser.parse_args()
    if not a.execute_i0:parser.error('explicit opt-in required')
    repo=pathlib.Path(__file__).resolve().parents[1];contract=pathlib.Path(a.source_contract)
    assert sha(contract)==a.expected_contract_sha256
    c=json.loads(contract.read_text())
    def pins():assert all(sha(repo/k)==v for k,v in {**c['preserved_pins'],**c['new_pins']}.items())
    pins();out=pathlib.Path(a.output);out.mkdir();started=time.perf_counter();u0=resource.getrusage(resource.RUSAGE_SELF)
    write(out/'INVOCATION.json',{'argv':sys.argv,'source_contract_sha256':sha(contract),'scope':'staged minimum I0 only; stop first failed prerequisite','scientific_authority':False})
    results=[];certrows=[];limrows=[];face_rows=[];marker='HR2_P1_R1_I0=BLOCKED_RUNTIME';code=2
    try:
        import numpy as np
        sys.path.insert(0,str(repo/'experiments'))
        from hr2_p1_r1_checks.checks_i0 import rational_flux_oracle,rational_limiter_oracle,cfl_constant_zero_and_negative_oracles,sphere_admission_oracle
        from hr2_p1_r1.geometry import sphere,prepare_face
        from hr2_p1_r1.certification import certify
        write(out/'RUNTIME.json',{'python':sys.version,'numpy':np.__version__,'executable':sys.executable})
        for fn in [rational_flux_oracle,rational_limiter_oracle,cfl_constant_zero_and_negative_oracles]:
            t=time.perf_counter();d=fn();write(out/(fn.__name__+'.json'),d)
            results.append({'test':fn.__name__,'status':'PASS','wall_s':time.perf_counter()-t})
            limrows.append({'test':fn.__name__,'status':'PASS','activated_faces':d.get('activated_faces'),'minimum_h':d.get('minimum_h'),'maximum_h':d.get('maximum_h'),'residual_m3':d.get('residual_m3'),'roundoff_bound_m3':d.get('roundoff_bound_m3')})
        for width,height in [(16,8),(32,16)]:
            mesh=sphere(width,height);sphere_admission_oracle(mesh)
            results.append({'test':f'sphere_geometry_{width}x{height}','status':'PASS'})
            geo=out/f'{width}x{height}';geo.mkdir()
            np.savez(geo/'topology.npz',areas=mesh.areas,first=mesh.first,second=mesh.second,axis=mesh.axis,length=mesh.length,distance=mesh.distance,centers=mesh.centers,face_phi=mesh.face_phi,face_lam=mesh.face_lam)
            order=[width-1]+[k for k in range(len(mesh.first)) if k!=width-1]
            for face in order:
                t=time.perf_counter();packet=prepare_face(mesh,face,16,32);cert=certify(mesh,packet)
                cert.update(width=width,height=height,face=face,axis='EW' if mesh.axis[face]==0 else 'NS',patch_cells=len(packet['patch']),assembly_wall_s=time.perf_counter()-t)
                file=geo/f'face_{face}.npz'
                np.savez(file,**{k:v for k,v in packet.items() if isinstance(v,np.ndarray)})
                cert.update(coefficient_file=file.name,coefficient_sha256=sha(file),coefficient_bytes=file.stat().st_size)
                certrows.append(cert);write(geo/f'face_{face}_certificate.json',cert)
                if cert['certificate_status']!='CERTIFIED':
                    results.append({'test':f'moment_certificate_{width}x{height}_face{face}','status':'FAIL','reason':cert['certificate_status']})
                    marker='HR2_P1_R1_I0=BLOCKED_GEOMETRY_ENCLOSURE_AND_RANK_CERTIFICATION'
                    raise StopIteration('Stopped at first geometry certificate failure; no sphere flux on state or advance authorized past it')
            # No latent unqualified evolution path: future flux/advance tests require
            # a separately reviewed error/derivative certificate implementation.
            marker='HR2_P1_R1_I0=BLOCKED_DERIVATIVE_CERTIFICATE_NOT_IMPLEMENTED'
            raise StopIteration('All pointwise certificates require a uniform derivative bound before physical flux tests')
    except StopIteration as e:
        write(out/'STOP.json',{'marker':marker,'reason':str(e),'no_retry':True})
        code=4
    except Exception:
        write(out/'ERROR.json',{'marker':marker,'traceback':traceback.format_exc(),'no_retry':True});traceback.print_exc()
    finally:
        pins()
        write(out/'STAGED_TESTS.json',results)
        for name,rows,fields in [('MOMENT_CERTIFICATES.csv',certrows,list(certrows[0]) if certrows else ['status']),('LIMITER_AND_CFL.csv',limrows,list(limrows[0]) if limrows else ['status'])]:
            with (out/name).open('x') as f:
                w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
        for width,height in [(16,8),(32,16)]:
            for mode in ['latitude','longitude_cosine','longitude_sine_shifted','rotated','degree_two','nonharmonic']:
                face_rows.append({'width':width,'height':height,'mode':mode,'status':'NOT_EXECUTED_GEOMETRY_GATE_BLOCKED','flux_error':None,'limiter_activation':None})
        with (out/'POLAR_FACE_ORACLES.csv').open('x') as f:w=csv.DictWriter(f,list(face_rows[0]));w.writeheader();w.writerows(face_rows)
        u=resource.getrusage(resource.RUSAGE_SELF)
        write(out/'RESULT.json',{'marker':marker,'exit_code':code,'executed_test_records':len(results),'wall_s_before_receipt':time.perf_counter()-started,'cpu_user_s':u.ru_utime-u0.ru_utime,'cpu_system_s':u.ru_stime-u0.ru_stime,'process_peak_rss_kib':u.ru_maxrss,'sphere_time_advances':0,'scope':'Initial implementation only; no R1 numerical PASS, no larger grid, no B0/restart qualification','new_full_qualification':False})
    print(marker,flush=True);return code


if __name__=='__main__':raise SystemExit(main())
