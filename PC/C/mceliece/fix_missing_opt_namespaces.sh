#!/bin/bash
set -e
base="Optimized_Implementation/kem"
count=0
for d in "$base"/mceliece*; do
  [ -d "$d" ] || continue
  nsdir="$d/namespacing"
  mkdir -p "$nsdir"
  short="${d##*/}"           # mceliece8192128f
  short="${short#mceliece}"  # 8192128f
  upper=$(printf "%s" "$short" | tr '[:lower:]' '[:upper:]')
  prefix="PQCLEAN_MCELIECE${upper}_AVX_"
  cat > "$nsdir/namespace.h" <<EOF
#ifndef NAMESPACE_H
#define NAMESPACE_H
#define CRYPTO_NAMESPACE(s) ${prefix}##s
#endif
EOF
  echo "[WRITE] $nsdir/namespace.h -> ${prefix}"
  count=$((count+1))
done
echo "[INFO] namespace.h escritos/actualizados: $count"
