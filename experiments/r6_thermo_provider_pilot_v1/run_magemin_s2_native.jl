# ARCANA R6 S2 candidate: fresh-process real native Earth chemistry fixtures.
# Not original ARCANA geology; run only under source-bound S2 qualification.
using MAGEMin_C
using TOML
using Pkg

const CUSTOM_NAMES = ["SiO2","Al2O3","CaO","MgO","FeO","Fe2O3",
                      "K2O","Na2O","TiO2","Cr2O3","H2O"]
const CUSTOM_WT = [48.43,15.19,11.57,10.13,6.65,1.64,
                   0.59,1.87,0.68,0.0,3.0]
const MASS = Dict("FeO"=>71.85, "Fe2O3"=>159.69, "O"=>16.0)

function source_native_basis(oxides::Vector{String})
    abs(sum(CUSTOM_WT) - 99.75) < 1e-10 ||
        error("S2_CUSTOM_INPUT_TOTAL_CHANGED")
    values = Dict(zip(CUSTOM_NAMES, CUSTOM_WT))
    n = values["Fe2O3"] / MASS["Fe2O3"]
    delete!(values, "Fe2O3")
    values["FeO"] += 2n * MASS["FeO"]
    values["O"] = n * MASS["O"]
    Set(keys(values)) == Set(oxides) || error("S2_SOURCE_BASIS_NOT_COVERED")
    total = sum(Base.values(values))
    return [values[oxide] / total for oxide in oxides]
end

function finite_fraction_vector(v)
    !isempty(v) && all(x -> isfinite(x) && x >= -1e-13 && x <= 1.0+1e-13, v)
end

function capture(out; custom::Bool=false)
    Int(out.status) == 0 || error("S2_MAGEMIN_NONZERO_NATIVE_STATUS")
    phases = String.(out.ph)
    f = Float64.(out.ph_frac_wt)
    oxides = String.(out.oxides)
    bulk = Float64.(out.bulk_wt)
    types = Int.(out.ph_type)
    nss, npp = Int(out.n_SS), Int(out.n_PP)
    length(unique(phases)) == length(phases) ||
        error("S2_AMBIGUOUS_PHASE_NAMES")
    length(phases) == length(f) == length(types) == nss+npp ||
        error("S2_PHASE_VECTOR_SIZE_MISMATCH")
    length(out.SS_vec) == nss && length(out.PP_vec) == npp ||
        error("S2_PHASE_SUBSTRUCT_SIZE_MISMATCH")
    all(==(1), types[1:nss]) && all(==(0), types[nss+1:end]) ||
        error("S2_PHASE_STRUCT_ORDER_UNVERIFIED")
    length(oxides) == length(bulk) && length(unique(oxides)) == length(oxides) ||
        error("S2_OXIDE_BASIS_INVALID")
    finite_fraction_vector(f) && abs(sum(f)-1.0) <= 1e-8 ||
        error("S2_PHASE_MASS_SUM_INVALID")
    finite_fraction_vector(bulk) && abs(sum(bulk)-1.0) <= 1e-8 ||
        error("S2_BULK_WEIGHT_SUM_INVALID")
    comps = Vector{Vector{Float64}}()
    for i in eachindex(phases)
        phase = i <= nss ? out.SS_vec[i] : out.PP_vec[i-nss]
        comp = Float64.(phase.Comp_wt)
        length(comp) == length(oxides) && finite_fraction_vector(comp) &&
            abs(sum(comp)-1.0) <= 1e-8 ||
            error("S2_PHASE_COMPOSITION_WEIGHT_INVALID")
        push!(comps, comp)
    end
    rec = [sum(f[i]*comps[i][j] for i in eachindex(f))
           for j in eachindex(oxides)]
    closure = maximum(abs.(rec .- bulk))
    residual = Float64(out.bulk_res_norm)
    isfinite(closure) && closure <= 1e-10 &&
        isfinite(residual) && 0 <= residual <= 1e-9 ||
        error("S2_NATIVE_CHEMICAL_CLOSURE_INVALID")

    source_delta = custom ?
        maximum(abs.(source_native_basis(oxides) .- bulk)) : -1.0
    if custom
        source_delta <= 1e-12 || error("S2_SOURCE_NATIVE_BASIS_INVALID")
    end
    G, rho = Float64(out.G_system), Float64(out.rho)
    isfinite(G) && isfinite(rho) && rho > 0 ||
        error("S2_MAGEMIN_PHYSICAL_FIELDS_INVALID")
    # TOML does not accept NaN; source-native check is only meaningful for custom.
    result = Dict{String,Any}(
        "status" => Int(out.status),
        "P_kbar" => Float64(out.P_kbar),
        "T_C" => Float64(out.T_C),
        "G_system" => G,
        "rho_kg_m3" => rho,
        "phases" => phases,
        "phase_mass_fractions" => f,
        "oxides" => oxides,
        "bulk_wt" => bulk,
        "phase_comp_wt" => comps,
        "bulk_res_norm" => residual,
        "iterations" => Int(out.iter),
        "source_native_basis_closure_custom" => source_delta,
        "native_component_weight_closure_abs" => closure,
        "database" => String(out.database),
        "dataset" => String(out.dataset),
        "phase_types" => types
    )
    result["database"] == "ig" && result["dataset"] == "tc_ds636" ||
        error("S2_MAGEMIN_DATABASE_DATASET_DRIFT")
    return result
end

function klb1()
    data = Initialize_MAGEMin("ig",verbose=false)
    try
        data = use_predefined_bulk_rock(data,0)
        out = point_wise_minimization(8.0,800.0,data)
        return capture(out)
    finally
        Finalize_MAGEMin(data)
    end
end

function custom()
    data = Initialize_MAGEMin("ig",verbose=false)
    try
        out = single_point_minimization(10.0,1100.0,data;
                       X=CUSTOM_WT,Xoxides=CUSTOM_NAMES,sys_in="wt")
        return capture(out,custom=true)
    finally
        Finalize_MAGEMin(data)
    end
end

function main()
    length(ARGS) == 1 || error("S2_REQUIRE_EXACTLY_ONE_REPORT_PATH")
    file = abspath(ARGS[1])
    !ispath(file) || error("S2_OUTPUT_WRITE_ONCE_CONFLICT")
    pkg = [x for x in values(Pkg.dependencies()) if x.name=="MAGEMin_C"]
    length(pkg)==1 && pkg[1].version == v"2.4.5" ||
        error("S2_MAGEMIN_C_VERSION_DRIFT")
    cases = Dict{String,Any}()
    cases["MAGEMIN_PREDEFINED_KLB1"] = klb1()
    cases["MAGEMIN_CUSTOM_IG"] = custom()
    report = Dict{String,Any}(
        "schema"=>"ARCANA_R6_THERMO_S2_MAGEMIN_NATIVE_RUN_V1",
        "scope"=>"EARTH_FIXTURES_ONLY",
        "provider"=>"MAGEMin_C.jl",
        "provider_version"=>"2.4.5",
        "cases"=>cases,
        "cross_provider_equivalence"=>false,
        "D_024"=>"ACTIVE",
        "physical_T1_is_null"=>true,
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED"=>false
    )
    open(file,"x") do io
        TOML.print(io,report)
    end
    println("S2_MAGEMIN_NATIVE_TWO_CASES_COMPLETE")
    println("S2_MAGEMIN_SOURCE_NATIVE_INPUT_BOOKKEEPING_PASS")
    println("S2_CROSS_PROVIDER_EQUIVALENCE=NOT_QUALIFIED")
end

main()
