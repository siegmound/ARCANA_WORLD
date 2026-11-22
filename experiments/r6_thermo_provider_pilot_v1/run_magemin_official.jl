# ARCANA Earth-only MAGEMin_C.jl official upstream examples, v2.4.5.
# No Arcana T0 rock assignment, no physical solver, no cross-tool ranking.
using Pkg
using TOML
using MAGEMin_C

length(ARGS) == 1 || error("Exactly one output .toml file path required")
file = abspath(ARGS[1])
ispath(file) && error("WRITE_ONCE_OUTPUT_EXISTS")

# The Julia package must be installed from the specified immutable upstream
# commit; the Julia Manifest.toml SHA is separately collected by the operator.
entries = [x for x in values(Pkg.dependencies()) if x.name == "MAGEMin_C"]
length(entries) == 1 || error("MAGEMin_C_PIN_NOT_INSTALLED")
entries[1].version == v"2.4.5" || error("MAGEMin_C_VERSION_NOT_2_4_5")

function normalize(out)
    out.status == 0 || error("MAGEMin_SOURCE_FIXTURE_NOT_CONVERGED")
    fractions = Float64.(out.ph_frac_wt)
    phases = String.(out.ph)
    (length(phases) > 0 && length(phases) == length(fractions)) || error("PHASES_MISSING")
    (all(isfinite, fractions) && all(x -> 0 <= x <= 1, fractions)
      && abs(sum(fractions)-1) < 0.02) || error("PHASE_MASS_BALANCE_BAD")
    rho = Float64(out.rho)
    isfinite(rho) && rho > 0 || error("SYSTEM_DENSITY_BAD")
    return Dict(
        "status"=>Int(out.status),"P_kbar"=>Float64(out.P_kbar),
        "T_C"=>Float64(out.T_C), "rho_kg_m3"=>rho,
        "phases"=>phases,"phase_mass_fractions"=>fractions,
        "database_label"=>"ig")
end

fixtures = Dict{String,Any}()
data = Initialize_MAGEMin("ig",verbose=false)
try
    data = use_predefined_bulk_rock(data,0)  # Official README Example 1: KLB1
    out = point_wise_minimization(8.0,800.0,data)
    fixtures["MAGEMIN_PREDEFINED_KLB1"] = normalize(out)
finally
    Finalize_MAGEMin(data)
end

data2 = Initialize_MAGEMin("ig",verbose=false)
try
    # Official README Example 2. Deliberately NOT renormalized (sum 99.75 wt.%).
    names = ["SiO2","Al2O3","CaO","MgO","FeO","Fe2O3","K2O",
             "Na2O","TiO2","Cr2O3","H2O"]
    values = [48.43,15.19,11.57,10.13,6.65,1.64,0.59,1.87,0.68,0.0,3.0]
    abs(sum(values)-99.75) < 1e-10 || error("COMPOSITION_QUIETLY_CHANGED")
    out = single_point_minimization(10.0,1100.0,data2;
                                     X=values,Xoxides=names,sys_in="wt")
    fixtures["MAGEMIN_CUSTOM_IG"] = normalize(out)
finally
    Finalize_MAGEMin(data2)
end

report=Dict("provider"=>"MAGEMin_C.jl","version"=>"2.4.5",
            "scope"=>"EARTH_OFFICIAL_FIXTURE_ONLY_NOT_ARCANA",
            "cross_provider_comparable"=>false,
            "physical_T1_is_null"=>true,
            "fixtures"=>fixtures)
# Output only after the two official exercises pass.
open(file,"w") do io
    TOML.print(io,report)
end
println("ARCANA_MAGEMIN_UPSTREAM_TWO_OFFICIAL_CASES=PASS")
