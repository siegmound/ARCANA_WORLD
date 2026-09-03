args <- commandArgs(trailingOnly=TRUE)
cfg_path <- args[1]; out <- args[2]; work <- args[3]
dir.create(work, recursive=TRUE, showWarnings=FALSE)
kv <- read.delim(cfg_path, header=FALSE, sep='\t', quote='', stringsAsFactors=FALSE, fill=TRUE)
getv <- function(k, default=NA) { x <- kv[kv$V1==k,2]; if(length(x)==0) return(default); x[[1]] }
asnum <- function(k,d=0) as.numeric(getv(k,d)); asint <- function(k,d=0) as.integer(round(asnum(k,d)))
json_escape <- function(x) { z <- encodeString(as.character(x), quote='"'); substr(z,2,nchar(z)-1) }
rep_count <- asint('replicate_count',4); years <- asint('runtime_steps',10)
p0 <- max(0.1,min(0.9,asnum('normalized_habitat_fraction_start',0.5)))
p1 <- max(0.1,min(0.9,asnum('normalized_habitat_fraction_end',0.5)))
conn <- max(0.05,min(0.95,asnum('normalized_connectivity_start',0.5)))
emig <- max(0.02,min(0.3,0.30*(1-conn)+0.02))
dist <- 50 + 250*conn
reps_json <- c(); all_ok <- TRUE
run_condition <- function(dirp, seed, prop, batch) {
  dir.create(dirp, recursive=TRUE, showWarnings=FALSE)
  dir.create(file.path(dirp,'Inputs'), showWarnings=FALSE)
  dir.create(file.path(dirp,'Outputs'), showWarnings=FALSE)
  dir.create(file.path(dirp,'Output_Maps'), showWarnings=FALSE)
  sim <- Simulation(Simulation=batch, Years=years+1, Replicates=1, OutIntRange=1, OutIntPop=1, OutIntOcc=0, ReturnPopDataFrame=TRUE, CreatePopFile=TRUE)
  land <- ArtificialLandscape(Resolution=100, K_or_DensDep=10, propSuit=prop, dimX=25, dimY=25, fractal=FALSE, continuous=FALSE)
  demo <- Demography(Rmax=1.5)
  disp <- Dispersal(Emigration=Emigration(EmigProb=emig), Transfer=DispersalKernel(Distances=dist), Settlement=Settlement())
  init <- Initialise(InitType=0, FreeType=1, InitDens=1)
  s <- RSsim(batchnum=batch, seed=seed, land=land, demog=demo, dispersal=disp, simul=sim, init=init)
  if(!isTRUE(validateRSparams(s))) stop('validateRSparams failed')
  pdf <- RunRS(s, dirpath=paste0(normalizePath(dirp,mustWork=TRUE),'/'))
  if(!is.data.frame(pdf)) stop('RunRS did not return data.frame')
  y <- max(pdf$Year); pf <- pdf[pdf$Year==y,,drop=FALSE]
  c(abundance=sum(pf$totalAbundance,na.rm=TRUE), occupied=sum(pf$totalAbundance>0,na.rm=TRUE), final_year=y)
}
tryCatch({
  suppressPackageStartupMessages(library(RangeShiftR))
  for(i in 0:(rep_count-1)) {
    seed <- asint(paste0('seed_',i),410000+i)
    rw <- file.path(work,sprintf('rep_%03d',i)); if(dir.exists(rw)) unlink(rw,recursive=TRUE,force=TRUE); dir.create(rw,recursive=TRUE)
    ok <- TRUE; err <- ''; a <- NULL; b <- NULL
    tryCatch({
      a <- run_condition(file.path(rw,'start'),seed,p0,4300+i*2)
      b <- run_condition(file.path(rw,'end'),seed,p1,4301+i*2)
    }, error=function(e){ ok <<- FALSE; err <<- conditionMessage(e) })
    if(ok) {
      js <- sprintf('{"replicate_index":%d,"seed":%d,"status":"PASS","returncode":0,"metrics":{"initial_abundance":%.12g,"final_abundance":%.12g,"initial_occupied_cells":%d,"final_occupied_cells":%d,"representative_years":%d,"start_habitat_fraction":%.12g,"end_habitat_fraction":%.12g,"emigration_probability":%.12g,"dispersal_distance":%.12g,"occupancy_semantics":"paired_single_replicate_positive_abundance_cells"}}', i,seed,a[['abundance']],b[['abundance']],as.integer(a[['occupied']]),as.integer(b[['occupied']]),years,p0,p1,emig,dist)
    } else {
      all_ok <- FALSE
      js <- sprintf('{"replicate_index":%d,"seed":%d,"status":"FAIL","returncode":1,"metrics":{},"error":"%s"}',i,seed,json_escape(err))
    }
    reps_json <- c(reps_json,js)
  }
}, error=function(e){ all_ok <<- FALSE; reps_json <<- c(reps_json,sprintf('{"replicate_index":-1,"seed":0,"status":"FAIL","returncode":1,"metrics":{},"error":"%s"}',json_escape(conditionMessage(e)))) })
status <- if(all_ok && length(reps_json)==rep_count) 'PASS' else 'ENGINE_EXECUTION_FAILURE'
txt <- sprintf('{"stage":"v0.6D1-R4.3","job_id":"%s","engine":"RangeShifter","adapter_status":"%s","driver_application":"paired_start_end_habitat_support_response","occupancy_semantics":"single_replicate_positive_abundance_cells_not_dedicated_multi_rep_occupancy","replicates":[%s],"canonical_write":false}\n',json_escape(getv('job_id','')),status,paste(reps_json,collapse=','))
writeLines(txt,out,useBytes=TRUE)
quit(status=if(status=='PASS') 0 else 1)
