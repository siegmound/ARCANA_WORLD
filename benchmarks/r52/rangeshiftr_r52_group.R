args <- commandArgs(trailingOnly=TRUE)
if(length(args) < 3) stop("usage: rangeshiftr_r52_group.R <group_dir> <group_numeric_id> <group_id>")
work <- normalizePath(args[1], mustWork=TRUE)
group_num <- as.integer(args[2])
group_id <- args[3]
inputs <- file.path(work,"Inputs")
evidence <- file.path(work,"Evidence")
dir.create(file.path(work,"Outputs"),showWarnings=FALSE,recursive=TRUE)
dir.create(file.path(work,"Output_Maps"),showWarnings=FALSE,recursive=TRUE)
dir.create(evidence,showWarnings=FALSE,recursive=TRUE)

clean_text <- function(x){ x <- gsub("[\\r\\n\\t]+"," ",as.character(x)); x }
summary_file <- file.path(evidence,"STREAM_SUMMARY.tsv")
header <- c("group_id","movement_profile","characteristic_distance","seed","execution_status","package_version","initialization_mode","engine_years","completed_engine_years","global_extinction_before_final","initial_abundance","final_abundance","initial_occupied_cells","final_occupied_cells","occupancy_file","error")
writeLines(paste(header,collapse="\t"),summary_file,useBytes=TRUE)

