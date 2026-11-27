"""Native C10 deck and pre-solve-only fixture generation."""
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np

from experiments.r6_thermo_provider_pilot_v1 import c10_boundary as bc
from experiments.r6_thermo_provider_pilot_v1.run_c08_regional_closure import need

VENDOR = Path("external/ShellSet-v1.1.0/src")
STOCK = ("MOD_SharedVars.f90","MOD_ShellSet.f90","DMods.f90","MOD_Shells.f90")
COMPILER = Path("/opt/nvidia/hpc_sdk/Linux_x86_64/25.11/compilers/bin/nvfortran")
LIB = COMPILER.parent.parent/"lib"

# Actual ReadPm record names and order. A fresh deck is written from values.
LR_FIELDS = ("fFric","cFric","Biot","Byerly","aCreep","bCreep","cCreep","dCreep",
             "eCreep","tAdiab_gradie","zBAsth","pltRef","iConve","trHMax","tauMax",
             "rhoH2O","rhoBar","rhoAst","gMean","oneKm","radius","alphaT","conduc",
             "radio","tSurf","temLim","maxItr","okToQt","refStr","okDelV","everyP")


def numerical_controls():
    return {"maxItr":50,"okToQt":5e-4,"refStr_Pa":50e6,"okDelV_m_s":1e-11,
            "everyP":False,"authority":"Originally parsed and used in the nine-node ENGINEERING_ONLY smoke. Reused as initial numerical proposals.",
            "sensitivity":"Compare tighter okToQt and rerun at half/double okDelV with independently fixed force, work and gradient error budgets. refStr changes constraint and viscosity scales.",
            "equations":{"etaMax":"min(refStr*mean_thickness/(side*okDelV),trHMax/okDelV)",
                         "visMax":"refStr*sqrt(total_area)/(4*okDelV) for regional non-sphere"},
            "not_constitutive_authority":True}


def lr_values(initial, model, biot, *, compatibility_depth=1000.):
    p=initial["parameters"]
    thermal=p["thermal"]
    density=p["reference_densities"]
    nc=numerical_controls()
    need(biot in (0.,1.) and int(compatibility_depth/1000.+.5)>=1
         and compatibility_depth<=300000.,"C10_BASAL_COMPATIBILITY_DEPTH")
    # S1B supplies the actual temperature and weighted densities. Compatibility
    # tAdiab comes from the source reference; gradie is inactive in OneBar S1B.
    return {"fFric":0.,"cFric":model["cFric"],"Biot":biot,"Byerly":0.,
            "aCreep":model["A_Pa_s_to_e"],"bCreep":model["B_K"],
            "cCreep":model["C_K_per_m"],"dCreep":model["dCreep_Pa"],"eCreep":model["eCreep"],
            "tAdiab_gradie":[p["potential_temperature"]["nominal"],0.],
            "zBAsth":compatibility_depth,"pltRef":"RF","iConve":0,"trHMax":0.,"tauMax":[0.,0.],
            "rhoH2O":density["seawater"]["nominal"],
            "rhoBar":[density["continental_crust"]["nominal"],density["lithospheric_mantle"]["nominal"]],
            "rhoAst":density["asthenosphere"]["nominal"],
            "gMean":p["gMean"]["value"],"oneKm":1000.,"radius":bc.RADIUS,
            "alphaT":[thermal[k]["alpha"]["nominal"] for k in ("continental_crust","mantle")],
            "conduc":[thermal[k]["k"]["nominal"] for k in ("continental_crust","mantle")],
            "radio":[p["heat_production"][k]["nominal"] for k in ("continental_crust","mantle_lithosphere")],
            "tSurf":p["surface_temperature"]["nominal"],"temLim":[p["temLim"]["value"]]*2,
            "maxItr":nc["maxItr"],"okToQt":nc["okToQt"],"refStr":nc["refStr_Pa"],
            "okDelV":nc["okDelV_m_s"],"everyP":"F"}


def serialize_lr(values):
    need(set(values)==set(LR_FIELDS),"C10_LR_INVENTORY")
    return bc.SCENARIO+"\n"+"".join(
        (",".join(map(str,values[key])) if isinstance(values[key],list) else str(values[key]))+"\n"
        for key in LR_FIELDS)


