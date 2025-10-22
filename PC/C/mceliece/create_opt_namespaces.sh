#!/bin/bash
set -e
base="Optimized_Implementation/kem"
count=0
for d in "$base"/mceliece*; do
  [ -d "$d" ] || continue
  nsdir="$d/namespacing"
  hdr="$nsdir/namespace.h"
  if [ -f "$hdr" ]; then
    echo "[SKIP] Ya existe $hdr"
    continue
  fi
  mkdir -p "$nsdir"
  short="${d##*/}"           # p.ej. mceliece8192128f
  short="${short#mceliece}"  # p.ej. 8192128f
  upper=$(printf "%s" "$short" | tr '[:lower:]' '[:upper:]')
  prefix="PQCLEAN_MCELIECE${upper}_AVX_"
  cat > "$hdr" <<EOF
#ifndef NAMESPACE_H
#define NAMESPACE_H
#define CRYPTO_NAMESPACE(s) ${prefix}##s
#endif
EOF
  echo "[OK] $hdr -> ${prefix}"
  count=$((count+1))
done
echo "[INFO] namespace.h creados: $count"
