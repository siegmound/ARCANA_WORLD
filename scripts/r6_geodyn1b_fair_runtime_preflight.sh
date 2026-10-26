#!/usr/bin/env bash
# GEODYN-1B FAIR runtime readiness probe.
# Read-only: no install, compile, module load, solver run, or output file creation.
set -u

printf 'GEODYN1B_PREFLIGHT_SCHEMA=1\n'
printf 'PREFLIGHT_UTC=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>&1)"
printf 'HOST=%s\n' "$(hostname 2>&1)"
printf 'KERNEL=%s\n' "$(uname -sr 2>&1)"
printf 'OS_RELEASE=%s\n' "$(uname -a 2>&1)"
printf 'ARCH=%s\n' "$(uname -m 2>&1)"
printf 'PWD=%s\n' "$PWD"
printf 'USER=%s\n' "${USER:-UNKNOWN}"
printf 'HOME=%s\n' "${HOME:-UNKNOWN}"

section() { printf '\n[%s]\n' "$1"; }
probe() {
  label=$1; shift
  tool=$1
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s_PATH=%s\n' "$label" "$(command -v "$tool")"
    output=$("$@" 2>&1); rc=$?
    printf '%s_EXIT=%s\n' "$label" "$rc"
    printf '%s_OUTPUT_BEGIN\n' "$label"
    printf '%s\n' "$output" | sed -n '1,12p'
    printf '%s_OUTPUT_END\n' "$label"
  else
    printf '%s=NOT_FOUND\n' "$label"
  fi
}
show_env() {
  name=$1
  eval 'value=${'"$name"'-}'
  if [ -n "$value" ]; then printf '%s=%s\n' "$name" "$value"; else printf '%s=UNSET\n' "$name"; fi
}

section SOFTWARE
if command -v aspect >/dev/null 2>&1; then
  ASPECT_BIN=$(command -v aspect)
  printf 'ASPECT_FOUND=yes\nASPECT_PATH=%s\n' "$ASPECT_BIN"
  if command -v readlink >/dev/null 2>&1; then printf 'ASPECT_REALPATH=%s\n' "$(readlink -f "$ASPECT_BIN" 2>&1)"; fi
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$ASPECT_BIN" 2>&1 | sed -n '1,2p'; else printf 'ASPECT_BINARY_SHA256=sha256sum_not_available\n'; fi
  if command -v timeout >/dev/null 2>&1; then
    aspect_output=$(timeout 10s "$ASPECT_BIN" --version 2>&1); aspect_rc=$?
  else
    aspect_output=$("$ASPECT_BIN" --version 2>&1); aspect_rc=$?
  fi
  printf 'ASPECT_VERSION_QUERY_EXIT=%s\nASPECT_VERSION_OUTPUT_BEGIN\n' "$aspect_rc"
  printf '%s\n' "$aspect_output" | sed -n '1,16p'
  printf 'ASPECT_VERSION_OUTPUT_END\n'
  if command -v ldd >/dev/null 2>&1; then
    printf 'ASPECT_RELEVANT_LINKED_LIBRARIES_BEGIN\n'
    ldd "$ASPECT_BIN" 2>&1 | grep -Ei 'mpi|deal|trilinos|p4est|hdf5|petsc|tpetra|blas|lapack|zlib|not found' | sed -n '1,40p' || true
    printf 'ASPECT_RELEVANT_LINKED_LIBRARIES_END\n'
  fi
else
  printf 'ASPECT_FOUND=no\n'
fi

printf 'ASPECT_DIR=%s\n' "${ASPECT_DIR:-UNSET}"
printf 'DEAL_II_DIR=%s\n' "${DEAL_II_DIR:-UNSET}"
printf 'Trilinos_DIR=%s\n' "${Trilinos_DIR:-UNSET}"
printf 'P4EST_DIR=%s\n' "${P4EST_DIR:-UNSET}"
printf 'CMAKE_PREFIX_PATH=%s\n' "${CMAKE_PREFIX_PATH:-UNSET}"
printf 'ASPECT_SOURCE_DIR=%s\n' "${ASPECT_SOURCE_DIR:-UNSET}"
if [ -n "${ASPECT_SOURCE_DIR:-}" ] && [ -d "$ASPECT_SOURCE_DIR" ]; then
  printf 'ASPECT_SOURCE_DIR_EXISTS=yes\n'
  for item in CMakeLists.txt benchmarks; do
    if [ -e "$ASPECT_SOURCE_DIR/$item" ]; then printf 'ASPECT_SOURCE_HAS_%s=yes\n' "$item"; else printf 'ASPECT_SOURCE_HAS_%s=no\n' "$item"; fi
  done
  if command -v git >/dev/null 2>&1 && git -C "$ASPECT_SOURCE_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf 'ASPECT_SOURCE_GIT_DESCRIBE=%s\n' "$(git -C "$ASPECT_SOURCE_DIR" describe --tags --always --dirty 2>&1)"
    printf 'ASPECT_SOURCE_GIT_STATUS_BEGIN\n'
    git -C "$ASPECT_SOURCE_DIR" status --short 2>&1 | sed -n '1,30p'
    printf 'ASPECT_SOURCE_GIT_STATUS_END\n'
  fi
elif [ -n "${ASPECT_SOURCE_DIR:-}" ]; then
  printf 'ASPECT_SOURCE_DIR_EXISTS=no\n'
fi

