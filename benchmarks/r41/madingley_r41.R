args <- commandArgs(trailingOnly=TRUE)
out <- args[1]
work <- args[2]
dir.create(work, recursive=TRUE, showWarnings=FALSE)
status <- "FAIL"
rc <- 1
err <- ""
metrics <- list()
tryCatch({
  suppressPackageStartupMessages(library(MadingleyR))
  spatial_window <- c(31, 32, -5, -4)
  m0 <- madingley_init(spatial_window=spatial_window)
  m1 <- madingley_run(out_dir=work, madingley_data=m0, years=1, max_cohort=100, silenced=TRUE, parallel=FALSE)
  metrics <- list(
    initial_cohort_count=nrow(m0$cohorts),
    final_cohort_count=nrow(m1$cohorts),
    initial_stock_count=nrow(m0$stocks),
    final_stock_count=nrow(m1$stocks),
    years=1
  )
  if(metrics$initial_cohort_count>0 && metrics$final_cohort_count>0 && metrics$initial_stock_count>0 && metrics$final_stock_count>0){status <- "PASS"; rc <- 0}
}, error=function(e){err <<- conditionMessage(e)})
json_escape <- function(x) {
  z <- encodeString(as.character(x), quote='"')
  substr(z, 2, nchar(z)-1)
}
if(length(metrics)==0){
  txt <- sprintf('{"status":"%s","returncode":%d,"metrics":{},"error":"%s"}\n',status,rc,json_escape(err))
} else {
  txt <- sprintf('{"status":"%s","returncode":%d,"metrics":{"initial_cohort_count":%d,"final_cohort_count":%d,"initial_stock_count":%d,"final_stock_count":%d,"years":1},"error":"%s"}\n',status,rc,metrics$initial_cohort_count,metrics$final_cohort_count,metrics$initial_stock_count,metrics$final_stock_count,json_escape(err))
}
writeLines(txt,out,useBytes=TRUE)
quit(status=rc)
