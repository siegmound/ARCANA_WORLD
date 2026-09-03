args <- commandArgs(trailingOnly=TRUE)
if(length(args) < 1) stop("usage: probe_rangeshiftr_r52_source_binding.R <probe_dir>")
work <- normalizePath(args[1], mustWork=TRUE)
inputs <- file.path(work,"Inputs")
evidence <- file.path(work,"Evidence")
dir.create(file.path(work,"Outputs"),showWarnings=FALSE,recursive=TRUE)
dir.create(file.path(work,"Output_Maps"),showWarnings=FALSE,recursive=TRUE)
dir.create(evidence,showWarnings=FALSE,recursive=TRUE)

suppressPackageStartupMessages(library(RangeShiftR))
pv <- as.character(packageVersion("RangeShiftR"))
if(pv != "3.0.1") stop(sprintf("RangeShiftR 3.0.1 required, got %s",pv))
if(!file.exists(file.path(inputs,"habitat_000.asc"))) stop("habitat_000.asc missing")
if(!file.exists(file.path(inputs,"source.asc"))) stop("source.asc missing")

sim <- Simulation(Simulation=52991, Years=1, Replicates=1,
                  OutIntRange=1, OutIntPop=1, OutIntOcc=0,
                  ReturnPopDataFrame=TRUE, CreatePopFile=TRUE)
land <- ImportedLandscape(LandscapeFile="habitat_000.asc",
                          Nhabitats=2, Resolution=100,
                          K_or_DensDep=c(10,0),
                          SpDistFile="source.asc", SpDistResolution=100)
demo <- Demography(Rmax=1.5)
disp <- Dispersal(Emigration=Emigration(EmigProb=0.1),
                  Transfer=DispersalKernel(Distances=100.0),
                  Settlement=Settlement())
# Exact R5.2-R1 source binding: initialise from loaded SpDistFile.
init <- Initialise(InitType=1, SpType=0, InitDens=1)
s <- RSsim(batchnum=52991, seed=520201L, land=land, demog=demo,
           dispersal=disp, simul=sim, init=init)
if(!isTRUE(validateRSparams(s))) stop("validateRSparams() did not return TRUE")
invisible(RunRS(s, dirpath=paste0(work,"/")))
pop_files <- list.files(file.path(work,"Outputs"),pattern="Batch52991_Sim52991_Land1_Pop\\.txt$",full.names=TRUE)
if(length(pop_files)!=1) stop(sprintf("Expected one probe Pop file, got %d",length(pop_files)))
pop <- read.delim(pop_files[1],check.names=FALSE)
need <- c("Year","x","y","NInd")
if(!all(need %in% names(pop))) stop("Probe Pop output missing Year/x/y/NInd")
write.table(pop[,need,drop=FALSE], file.path(evidence,"SOURCE_BINDING_PROBE.tsv"),
            sep="\t",row.names=FALSE,col.names=TRUE,quote=FALSE)
