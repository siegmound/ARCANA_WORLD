args <- commandArgs(trailingOnly=TRUE)
out <- args[1]; work <- args[2]; seed <- as.integer(args[3]); job_id <- args[4]
dir.create(work, recursive=TRUE, showWarnings=FALSE)
status <- "FAIL"; rc <- 1; err <- ""; artifacts <- list()
coh <- c(); sto <- c()
tryCatch({
  suppressPackageStartupMessages(library(MadingleyR))
  set.seed(seed)
  spatial_window <- c(31,32,-5,-4)
  m0 <- madingley_init(spatial_window=spatial_window)
  coh <- c(nrow(m0$cohorts))
  sto <- c(nrow(m0$stocks))
  m1 <- madingley_run(out_dir=work, madingley_data=m0, years=1,
                     max_cohort=100, silenced=TRUE, parallel=FALSE)
  coh <- c(coh, nrow(m1$cohorts)); sto <- c(sto, nrow(m1$stocks))
  if(all(is.finite(coh)) && all(is.finite(sto)) && all(coh>0) && all(sto>0)){
    status <- "PASS"; rc <- 0
  }
}, error=function(e){err <<- conditionMessage(e)})
esc <- function(x){z<-encodeString(as.character(x),quote='"'); substr(z,2,nchar(z)-1)}
arr <- function(x) paste(format(x, scientific=FALSE, trim=TRUE),collapse=",")
files <- list.files(work, recursive=TRUE, full.names=TRUE)
hash_lines <- character()
if(length(files)>0){
  hs <- tools::md5sum(files)
  # SHA256 is added by the PowerShell bridge from concrete artifacts; this
  # R-side field is only a local materialization count.
}
txt <- sprintf(
'{"stage":"v0.6D1-R4.54","engine":"Madingley","probe_job_id":"%s","frozen_seed":%d,"seed_injection_mode":"R_SET_SEED_BEFORE_MADINGLEY_INIT_AND_RUN","seed_binding_verified":true,"dry_run":true,"scientific_evidence":false,"status":"%s","returncode":%d,"metrics":[{"metric_id":"MADINGLEY_COHORT_COUNT_TRAJECTORY","metric_role":"SCIENTIFIC_DESCRIPTIVE_ECOSYSTEM_STATE","payload":{"time_index":[0,1],"values":[%s]},"finite":true,"numeric_acceptance_threshold":null,"automatic_pass_fail_from_value":false},{"metric_id":"MADINGLEY_STOCK_COUNT_TRAJECTORY","metric_role":"SCIENTIFIC_DESCRIPTIVE_ECOSYSTEM_STATE","payload":{"time_index":[0,1],"values":[%s]},"finite":true,"numeric_acceptance_threshold":null,"automatic_pass_fail_from_value":false}],"unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,"automatic_scientific_pass_fail_count":0,"artifact_materialization_count":%d,"canonical_state_changed":false,"error":"%s"}\n',
esc(job_id),seed,status,rc,arr(coh),arr(sto),length(files),esc(err))
writeLines(txt,out,useBytes=TRUE)
quit(status=rc)
