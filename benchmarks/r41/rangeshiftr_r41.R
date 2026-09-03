args <- commandArgs(trailingOnly=TRUE)
out <- args[1]
work <- args[2]
dir.create(work, recursive=TRUE, showWarnings=FALSE)
dir.create(file.path(work,'Inputs'), showWarnings=FALSE)
dir.create(file.path(work,'Outputs'), showWarnings=FALSE)
dir.create(file.path(work,'Output_Maps'), showWarnings=FALSE)
status <- "FAIL"; rc <- 1; err <- ""; metrics <- list()
tryCatch({
  suppressPackageStartupMessages(library(RangeShiftR))
  # R4.1 uses a complete, explicit parameter master. RangeShiftR 3.0.1
  # requires Replicates > 1 only for its dedicated cross-replicate Occupancy
  # output. On the governed Linux runtime, that multi-replicate path segfaulted
  # after a successful first replicate. For the semantic microbenchmark we
  # instead request the native per-year population dataframe for ONE replicate
  # and derive occupied cells directly as count(totalAbundance > 0). This keeps
  # the benchmark on an engine-native executable path without claiming that
  # single-run occupancy equals RangeShiftR's multi-replicate occupancy output.
  sim <- Simulation(Simulation=41, Years=10, Replicates=1,
                    OutIntRange=1, OutIntPop=1, OutIntOcc=0,
                    ReturnPopDataFrame=TRUE, CreatePopFile=TRUE)
  land <- ArtificialLandscape(Resolution=100, K_or_DensDep=10,
                              propSuit=0.5, dimX=25, dimY=25,
                              fractal=FALSE, continuous=FALSE)
  demo <- Demography(Rmax=1.5)
  disp <- Dispersal(Emigration=Emigration(EmigProb=0.1),
                    Transfer=DispersalKernel(Distances=100),
                    Settlement=Settlement())
  init <- Initialise(InitType=0, FreeType=1, InitDens=1)
  s <- RSsim(batchnum=41, seed=410041, land=land, demog=demo,
             dispersal=disp, simul=sim, init=init)
  valid <- validateRSparams(s)
  if(!isTRUE(valid)) stop('validateRSparams() did not return TRUE')
  pdf <- RunRS(s, dirpath=paste0(normalizePath(work,mustWork=TRUE),'/'))
  if(!is.data.frame(pdf)) stop('RunRS did not return a population data.frame')
  need <- c('Rep','Year','PatchID','totalAbundance')
  if(!all(need %in% names(pdf))) stop('RunRS population data.frame missing required columns')
  if(nrow(pdf)<2) stop('RunRS population data.frame returned fewer than two rows')
  y0 <- min(pdf$Year); y1 <- max(pdf$Year)
  p0 <- pdf[pdf$Year==y0,,drop=FALSE]
  p1 <- pdf[pdf$Year==y1,,drop=FALSE]
  metrics <- list(
    initial_abundance=as.numeric(sum(p0$totalAbundance, na.rm=TRUE)),
    final_abundance=as.numeric(sum(p1$totalAbundance, na.rm=TRUE)),
    initial_occupied_cells=as.integer(sum(p0$totalAbundance>0, na.rm=TRUE)),
    final_occupied_cells=as.integer(sum(p1$totalAbundance>0, na.rm=TRUE)),
    years=as.integer(y1-y0),
    replicates=1L,
    parameter_master_valid=TRUE,
    occupancy_semantics='single_replicate_positive_abundance_cells',
    dedicated_multi_replicate_occupancy_output=FALSE
  )
  if(metrics$initial_abundance>0 && metrics$final_abundance>0 &&
     metrics$initial_occupied_cells>0 && metrics$final_occupied_cells>0 &&
     metrics$years>=1){status <- 'PASS'; rc <- 0}
}, error=function(e){err <<- conditionMessage(e)})
json_escape <- function(x) {
  z <- encodeString(as.character(x), quote='"')
  substr(z, 2, nchar(z)-1)
}
if(length(metrics)==0){
 txt <- sprintf('{"status":"%s","returncode":%d,"metrics":{},"error":"%s"}\n',status,rc,json_escape(err))
} else {
 txt <- sprintf('{"status":"%s","returncode":%d,"metrics":{"initial_abundance":%.12g,"final_abundance":%.12g,"initial_occupied_cells":%d,"final_occupied_cells":%d,"years":%d,"replicates":%d,"parameter_master_valid":true,"occupancy_semantics":"%s","dedicated_multi_replicate_occupancy_output":false},"error":"%s"}\n',status,rc,metrics$initial_abundance,metrics$final_abundance,metrics$initial_occupied_cells,metrics$final_occupied_cells,metrics$years,metrics$replicates,json_escape(metrics$occupancy_semantics),json_escape(err))
}
writeLines(txt,out,useBytes=TRUE)
quit(status=rc)
