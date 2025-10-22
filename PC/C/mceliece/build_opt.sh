#!/bin/bash
set -e
VARIANTS="348864f 348864 460896f 460896 6688128f 6688128 6960119f 6960119 8192128f 8192128"
mkdir -p build
for v in $VARIANTS; do
  d="Optimized_Implementation/kem/mceliece${v}"
  out="build/bench_${v}_avx"
  if [ ! -d "$d" ]; then
    echo "[SKIP] No existe $d"
    continue
  fi
  echo "===> ${d} -> ${out}"
  SRCS=$(cd "$d" && find . -type f -name '*.c' ! -name 'kat_kem.c' | LC_ALL=C sort)
  [ -n "$SRCS" ] || { echo "[SKIP] No hay .c en $d"; continue; }

  OBJDIR="build/obj_mceliece${v}_avx"
  rm -rf "$OBJDIR"
  mkdir -p "$OBJDIR"

  INCS="-I$d -I$d/subroutines -I$d/nist -Iexternal/headers"
  [ -d "$d/namespacing" ] && INCS="$INCS -I$d/namespacing"
  CFLAGS="-O3 -march=native -Wall -Wextra"

  EXTRA_INC=""
  if [ -f "$d/namespacing/namespace.h" ]; then
    EXTRA_INC="-include $d/namespacing/namespace.h"
  fi

  # objetos del KEM (ahora SI con -include namespace.h)
  for s in $SRCS; do
    base=${s#./}; base=${base%.c}
    mkdir -p "$OBJDIR/$(dirname "$base")"
    cc $CFLAGS $INCS $EXTRA_INC -c "$d/$s" -o "$OBJDIR/$base.o"
  done

  # objeto del bench (también con -include namespace.h)
  [ -f "$d/api.h" ] || { echo "[ERR] Falta $d/api.h"; exit 1; }
  [ -f "$d/crypto_kem.h" ] || { echo "[ERR] Falta $d/crypto_kem.h"; exit 1; }
  cc $CFLAGS $INCS $EXTRA_INC -include "$d/api.h" -include "$d/crypto_kem.h" \
     -c bench_mceliece.c -o "$OBJDIR/bench_mceliece.o"

  # enlazado
  objs=$(find "$OBJDIR" -type f -name '*.o' | LC_ALL=C sort)
  ldextra=""
  [ -f "external/XKCP/bin/generic64/libXKCP.a" ] && ldextra="external/XKCP/bin/generic64/libXKCP.a"
  cc $objs $ldextra -lcrypto -o "$out"
  echo "[OK] $out"
done
