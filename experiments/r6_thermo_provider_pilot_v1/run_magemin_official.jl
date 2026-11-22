# ARCANA R6 S1: real upstream Earth-only MAGEMin official fixtures.
# Source revision V2 fixes Julia soft-scope; no Arcana material or physical T1.
using Pkg
using TOML
using MAGEMin_C

function normalize(out)
    out.status == 0 || error("MAGEMIN_SOURCE_FIXTURE_NOT_CONVERGED")
    phases = String.(out.ph)
    fractions_wt = Float64.(out.ph_frac_wt)
    fractions_mol = Float64.(out.ph_frac)
    n = length(phases)
    n > 0 && n == length(fractions_wt) && n == length(fractions_mol) ||
        error("MAGEMIN_PHASES_MISSING")
    all(isfinite, fractions_wt) && all(x -> 0.0 <= x <= 1.0, fractions_wt) &&
        abs(sum(fractions_wt) - 1.0) < 1e-6 ||
        error("MAGEMIN_PHASE_WT_CLOSURE_BAD")
    all(isfinite, fractions_mol) && all(x -> 0.0 <= x <= 1.0, fractions_mol) &&
        abs(sum(fractions_mol) - 1.0) < 1e-6 ||
        error("MAGEMIN_PHASE_MOL_CLOSURE_BAD")
    rho = Float64(out.rho)
    G = Float64(out.G_system)
    isfinite(rho) && rho > 0 && isfinite(G) || error("MAGEMIN_THERMO_OUTPUT_INVALID")
    return Dict{String,Any}(
        "status" => Int(out.status),
        "P_kbar" => Float64(out.P_kbar),
        "T_C" => Float64(out.T_C),
        "rho_kg_m3" => rho,
        "G_system" => G,
        "phases" => phases,
        "phase_mass_fractions" => fractions_wt,
        "phase_molar_fractions" => fractions_mol,
        "database_label" => "ig"
    )
end

function run_predefined_case()
    data = Initialize_MAGEMin("ig", verbose=false)
    try
        # Official README Example 1: KLB1 at 8 kbar / 800 C.
        data = use_predefined_bulk_rock(data, 0)
        out = point_wise_minimization(8.0, 800.0, data)
        result = normalize(out)
        g_reference = -797.7873865220898
        cp_reference = 1208.466551730128
        g_delta = abs(Float64(out.G_system) - g_reference)
        cp_delta = abs(Float64(out.s_cp[1]) - cp_reference)
        (isfinite(g_delta) && g_delta < 1e-3) ||
            error("MAGEMIN_KLB1_G_REFERENCE_MISMATCH")
        (isfinite(cp_delta) && cp_delta < 2.0) ||
            error("MAGEMIN_KLB1_CP_REFERENCE_MISMATCH")
        result["KLB1_G_reference_abs_delta"] = g_delta
        result["KLB1_cp_reference_abs_delta"] = cp_delta
        return result
    finally
        Finalize_MAGEMin(data)
    end
end

function run_custom_case()
    data = Initialize_MAGEMin("ig", verbose=false)
    try
        # Official README Example 2. Preserve 99.75 wt.% as reported, not 100%.
        names = ["SiO2","Al2O3","CaO","MgO","FeO","Fe2O3",
                 "K2O","Na2O","TiO2","Cr2O3","H2O"]
        values = [48.43,15.19,11.57,10.13,6.65,1.64,
                  0.59,1.87,0.68,0.0,3.0]
        abs(sum(values) - 99.75) < 1e-10 ||
            error("MAGEMIN_COMPOSITION_QUIETLY_CHANGED")
        out = single_point_minimization(10.0, 1100.0, data;
                                         X=values, Xoxides=names, sys_in="wt")
        result = normalize(out)
        fm = Float64(out.frac_M_wt)
        fs = Float64(out.frac_S_wt)
        rho_m = Float64(out.rho_M)
        rho_s = Float64(out.rho_S)
        all(isfinite, (fm, fs, rho_m, rho_s)) &&
            fm > 0 && fs > 0 && rho_m > 0 && rho_s > 0 &&
            abs(fm + fs - 1.0) < 1e-6 ||
            error("MAGEMIN_CUSTOM_MELT_SOLID_INVALID")
        reconstructed = 1.0 / (fm / rho_m + fs / rho_s)
        closure = abs(Float64(out.rho) - reconstructed)
        isfinite(closure) && closure < 1e-10 ||
            error("MAGEMIN_CUSTOM_DENSITY_CLOSURE_INVALID")
        result["frac_M_wt"] = fm
        result["frac_S_wt"] = fs
        result["rho_M"] = rho_m
        result["rho_S"] = rho_s
        result["density_closure_abs"] = closure
        result["input_sum_as_reported_wt_percent"] = 99.75
        result["readme_quantitative_reconciliation"] = "PENDING"
        return result
    finally
        Finalize_MAGEMin(data)
    end
end

function main()
    length(ARGS) == 1 || error("Exactly one output .toml file path required")
    file = abspath(ARGS[1])
    ispath(file) && error("WRITE_ONCE_OUTPUT_EXISTS")
    entries = [x for x in values(Pkg.dependencies()) if x.name == "MAGEMin_C"]
    length(entries) == 1 || error("MAGEMIN_C_PIN_NOT_INSTALLED")
    entries[1].version == v"2.4.5" || error("MAGEMIN_C_VERSION_NOT_2_4_5")

    fixtures = Dict{String,Any}()
    fixtures["MAGEMIN_PREDEFINED_KLB1"] = run_predefined_case()
    fixtures["MAGEMIN_CUSTOM_IG"] = run_custom_case()
    report = Dict(
        "provider" => "MAGEMin_C.jl",
        "version" => "2.4.5",
        "scope" => "EARTH_OFFICIAL_FIXTURE_ONLY_NOT_ARCANA",
        "cross_provider_comparable" => false,
        "physical_T1_is_null" => true,
        "reference_test_scope" => "S1_STANDALONE_NUMERICAL",
        "fixtures" => fixtures
    )
    # Preserve legacy report fields; only write after both numerical checks.
    open(file, "w") do io
        TOML.print(io, report)
    end
    println("ARCANA_MAGEMIN_UPSTREAM_TWO_OFFICIAL_CASES=PASS")
    println("ARCANA_MAGEMIN_KLB1_NUMERICAL_REFERENCE=PASS")
    println("ARCANA_MAGEMIN_CUSTOM_DENSITY_CLOSURE=PASS")
    println("ARCANA_MAGEMIN_README_QUANTITATIVE_RECONCILIATION=PENDING")
end

main()
