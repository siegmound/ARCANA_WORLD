args <- commandArgs(trailingOnly=TRUE)
out <- args[1]
status <- "FAIL"; version <- ""; libpath <- ""; err <- ""
tryCatch({
  suppressPackageStartupMessages(library(RangeShiftR))
  version <- as.character(packageVersion("RangeShiftR"))
  libpath <- find.package("RangeShiftR")
  if(version != "3.0.1") stop(sprintf("RangeShiftR exact version 3.0.1 required, got %s", version))
  status <- "PASS"
}, error=function(e){ err <<- conditionMessage(e) })
json_escape <- function(x) {
  z <- encodeString(as.character(x), quote='"')
  substr(z, 2, nchar(z)-1)
}
txt <- sprintf('{"stage":"v0.6D1-R5.2","status":"%s","package":"RangeShiftR","package_version":"%s","library_path":"%s","r_version":"%s","error":"%s"}\n',
               if(status=="PASS") "PASS_R52_RANGESHIFTR_3_0_1_RUNTIME_IDENTITY" else "BLOCKED_R52_RANGESHIFTR_RUNTIME_IDENTITY",
               json_escape(version), json_escape(libpath), json_escape(R.version.string), json_escape(err))
writeLines(txt,out,useBytes=TRUE)
quit(status=if(status=="PASS") 0 else 2)
