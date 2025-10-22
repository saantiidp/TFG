#!/bin/bash
set -e

build_one() {
  local base="$1"   # Optimized_Implementation/kem o Reference_Implementation/kem
  local impl="$2"   # avx o ref
  local d="$3"      # p.ej. mceliece8192128f
  local full="${base}/${d}"
  [ -d "$full" ] || { echo "[SKIP] No existe ${full}"; return; }

  local short="${d#mceliece}"
  echo "===> ${d} -> build/bench_${short}_${impl}"

  # Fuentes (excluye kat_kem.c)
  SRCS=$(cd "$full" && find . -type f -name '*.c' ! -name 'kat_kem.c' | LC_ALL=C sort)
  [ -n "$SRCS" ] || { echo "[SKIP] No hay .c en ${full}"; return; }

  OBJDIR="build/${d}_${impl}"
  mkdir -p "$OBJDIR"

  INCS="-I${full} -I${full}/subroutines -I${full}/nist -Iexternal/headers"
  CFLAGS="-O3 -Wall -Wextra"

  if [ "$impl" = "avx" ]; then
    CFLAGS="${CFLAGS} -march=native"
    # AVX/opt NECESITA su namespace.h; si no está, saltamos
    if [ -f "${full}/namespacing/namespace.h" ]; then
      INCS="${INCS} -I${full}/namespacing"
      NSINC="-include ${full}/namespacing/namespace.h"
    else
      echo "[SKIP] Falta ${full}/namespacing/namespace.h (opt requiere namespacing); saltando ${d}"
      return
    fi
  else
    # ref: si no hay namespacing, activamos fallback identidad (sin comillas)
    if [ -f "${full}/namespacing/namespace.h" ]; then
      INCS="${INCS} -I${full}/namespacing"
      NSINC="-include ${full}/namespacing/namespace.h"
    else
      CFLAGS="${CFLAGS} -DCRYPTO_NAMESPACE(x)=x"
      NSINC=""
    fi
  fi

  # Compila objetos del KEM
  for s in $SRCS; do
    basec=${s#./}; basec=${basec%.c}
    out="$OBJDIR/$basec.o"
    mkdir -p "$(dirname "$out")"
    cc $CFLAGS $INCS -c "$full/$s" -o "$out"
  done

  # bench.o con api.h y crypto_kem.h
  [ -f "$full/api.h" ] || { echo "[ERR] Falta ${full}/api.h"; return 1; }
  [ -f "$full/crypto_kem.h" ] || { echo "[ERR] Falta ${full}/crypto_kem.h"; return 1; }
  BENCHO="$OBJDIR/bench_mceliece.o"
  cc $CFLAGS $INCS ${NSINC} \
     -include "$full/api.h" -include "$full/crypto_kem.h" \
     -c bench_mceliece.c -o "$BENCHO"

  # Enlace
  objs=$(find "$OBJDIR" -type f -name '*.o' | LC_ALL=C sort)
  ldextra=""
  [ -f "external/XKCP/bin/generic64/libXKCP.a" ] && ldextra="external/XKCP/bin/generic64/libXKCP.a"
  cc $objs $ldextra -lcrypto -o "build/bench_${short}_${impl}"

  echo "[OK] build/bench_${short}_${impl}"
}

# Build opt (solo variantes que tengan namespacing/namespace.h)
for d in $(ls -1 Optimized_Implementation/kem | grep '^mceliece'); do
  build_one "Optimized_Implementation/kem" "avx" "$d"
done

# Build ref (si tienen namespacing lo usamos; si no, fallback identidad)
for d in $(ls -1 Reference_Implementation/kem | grep '^mceliece'); do
  build_one "Reference_Implementation/kem" "ref" "$d"
done
