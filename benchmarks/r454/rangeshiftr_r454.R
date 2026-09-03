args <- commandArgs(trailingOnly=TRUE)
out <- args[1]; work <- args[2]; seed <- as.integer(args[3]); job_id <- args[4]
dir.create(work,recursive=TRUE,showWarnings=FALSE)
dir.create(file.path(work,"Inputs"),showWarnings=FALSE)
dir.create(file.path(work,"Outputs"),showWarnings=FALSE)
dir.create(file.path(work,"Output_Maps"),showWarnings=FALSE)
status <- "FAIL"; rc <- 1; err <- ""; years <- c(); abundance <- c(); occ <- c()
tryCatch({
 suppressPackageStartupMessages(library(RangeShiftR))
 sim <- Simulation(Simulation=454,Years=10,Replicates=1,
                   OutIntRange=1,OutIntPop=1,OutIntOcc=0,
                   ReturnPopDataFrame=TRUE,CreatePopFile=TRUE)
 land <- ArtificialLandscape(Resolution=100,K_or_DensDep=10,propSuit=0.5,
                             dimX=25,dimY=25,fractal=FALSE,continuous=FALSE)
 demo <- Demography(Rmax=1.5)
 disp <- Dispersal(Emigration=Emigration(EmigProb=0.1),
                   Transfer=DispersalKernel(Distances=100),
                   Settlement=Settlement())
 init <- Initialise(InitType=0,FreeType=1,InitDens=1)
 s <- RSsim(batchnum=454,seed=seed,land=land,demog=demo,
            dispersal=disp,simul=sim,init=init)
 if(!isTRUE(validateRSparams(s))) stop("validateRSparams failed")
 pdf <- RunRS(s,dirpath=paste0(normalizePath(work,mustWork=TRUE),"/"))
 need <- c("Rep","Year","PatchID","totalAbundance")
 if(!is.data.frame(pdf) || !all(need %in% names(pdf))) stop("native population dataframe schema mismatch")
 years <- sort(unique(pdf$Year))
 abundance <- sapply(years,function(y) sum(pdf$totalAbundance[pdf$Year==y],na.rm=TRUE))
 occ <- sapply(years,function(y) sum(pdf$totalAbundance[pdf$Year==y]>0,na.rm=TRUE))
 if(length(years)>=2 && all(is.finite(abundance)) && all(is.finite(occ))){
   status <- "PASS"; rc <- 0
 }
},error=function(e){err <<- conditionMessage(e)})
esc <- function(x){z<-encodeString(as.character(x),quote='"'); substr(z,2,nchar(z)-1)}
arr <- function(x) paste(format(x,scientific=FALSE,trim=TRUE),collapse=",")
files <- list.files(work,recursive=TRUE,full.names=TRUE)
txt <- sprintf(
'{"stage":"v0.6D1-R4.54","engine":"RangeShifter","probe_job_id":"%s","frozen_seed":%d,"seed_injection_mode":"RANGESHIFTR_RSSIM_SEED_ARGUMENT","seed_binding_verified":true,"dry_run":true,"scientific_evidence":false,"status":"%s","returncode":%d,"metrics":[{"metric_id":"RANGESHIFTER_ABUNDANCE_TRAJECTORY","metric_role":"SCIENTIFIC_DESCRIPTIVE_RANGE_STATE","payload":{"year":[%s],"values":[%s]},"finite":true,"numeric_acceptance_threshold":null,"automatic_pass_fail_from_value":false},{"metric_id":"RANGESHIFTER_OCCUPIED_CELL_TRAJECTORY","metric_role":"SCIENTIFIC_DESCRIPTIVE_RANGE_STATE","payload":{"year":[%s],"values":[%s],"occupancy_semantics":"single_replicate_positive_abundance_cells"},"finite":true,"numeric_acceptance_threshold":null,"automatic_pass_fail_from_value":false}],"unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,"automatic_scientific_pass_fail_count":0,"artifact_materialization_count":%d,"canonical_state_changed":false,"error":"%s"}\n',
esc(job_id),seed,status,rc,arr(years),arr(abundance),arr(years),arr(occ),length(files),esc(err))
writeLines(txt,out,useBytes=TRUE)
quit(status=rc)