all_ok <- TRUE
tryCatch({
  suppressPackageStartupMessages(library(RangeShiftR))
  pv <- as.character(packageVersion("RangeShiftR"))
  if(pv != "3.0.1") stop(sprintf("RangeShiftR 3.0.1 required, got %s",pv))

  lands <- sort(list.files(inputs,pattern="^habitat_[0-9]{3}\\.asc$",full.names=FALSE))
  if(length(lands) < 2) stop("Need at least two dynamic landscape states")
  years <- length(lands)-1L
  if(!file.exists(file.path(inputs,"source.asc"))) stop("source.asc missing")

  movement_names <- c("D1_STANDARDIZED_1_CELL_CHARACTERISTIC","D2_STANDARDIZED_2_CELL_CHARACTERISTIC")
  movement_dist <- c(100.0,200.0)
  seeds <- c(520201L,520202L)
  stream_idx <- 0L
  for(mi in seq_along(movement_names)){
    for(seed in seeds){
      stream_idx <- stream_idx + 1L
      simid <- group_num*10L + stream_idx
      batchnum <- 520000L + group_num
      occ_name <- sprintf("occupancy_%s_seed%d.tsv.gz",if(mi==1) "D1" else "D2",seed)
      occ_path <- file.path(evidence,occ_name)
      st <- "FAIL"; er <- ""; ia <- 0; fa <- 0; io <- 0L; fo <- 0L; completed <- 0L; extinct_early <- FALSE
      tryCatch({
        sim <- Simulation(Simulation=simid, Years=years, Replicates=1,
                          OutIntRange=1, OutIntPop=1, OutIntOcc=0,
                          ReturnPopDataFrame=TRUE, CreatePopFile=TRUE)
        land <- ImportedLandscape(LandscapeFile=lands,
                                  DynamicLandYears=0:years,
                                  Nhabitats=2,
                                  Resolution=100,
                                  K_or_DensDep=c(10,0),
                                  SpDistFile="source.asc",
                                  SpDistResolution=100)
        demo <- Demography(Rmax=1.5)
        disp <- Dispersal(Emigration=Emigration(EmigProb=0.1),
                          Transfer=DispersalKernel(Distances=movement_dist[mi]),
                          Settlement=Settlement())
        # R5.2-R1: source authority is the ARCANA-derived SpDistFile.  InitType=1 is
        # required to initialise from that loaded species-distribution map; InitType=0
        # would free-initialise suitable habitat and invalidate the frozen origin mask.
        init <- Initialise(InitType=1, SpType=0, InitDens=1)
        s <- RSsim(batchnum=batchnum, seed=seed, land=land, demog=demo,
                   dispersal=disp, simul=sim, init=init)
        valid <- validateRSparams(s)
        if(!isTRUE(valid)) stop("validateRSparams() did not return TRUE")
        invisible(RunRS(s, dirpath=paste0(work,"/")))

        pop_pattern <- sprintf("Batch%d_Sim%d_Land1_Pop\\.txt$",batchnum,simid)
        range_pattern <- sprintf("Batch%d_Sim%d_Land1_Range\\.txt$",batchnum,simid)
        pop_files <- list.files(file.path(work,"Outputs"),pattern=pop_pattern,full.names=TRUE)
        range_files <- list.files(file.path(work,"Outputs"),pattern=range_pattern,full.names=TRUE)
        if(length(pop_files)!=1) stop(sprintf("Expected one Pop file, got %d",length(pop_files)))
        if(length(range_files)!=1) stop(sprintf("Expected one Range file, got %d",length(range_files)))
        pop <- read.delim(pop_files[1],check.names=FALSE)
        rng <- read.delim(range_files[1],check.names=FALSE)
        needp <- c("Year","x","y","NInd"); needr <- c("Year")
        if(!all(needp %in% names(pop))) stop("Pop output missing Year/x/y/NInd")
        if(!all(needr %in% names(rng))) stop("Range output missing Year")
        completed <- as.integer(max(rng$Year,na.rm=TRUE))
        p0 <- pop[pop$Year==0,,drop=FALSE]
        pf <- pop[pop$Year==years,,drop=FALSE]
        ia <- sum(p0$NInd,na.rm=TRUE); fa <- if(nrow(pf)) sum(pf$NInd,na.rm=TRUE) else 0
        io <- sum(p0$NInd>0,na.rm=TRUE); fo <- if(nrow(pf)) sum(pf$NInd>0,na.rm=TRUE) else 0L
        extinct_early <- (completed < years && max(pop$Year,na.rm=TRUE) <= completed && sum(pop[pop$Year==completed,"NInd"],na.rm=TRUE) <= 0) || (completed < years && nrow(pop[pop$Year==completed,,drop=FALSE])==0)
        con <- gzfile(occ_path,"wt")
        write.table(pop[,needp,drop=FALSE],con,sep="\t",row.names=FALSE,col.names=TRUE,quote=FALSE)
        close(con)
        st <- "PASS"
      }, error=function(e){ er <<- conditionMessage(e); all_ok <<- FALSE })
      vals <- c(group_id,movement_names[mi],format(movement_dist[mi],scientific=FALSE),as.character(seed),st,pv,"SPDIST_INITTYPE1_SPTYPE0",as.character(years),as.character(completed),as.character(extinct_early),
                format(ia,scientific=FALSE),format(fa,scientific=FALSE),as.character(io),as.character(fo),if(st=="PASS") occ_name else "",clean_text(er))
      cat(paste(vals,collapse="\t"),"\n",file=summary_file,append=TRUE,sep="")
    }
  }
}, error=function(e){
  all_ok <<- FALSE
  er <- clean_text(conditionMessage(e))
  # If setup failed before stream rows were emitted, emit the four frozen stream identities as FAIL.
  current <- readLines(summary_file,warn=FALSE)
  if(length(current)==1){
    for(m in c("D1_STANDARDIZED_1_CELL_CHARACTERISTIC","D2_STANDARDIZED_2_CELL_CHARACTERISTIC")){
      dist <- if(grepl("D1_",m)) 100 else 200
      for(seed in c(520201L,520202L)){
        vals <- c(group_id,m,as.character(dist),as.character(seed),"FAIL","","SPDIST_INITTYPE1_SPTYPE0", "", "", "FALSE", "0","0","0","0","",er)
        cat(paste(vals,collapse="\t"),"\n",file=summary_file,append=TRUE,sep="")
      }
    }
  }
})
quit(status=if(all_ok) 0 else 3)
