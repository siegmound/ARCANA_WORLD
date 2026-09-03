args <- commandArgs(trailingOnly=TRUE)
cfg_path <- args[1]; out <- args[2]; work <- args[3]
dir.create(work, recursive=TRUE, showWarnings=FALSE)
kv <- read.delim(cfg_path, header=FALSE, sep='\t', quote='', stringsAsFactors=FALSE, fill=TRUE)
getv <- function(k, default=NA) { x <- kv[kv$V1==k,2]; if(length(x)==0) return(default); x[[1]] }
asnum <- function(k,d=0) as.numeric(getv(k,d)); asint <- function(k,d=0) as.integer(round(asnum(k,d)))
json_escape <- function(x) { z <- encodeString(as.character(x), quote='"'); substr(z,2,nchar(z)-1) }
rep_count <- asint('replicate_count',4); years <- asint('runtime_steps',3)
env_delta <- max(-1,min(1,asnum('normalized_environment_change',0)))
end_factor <- max(0.6,min(1.4,1+0.35*env_delta))
reps_json <- c(); all_ok <- TRUE
sum_hetero <- function(m) {
  tl <- m$time_line_cohorts
  if(is.null(tl) || nrow(tl)==0) return(NA_real_)
  cols <- grep('^Biomass_FG_', names(tl), value=TRUE)
  if(length(cols)==0) return(NA_real_)
  sum(as.numeric(tl[nrow(tl),cols]),na.rm=TRUE)
}
sum_auto <- function(m) {
  tl <- m$time_line_stocks
  if(is.null(tl) || nrow(tl)==0) return(NA_real_)
  if('TotalStockBiomass' %in% names(tl)) return(as.numeric(tl$TotalStockBiomass[nrow(tl)]))
  cols <- grep('Biomass',names(tl),value=TRUE); if(length(cols)==0) return(NA_real_)
  sum(as.numeric(tl[nrow(tl),cols]),na.rm=TRUE)
}
tryCatch({
  suppressPackageStartupMessages(library(MadingleyR))
  spatial_window <- c(31,32,-5,-4)
  for(i in 0:(rep_count-1)) {
    seed <- asint(paste0('seed_',i),420000+i); set.seed(seed)
    rw <- file.path(work,sprintf('rep_%03d',i)); if(dir.exists(rw)) unlink(rw,recursive=TRUE,force=TRUE); dir.create(rw,recursive=TRUE)
    ok <- TRUE; err <- ''; metrics <- list()
    tryCatch({
      sptl0 <- madingley_inputs('spatial inputs'); sptl1 <- madingley_inputs('spatial inputs')
      # Normalized ARCANA exogenous productivity response. Absolute ARCANA climate is NOT mapped to Earth values.
      sptl1[['terrestrial_net_primary_productivity']] <- sptl1[['terrestrial_net_primary_productivity']] * end_factor
      start_dir <- file.path(rw,'start'); end_dir <- file.path(rw,'end')
      dir.create(start_dir,recursive=TRUE,showWarnings=FALSE); dir.create(end_dir,recursive=TRUE,showWarnings=FALSE)
      m0 <- madingley_init(spatial_window=spatial_window, spatial_inputs=sptl0, max_cohort=100)
      set.seed(seed); m1 <- madingley_run(out_dir=start_dir, madingley_data=m0, spatial_inputs=sptl0, years=years, max_cohort=100, silenced=TRUE, parallel=FALSE)
      m0b <- madingley_init(spatial_window=spatial_window, spatial_inputs=sptl1, max_cohort=100)
      set.seed(seed); m2 <- madingley_run(out_dir=end_dir, madingley_data=m0b, spatial_inputs=sptl1, years=years, max_cohort=100, silenced=TRUE, parallel=FALSE)
      metrics <- list(initial_cohort_count=nrow(m1$cohorts), final_cohort_count=nrow(m2$cohorts), initial_stock_count=nrow(m1$stocks), final_stock_count=nrow(m2$stocks), initial_heterotroph_biomass=sum_hetero(m1), final_heterotroph_biomass=sum_hetero(m2), initial_autotroph_biomass=sum_auto(m1), final_autotroph_biomass=sum_auto(m2))
      if(any(!is.finite(c(metrics$initial_heterotroph_biomass,metrics$final_heterotroph_biomass,metrics$initial_autotroph_biomass,metrics$final_autotroph_biomass)))) stop('Madingley biomass timeline unavailable')
    }, error=function(e){ ok <<- FALSE; err <<- conditionMessage(e) })
    if(ok) {
      js <- sprintf('{"replicate_index":%d,"seed":%d,"status":"PASS","returncode":0,"metrics":{"initial_cohort_count":%d,"final_cohort_count":%d,"initial_stock_count":%d,"final_stock_count":%d,"initial_heterotroph_biomass":%.12g,"final_heterotroph_biomass":%.12g,"initial_autotroph_biomass":%.12g,"final_autotroph_biomass":%.12g,"npp_response_factor":%.12g,"representative_years":%d}}',i,seed,metrics$initial_cohort_count,metrics$final_cohort_count,metrics$initial_stock_count,metrics$final_stock_count,metrics$initial_heterotroph_biomass,metrics$final_heterotroph_biomass,metrics$initial_autotroph_biomass,metrics$final_autotroph_biomass,end_factor,years)
    } else { all_ok <- FALSE; js <- sprintf('{"replicate_index":%d,"seed":%d,"status":"FAIL","returncode":1,"metrics":{},"error":"%s"}',i,seed,json_escape(err)) }
    reps_json <- c(reps_json,js)
  }
}, error=function(e){ all_ok <<- FALSE; reps_json <<- c(reps_json,sprintf('{"replicate_index":-1,"seed":0,"status":"FAIL","returncode":1,"metrics":{},"error":"%s"}',json_escape(conditionMessage(e)))) })
status <- if(all_ok && length(reps_json)==rep_count) 'PASS' else 'ENGINE_EXECUTION_FAILURE'
txt <- sprintf('{"stage":"v0.6D1-R4.3","job_id":"%s","engine":"Madingley","adapter_status":"%s","driver_application":"normalized_NPP_boundary_response_factor","spatial_semantics":"Earth_reference_window_functional_proxy_not_ARCANA_geography","replicates":[%s],"canonical_write":false}\n',json_escape(getv('job_id','')),status,paste(reps_json,collapse=','))
writeLines(txt,out,useBytes=TRUE)
quit(status=if(status=='PASS') 0 else 1)
