// Dimensionless arithmetic microbenchmark, NOT an ASPECT or mantle model.
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
int main() {
  const std::size_t count=1u<<20;
  const int rounds=8,iterations=32;
  double *values=nullptr,*forcing=nullptr;
  if (posix_memalign((void**)&values,64,count*sizeof(double)) ||
      posix_memalign((void**)&forcing,64,count*sizeof(double))) return 2;
  for(std::size_t i=0;i<count;++i) {values[i]=1.+double(i%1024)/1024.;forcing[i]=.5+double(i%8192)/8192.;}
  auto start=std::chrono::steady_clock::now();
  for(int r=0;r<rounds;++r) {
#ifdef ENABLE_SIMD
#pragma omp simd aligned(values,forcing:64)
#endif
    for(std::size_t i=0;i<count;++i) {
      double y=values[i],x=forcing[i];
      for(int k=0;k<iterations;++k) y=((.125*y-.25)*y+.5)*y+.125*x;
      values[i]=y;
    }
  }
  double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  std::uint64_t checksum=1469598103934665603ULL;
  for(std::size_t i=0;i<count;++i) {
    if (!std::isfinite(values[i])) return 3;
    std::uint64_t bits;std::memcpy(&bits,&values[i],8);checksum=(checksum^bits)*1099511628211ULL;
  }
  std::printf("{\"elements\":%zu,\"rounds\":%d,\"iterations\":%d,\"compute_s\":%.9f,\"checksum\":\"%016llx\"}\n",count,rounds,iterations,elapsed,(unsigned long long)checksum);
  std::free(values);std::free(forcing);return 0;
}