def reporting_plate_map(package, source_nodes):
    result=[]
    for row in package["G4_mapping"]["nodes"]:
        parent=row["parent_id"]
        src=source_nodes[str(parent)]
        owners=[c["plate_id"] for c in src["native_cells"]
                if c["cell_id"]==src["pre_numerical_owner_cell"]]
        need(len(owners)==1 and owners[0] in src["native_plate_ids"],"C10_SOURCE_REPORTING_OWNER")
        result.append({"local_id":row["local_id"],"parent_id":parent,"native_slot":owners[0]+2,
                       "source_PRE_owner_plate_id":owners[0],"all_source_plate_ids":src["native_plate_ids"],
                       "sided_fault_assignment":None})
    return result


def source_with_hard_stop(original):
    """Compile the real readers and precompute path while excluding Pure."""
    a=original.index("       IF(Verbose) WRITE(iUnitVerb, 2) iUnitC")
    b=original.index("       if(rpeat>1",a)
    # Keep exact PRE numerical owner as reporting metadata only. Native
    # GetPBx/Assign are legacy Earth lookup and are not needed with code-2 BC.
    assign="""       if (.not. ArcanaShellsModeActive()) stop 20
       if (iConve /= 0 .or. trHMax /= 0d0 .or. nFl /= 0 .or. rpeat /= 1) stop 21
       slab_q = .false.
       do i=1,numNod
         read(iUnitC,*,iostat=ios) n,whichP(i)
         if (ios/=0 .or. n/=i) stop 22
         if (whichP(i)<2 .or. whichP(i)>13) stop 22
       end do

"""
    tail="!  -Create and solve a thin-plate version of equilibrium"
    end=original.index(tail,b)
    before=original[:a]+assign+original[b:end]
    # Require ordered ReadBC input independently since this upstream reader
    # sets allOK on ordering defects and does not export that flag.
    needle="       skipBC = .FALSE.\n       CALL ReadBC"
    need(before.count(needle)==1,"C10_NATIVE_READBC_ANCHOR")
    before=before.replace(needle,"""       read(iUnitB,'(A)',iostat=ios) title2
       if (ios/=0 .or. nCond/=32) stop 23
       do i=1,nCond
         read(iUnitB,*,iostat=ios) n,LRi,j
         if (ios/=0 .or. n/=i .or. LRi/=nodCon(i) .or. j/=2) stop 24
       end do
       read(iUnitB,*,iostat=ios) n
       if (ios>=0) stop 25
       rewind(iUnitB)
       skipBC = .FALSE.
       CALL ReadBC""")
    return before+"""
! No assembled operator or call to Pure/Solver exists in this fixture.
       if (sphere .or. numNod/=81 .or. numEl/=128 .or. nCond/=32) stop 26
       if (any(pulled) .or. etaMax/=0d0 .or. any(oVB/=0d0) .or. any(vM/=0d0)) stop 27
       if (any(delta_rho/=0d0) .or. any(glue<=0d0) .or. any(.not.ieee_is_finite(glue))) stop 28
       v(1,:) = 2d-9
       v(2,:) = -3d-9
       call THOnB(basal,continuum_LRi,etaMax,fPSfer,glue,iConve,LRn,LR_set_eCreep, &
            mxEl,mxNode,nodes,numEl,oVB,pulled,trHMax,v,eta,sigHB,outVec)
       if (any(eta/=0d0) .or. any(sigHB/=0d0)) stop 29
       open(71,file='native_pre_solve.txt',status='new')
       write(71,'(A,7I8)') 'SIZE ',numNod,numEl,nCond,nRank,nLB,nUB,nKRows
       write(71,'(A,4ES26.17E3,2I8)') 'CONTROL ',Biot,zBAsth,etaMax,visMax,iConve,iPVRef
       do i=1,numNod
         write(71,'(A,2I8,7ES26.17E3)') 'NODE ',i,whichP(i),elev(i),zMNode(i),tLNode(i),atNode(i),tauZZN(i), &
             fBase(2*i-1),fBase(2*i)
       end do
       do i=1,numEl
         do j=1,7
           call c10_ip_diagnostics(nodes(:,i),points(:,j),gMean,zMoho(j,i),tLInt(j,i), &
                c10_water,c10_pc,c10_p_total)
           write(71,'(A,2I8,11ES26.17E3)') 'IP ',i,j,zMoho(j,i),tLInt(j,i),sigZZI(j,i),tauZZI(j,i),glue(j,i), &
                c10_water,c10_pc,c10_p_total,eta(j,i),sigHB(:,j,i)
         end do
       end do
       do i=1,nCond
         write(71,'(A,3I8,2ES26.17E3)') 'BC ',i,nodCon(i),iCond(i),vBCMag(i)*cos(vBCArg(i)),vBCMag(i)*sin(vBCArg(i))
       end do
       close(71)
       print '(A)','C10_STOP_AFTER_FIXED_BEFORE_PURE'
       stop 0
end subroutine Shells_v5p0

subroutine c10_ip_diagnostics(ids,w,g,moho,mantle,water,pc,pt)
  use ArcanaRuntime, only: ArcanaRuntimeEvaluateIP, ArcanaRuntimeMeanEffectiveDensity, &
       ARCANA_PROPERTY_COUNT, ARCANA_PROP_RHO_WATER
  implicit none
  integer, intent(in) :: ids(3)
  real(8), intent(in) :: w(3),g,moho,mantle
  real(8), intent(out) :: water,pc,pt
  integer :: ierr, phases(3)
  real(8) :: p(ARCANA_PROPERTY_COUNT),t,rho
  call ArcanaRuntimeEvaluateIP(ids,w,0d0,t,p,phases,ierr)
  if (ierr /= 0) stop 30
  water = p(ARCANA_PROP_RHO_WATER)
  call ArcanaRuntimeMeanEffectiveDensity(ids,w,3,0d0,moho,rho,ierr)
  if (ierr /= 0) stop 31
  pc = rho*g*moho
  call ArcanaRuntimeMeanEffectiveDensity(ids,w,3,moho,moho+mantle,rho,ierr)
  if (ierr /= 0) stop 32
  pt = pc+rho*g*mantle
end subroutine c10_ip_diagnostics
end module SHELLS
"""


