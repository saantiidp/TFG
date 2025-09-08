#!/usr/bin/env bash
set -euo pipefail

PARAMS=( mceliece348864 mceliece348864f mceliece460896 mceliece460896f \
         mceliece6688128 mceliece6688128f mceliece6960119 mceliece6960119f \
         mceliece8192128 mceliece8192128f )

ITERS=${1:-200}

for P in "${PARAMS[@]}"; do
  for I in ref opt; do
    make clean
    make PARAM="$P" IMPL="$I"
    ./build/bench_${P}_${I} "$ITERS" "$I" "$P" > "${P}_${I}_c.csv"
    echo "OK -> ${P}_${I}_c.csv"
  done
done
