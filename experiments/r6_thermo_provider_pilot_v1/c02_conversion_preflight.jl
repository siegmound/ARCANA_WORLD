# Conversion only. No Initialize_MAGEMin, no minimization.
using MAGEMin_C, TOML, SHA, Pkg
function blob(path)
    raw=read(path)
    bytes2hex(sha1(vcat(Vector{UInt8}(codeunits("blob "*string(length(raw))*"\0")),raw)))
end
length(ARGS)==2 || error("C02_ARGS")
inp=TOML.parsefile(ARGS[1])
pkg=[x for x in values(Pkg.dependencies()) if x.name=="MAGEMin_C"]
length(pkg)==1 && pkg[1].version==v"2.4.5" || error("C02_PACKAGE_DRIFT")
dir=joinpath(dirname(dirname(pathof(MAGEMin_C))),"julia")
w=blob(joinpath(dir,"MAGEMin_wrappers.jl"))
i=blob(joinpath(dir,"db_infos_generated.jl"))
r=blob(joinpath(dir,"database_registry.jl"))
w==inp["wrapper_git_blob"] && i=="a4e89099410933577ebd182732705ab472d090cb" && r=="887cba5331efcf8adff81555f8a58dcd07e59c90" || error("C02_PROVIDER_SOURCE_DRIFT")
v,ox=convertBulk4MAGEMin(Float64.(inp["wt_amounts"]),String.(inp["names"]),"wt","ig")
path=joinpath(ARGS[2],"CONVERSION.toml")
!ispath(path) || error("C02_OUTPUT_EXISTS")
open(path,"w") do io
    TOML.print(io,Dict("oxides"=>ox,"mol_fraction"=>Float64.(v)./100,
        "wrapper_git_blob"=>w,"info_git_blob"=>i,"registry_git_blob"=>r,"minimization_calls"=>0))
end
