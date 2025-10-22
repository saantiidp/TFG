#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

echo "==== FALTANTES REF (ref/results) ===="
missing_ref=0
for hash in sha256 shake256; do
  for level in 128 192 256; do
    for speed in s f; do
      for mode in simple robust; do
        file="ref/results/sphincs-${hash}-${level}${speed}-${mode}.csv"
        if [[ ! -s "$file" ]]; then
          echo "✗ Falta $file"
          missing_ref=1
        fi
      done
    done
  done
done
[[ $missing_ref -eq 0 ]] && echo "✓ Nada"

echo
echo "==== FALTANTES SHA2_AVX2 (sha2_avx2/csv) ===="
missing_sha2=0
for level in 128 192 256; do
  for speed in s f; do
    file="sha2_avx2/csv/sha2-avx-sha2-${level}${speed}.csv"
    if [[ ! -s "$file" ]]; then
      echo "✗ Falta $file"
      missing_sha2=1
    fi
  done
done
[[ $missing_sha2 -eq 0 ]] && echo "✓ Nada"

echo
echo "==== FALTANTES SHAKE_AVX2 (shake_avx2/csv) ===="
missing_shake=0
for level in 128 192 256; do
  for speed in s f; do
    file="shake_avx2/csv/shake-avx-shake-${level}${speed}-simple.csv"
    if [[ ! -s "$file" ]]; then
      echo "✗ Falta $file"
      missing_shake=1
    fi
  done
done
[[ $missing_shake -eq 0 ]] && echo "✓ Nada"