section MODULES
if type module >/dev/null 2>&1; then
  printf 'MODULE_COMMAND=available\n'
  printf 'LOADED_RELEVANT_MODULES_BEGIN\n'
  module -t list 2>&1 | grep -Ei 'aspect|deal.?ii|trilinos|p4est|openmpi|mpich' | sed -n '1,40p' || true
  printf 'LOADED_RELEVANT_MODULES_END\n'
  printf 'AVAILABLE_RELEVANT_MODULES_BEGIN\n'
  module -t avail aspect deal.II trilinos p4est 2>&1 | sed -n '1,80p'
  printf 'AVAILABLE_RELEVANT_MODULES_END\n'
else
  printf 'MODULE_COMMAND=not_loaded_or_unavailable\n'
fi

section TOOLCHAIN
probe MPIEXEC mpiexec --version
probe MPIRUN mpirun --version
probe MPICXX mpicxx --version
probe CMAKE cmake --version
probe CXX c++ --version
probe GCC gcc --version
probe GXX g++ --version
probe FC gfortran --version
probe MAKE make --version
probe NINJA ninja --version
probe PKG_CONFIG pkg-config --version
if command -v pkg-config >/dev/null 2>&1; then
  for package in deal.II deal.ii trilinos Trilinos p4est hdf5 blas lapack zlib; do
    printf 'PKG_%s=' "$package"
    pkg-config --modversion "$package" 2>&1 | sed -n '1,3p'
  done
fi
if command -v ldconfig >/dev/null 2>&1; then
  printf 'SYSTEM_RELEVANT_LIBRARIES_BEGIN\n'
  ldconfig -p 2>/dev/null | grep -Ei 'lib(deal_ii|trilinos|p4est|mpi|hdf5|blas|lapack|z|zlib)' | sed -n '1,50p' || true
  printf 'SYSTEM_RELEVANT_LIBRARIES_END\n'
else
  printf 'LDCONFIG=NOT_FOUND\n'
fi

section RESOURCES_CURRENT_SHELL_NOT_FUTURE_JOB
probe NPROC nproc --all
if command -v free >/dev/null 2>&1; then free -b 2>&1; else printf 'FREE=NOT_FOUND\n'; fi
if [ -r /proc/meminfo ]; then grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo; fi
if command -v df >/dev/null 2>&1; then
  df -PB1 "${HOME:-$PWD}" 2>&1 | sed -n '1,4p'
  df -Pi "${HOME:-$PWD}" 2>&1 | sed -n '1,4p'
fi
if command -v quota >/dev/null 2>&1; then quota -s 2>&1 | sed -n '1,30p'; else printf 'USER_QUOTA=quota_command_unavailable\n'; fi
ulimit -a 2>&1 | sed -n '1,40p'
for name in SLURM_JOB_ID SLURM_CPUS_PER_TASK SLURM_MEM_PER_NODE SLURM_MEM_PER_CPU PBS_JOBID PBS_NCPUS LSB_JOBID LSB_DJOB_NUMPROC; do show_env "$name"; done

# Read only this process's known cgroup path and finite ancestor chain; no scans.
if [ -r /proc/self/cgroup ]; then
  printf 'CGROUP_MEMBERSHIP_BEGIN\n'
  cat /proc/self/cgroup
  printf 'CGROUP_MEMBERSHIP_END\n'
  cgroup_v2=$(awk -F: '$1 == "0" && $2 == "" {print $3; exit}' /proc/self/cgroup)
  if [ -n "$cgroup_v2" ] && [ -d /sys/fs/cgroup ]; then
    d="/sys/fs/cgroup${cgroup_v2}"
    printf 'CGROUP_VERSION=2\n'
    depth=0
    while [ "$depth" -lt 12 ] && [ -d "$d" ]; do
      printf 'CGROUP_PATH=%s\n' "$d"
      for f in memory.max memory.high memory.current memory.peak cpu.max pids.max; do
        if [ -r "$d/$f" ]; then printf '%s=' "$f"; cat "$d/$f"; fi
      done
      [ "$d" = /sys/fs/cgroup ] && break
      parent=${d%/*}; [ -n "$parent" ] || break
      d=$parent; depth=$((depth + 1))
    done
  else
    cgroup_mem=$(awk -F: '$2 ~ /(^|,)memory(,|$)/ {print $3; exit}' /proc/self/cgroup)
    printf 'CGROUP_VERSION=not_v2_or_unavailable\n'
    if [ -n "$cgroup_mem" ]; then
      d="/sys/fs/cgroup/memory${cgroup_mem}"
      depth=0
      while [ "$depth" -lt 12 ] && [ -d "$d" ]; do
        printf 'CGROUP_MEMORY_PATH=%s\n' "$d"
        for f in memory.limit_in_bytes memory.soft_limit_in_bytes memory.usage_in_bytes; do
          if [ -r "$d/$f" ]; then printf '%s=' "$f"; cat "$d/$f"; fi
        done
        [ "$d" = /sys/fs/cgroup/memory ] && break
        parent=${d%/*}; [ -n "$parent" ] || break
        d=$parent; depth=$((depth + 1))
      done
    fi
  fi
else
  printf 'CGROUP_MEMBERSHIP=NOT_READABLE\n'
fi

printf '\nPREFLIGHT_END=READ_ONLY_NO_INSTALL_NO_BUILD_NO_ASPECT_RUN\n'
printf 'NOTE=These are observations of this shell/session, not proof of resources assigned to a future scheduler job.\n'
exit 0