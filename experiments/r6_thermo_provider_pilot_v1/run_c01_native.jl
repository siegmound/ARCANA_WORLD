# Approved noncanonical C01, one process / one minimization at most.
using MAGEMin_C, TOML, Pkg, SHA

function write_once(path, report)
    !ispath(path) || error("C01_OUTPUT_EXISTS")
    open(path,"w") do io
        TOML.print(io,report)
    end
end

function raw_scalar(x)
    v=Float64(x)
    return isfinite(v) ? v : string(v)
end
raw_vector(x) = raw_scalar.(x)

function main()
    length(ARGS)==2 || error("C01_ARGS")
    inp=TOML.parsefile(ARGS[1])
    dir=ARGS[2]
    pkg=[x for x in values(Pkg.dependencies()) if x.name=="MAGEMin_C"]
    length(pkg)==1 && pkg[1].version==v"2.4.5" || error("C01_PACKAGE_DRIFT")
    wrapper=joinpath(dirname(dirname(pathof(MAGEMin_C))),"julia","MAGEMin_wrappers.jl")
    raw=read(wrapper)
    blob=bytes2hex(sha1(vcat(Vector{UInt8}(codeunits("blob "*string(length(raw))*"\0")),raw)))
    blob==inp["wrapper_git_blob"] || error("C01_WRAPPER_GIT_BLOB_DRIFT")
    function gitblob(path)
        bytes=read(path)
        bytes2hex(sha1(vcat(Vector{UInt8}(codeunits("blob "*string(length(bytes))*"\0")),bytes)))
    end
    info=gitblob(joinpath(dirname(wrapper),"db_infos_generated.jl"))
    registry=gitblob(joinpath(dirname(wrapper),"database_registry.jl"))
    info=="a4e89099410933577ebd182732705ab472d090cb" && registry=="887cba5331efcf8adff81555f8a58dcd07e59c90" || error("C01_REGISTRY_DRIFT")
    names=String.(inp["names"])
    wt=Float64.(inp["wt_amounts"])
    # Run provider's own conversion with default guard, never disable guard.
    converted,ox=convertBulk4MAGEMin(wt,names,"wt","mb")
    mol=Float64.(converted)./100
    expected=inp["expected_native_mol"]
    Set(ox)==Set(keys(expected)) || error("C01_CONVERSION_OXIDES")
    delta=maximum(abs(mol[i]-expected[ox[i]]) for i in eachindex(ox))
    write_once(joinpath(dir,"CONVERSION.toml"),Dict("oxides"=>ox,"mol_fraction"=>mol,
        "max_expected_mole_delta"=>delta,"wrapper_git_blob"=>blob,"info_git_blob"=>info,"registry_git_blob"=>registry,"minimization_calls"=>0))
    isfinite(delta) && delta<=1e-12 || error("C01_CONVERSION_GUARD_CHANGED_INPUT_NO_SOLVE")
    data=Initialize_MAGEMin("mb",verbose=false,dataset=62,mbCpx=1,mbIlm=0,solver=0,optimizer=0,final_Newton_step=1,buffer="NONE")
    try
        out=single_point_minimization(Float64(inp["P_kbar"]),Float64(inp["T_C"]),data;
            X=wt,Xoxides=names,sys_in="wt",scp=0,progressbar=false)
        phases=String.(out.ph)
        nss=Int(out.n_SS)
        types=Int.(out.ph_type)
        length(types)==length(phases)==nss+Int(out.n_PP) || error("C01_PHASE_STRUCTURE")
        all(==(1),types[1:nss]) && all(==(0),types[nss+1:end]) || error("C01_PHASE_ORDER")
        comps=[Float64.((i<=nss ? out.SS_vec[i] : out.PP_vec[i-nss]).Comp_wt) for i in eachindex(phases)]
        diag=Dict("Cp_fixed_phase_J_kg_K"=>raw_vector(out.s_cp),
            "alpha_fixed_phase_per_K"=>raw_vector(out.alpha),"beta_per_GPa"=>raw_scalar(out.beta),
            "entropy_kJ_mol_oxide_K"=>raw_vector(out.entropy),"enthalpy_kJ_mol_oxide"=>raw_vector(out.enthalpy),
            "M_sys_g_mol_oxide"=>raw_scalar(out.M_sys),"volume_cm3_mol_oxide"=>raw_scalar(out.V),
            "native_fO2_unqualified"=>raw_scalar(out.fO2),"native_dQFM_unqualified"=>raw_scalar(out.dQFM),
            "native_aH2O_unqualified"=>raw_scalar(out.aH2O))
        write_once(joinpath(dir,"NATIVE.toml"),Dict("case"=>inp["case"],"status"=>Int(out.status),
            "database"=>String(out.database),"dataset"=>String(out.dataset),"native_version"=>String(out.MAGEMin_ver),
            "P_kbar"=>Float64(out.P_kbar),"T_C"=>Float64(out.T_C),"G_system"=>Float64(out.G_system),
            "rho_kg_m3"=>Float64(out.rho),"oxides"=>String.(out.oxides),"bulk_wt"=>Float64.(out.bulk_wt),
            "bulk_mol"=>Float64.(out.bulk),"phases"=>phases,"phase_types"=>types,
            "phase_mass_fractions"=>Float64.(out.ph_frac_wt),"phase_comp_wt"=>comps,
            "bulk_res_norm"=>Float64(out.bulk_res_norm),"iterations"=>Int(out.iter),
            "solid_wt"=>Float64(out.frac_S_wt),"melt_wt"=>Float64(out.frac_M_wt),"fluid_wt"=>Float64(out.frac_F_wt),
            "native_diagnostics"=>diag))
    finally
        Finalize_MAGEMin(data)
    end
end
main()
