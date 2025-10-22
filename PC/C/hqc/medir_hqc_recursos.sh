#!/bin/bash
set -euo pipefail

OUTCSV="hqc_resources.csv"
echo "Algorithm,SecurityLevel,Variant,Wall_s,CPU_pct,MaxRSS_kB" > "$OUTCSV"

measure() {
  local algo=$1
  local sec=$2
  local variant=$3
  local bin=$4

  if [[ ! -x "$bin" ]]; then
    echo "WARN: no existe ejecutable $bin"
    echo "$algo,$sec,$variant,NA,NA,NA" >> "$OUTCSV"
    return
  fi

  echo "Midiendo $algo-$sec $variant con $bin ..."
  local metrics
  metrics=$( /usr/bin/time -f "%e;%P;%M" "$bin" 2>&1 >/dev/null || true )

  if [[ -z "$metrics" ]]; then
    echo "WARN: sin métricas para $algo-$sec $variant."
    echo "$algo,$sec,$variant,NA,NA,NA" >> "$OUTCSV"
    return
  fi

  local wall=$(echo "$metrics" | cut -d';' -f1)
  local cpu=$(echo "$metrics" | cut -d';' -f2 | tr -d '%')
  local rss=$(echo "$metrics" | cut -d';' -f3)

  echo "OK  $algo-$sec $variant: wall=${wall}s cpu=${cpu}% rss=${rss}kB"
  echo "$algo,$sec,$variant,$wall,$cpu,$rss" >> "$OUTCSV"
}

# Reference
measure HQC 128 ref "./Reference_Implementation/hqc-128/bin/test_hqc"
measure HQC 192 ref "./Reference_Implementation/hqc-192/bin/test_hqc"
measure HQC 256 ref "./Reference_Implementation/hqc-256/bin/test_hqc"

# Optimized
measure HQC 128 avx2 "./Optimized_Implementation/hqc-128/bin/test_hqc"
measure HQC 192 avx2 "./Optimized_Implementation/hqc-192/bin/test_hqc"
measure HQC 256 avx2 "./Optimized_Implementation/hqc-256/bin/test_hqc_256"

echo
echo "→ Resultados guardados en $OUTCSV"