def generated_source(original):
    source=source_with_hard_stop(original)
    anchor="       use ShellsSubs"
    source=source.replace(anchor,"       use, intrinsic :: ieee_arithmetic, only: ieee_is_finite\n"+anchor,1)
    anchor="       CHARACTER*10 :: clock_time"
    need(source.count(anchor)==1 and not re.search(r"(?im)^\s*call\s+(pure|solver|viscos)\b",source),
         "C10_PRESOLVE_STOP_SCOPE")
    return source.replace(anchor,"       real(8) :: c10_water,c10_pc,c10_p_total\n"+anchor,1)


def parse_probe(path):
    values={k:[] for k in ("SIZE","CONTROL","NODE","IP","BC")}
    for line in path.read_text().splitlines():
        key,*raw=line.split()
        row=[float(x) for x in raw]
        need(np.isfinite(row).all(),"C10_NONFINITE_NATIVE_DIAGNOSTIC")
        values[key].append(row)
    need([len(values[k]) for k in values]==[1,1,81,896,32],"C10_NATIVE_OUTPUT_INVENTORY")
    return values


def run_native_probe(root, output, files, controls):
    """Link and execute only an executable whose entry routine ends before Pure."""
    need(COMPILER.is_file() and (LIB/"liblapack.so").is_file() and (LIB/"libblas.so").is_file(),
         "C10_PINNED_COMPILER_OR_LINK_INPUT_MISSING")
    build=output/"native_pre_solve"
    build.mkdir()
    stock=tuple(root/VENDOR/name for name in STOCK)
    for p in stock:
        shutil.copyfile(p,build/p.name)
    (build/"MOD_ArcanaRuntime.f90").write_text(files["MOD_ArcanaRuntime.regional.f90"])
    upstream=root/VENDOR/"SHELLS_v5.0.f90"
    (build/"SHELLS_pre_solve.f90").write_text(generated_source(upstream.read_text()))
    driver=Path(__file__).with_name("c10_pre_solve_driver.f90")
    shutil.copyfile(driver,build/driver.name)
    sources=(STOCK[0],"MOD_ArcanaRuntime.f90",*STOCK[1:],"SHELLS_pre_solve.f90",driver.name)
    argv=[str(COMPILER),"-O0","-Mbackslash","-Kieee","-Mbounds",*sources,
          "-L"+str(LIB),"-Wl,-rpath,"+str(LIB),"-llapack","-lblas","-o","pre_solve_probe.exe"]
    with (build/"build.log").open("x") as log:
        subprocess.run(["/usr/bin/time","-v","-o","build.time",*argv],cwd=build,
                       check=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    exe=build/"pre_solve_probe.exe"
    for name, args in (("compiler.txt",[str(COMPILER),"--version"]),("linked.txt",["ldd",str(exe)]),
                       ("elf.txt",["readelf","-h","-d",str(exe)])):
        with (build/name).open("x") as log:
            subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=10)
    results={}
    bad_depth=serialize_lr(dict(controls,zBAsth=400.))
    invalid_mode=serialize_lr(dict(controls,iConve="6,1.0"))
    rejected={}
    for label, body, bcs, expected in (
        ("hydrostatic",files["regional.in"],files["controlled.bcs"],0),
        ("dry",files["regional_dry.in"],files["controlled.bcs"],0),
        ("linear_arc",files["regional.in"],files["linear_arc_sensitivity.bcs"],0),
        ("zero_depth",serialize_lr(dict(controls,zBAsth=0.)),files["controlled.bcs"],13),
        ("depth_2km",files["regional_compatibility_2km.in"],files["controlled.bcs"],0),
        ("empty_onebar",bad_depth,files["controlled.bcs"],15),
        ("active_basal_guard",invalid_mode,files["controlled.bcs"],14),
        ("wrong_bc_order",files["regional.in"],swap_boundary_nodes(files["controlled.bcs"]),24),
    ):
        work=build/label
        work.mkdir()
        for key in ("regional.feg","regional_PRE.dat","runtime.control","regional_reporting_plates.dat"):
            (work/key).write_text(files[key])
        (work/"regional.in").write_text(body)
        (work/"controlled.bcs").write_text(bcs)
        with (work/"run.log").open("x") as log:
            p=subprocess.run(["/usr/bin/time","-v","-o","run.time",str(exe)],cwd=work,stdout=log,
                             stderr=subprocess.STDOUT,timeout=30)
        need(p.returncode==expected,"C10_NATIVE_PROBE_EXIT:"+label)
        if expected:
            need(not (work/"native_pre_solve.txt").exists(),"C10_UNEXPECTED_NEGATIVE_RESULT")
            rejected[label]=p.returncode
            continue
        need("C10_STOP_AFTER_FIXED_BEFORE_PURE" in (work/"run.log").read_text()
             and not (work/"FatalError.txt").exists(),"C10_NATIVE_PROBE_MARKER")
        results[label]=parse_probe(work/"native_pre_solve.txt")
    from experiments.r6_thermo_provider_pilot_v1.run_c08_regional_closure import sha

    return results, {"compiler":str(COMPILER),"compiler_sha256":sha(COMPILER),"build_arguments":argv,
                     "linked_LAPACK_BLAS_sha256":{name:sha(LIB/name) for name in ("liblapack.so","libblas.so")},
                     "native_library_bindings":(build/"linked.txt").read_text(),
                     "stock_source_sha256":{p.name:sha(p) for p in (*stock,upstream)},
                     "probe_binary_sha256":sha(exe),"stops":rejected,
                     "physical_solves":0,"assembled_operators":0,
                     "diagnostic_scope":"Serial native readers, FillIn, Limits, Fixed and THOnB with manufactured velocity, then hard stop. No rpeat loop, Pure or factorization."}


def swap_boundary_nodes(body):
    rows=body.splitlines()
    first,second=rows[1].split(),rows[2].split()
    first[1],second[1]=second[1],first[1]
    rows[1],rows[2]=" ".join(first)," ".join(second)
    return "\n".join(rows)+"\n"
