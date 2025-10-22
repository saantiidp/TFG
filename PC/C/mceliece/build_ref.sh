#!/usr/bin/env bash
set -euo pipefail

variants=(mceliece348864 mceliece348864f \
          mceliece460896 mceliece460896f \
          mceliece6688128 mceliece6688128f \
          mceliece6960119 mceliece6960119f \
          mceliece8192128 mceliece8192128f)

mkdir -p build bin

for param in "${variants[@]}"; do
  d="Reference_Implementation/kem/$param"
  echo "===> $param ref (portable C)"
  if [[ ! -d "$d" ]]; then
    echo "[WARN] No existe $d (me lo salto)"; continue
  fi

  SRCS=$(cd "$d" && find . -type f -name '*.c' ! -name 'kat_kem.c' | LC_ALL=C sort)
  [[ -z "$SRCS" ]] && { echo "[WARN] No hay .c en $d (me lo salto)"; continue; }

  OBJDIR="build/${param}_ref"
  mkdir -p "$OBJDIR"

  # Si existe, lo inyectamos (pone CRYPTO_NAMESPACE a algo seguro)
  EXTRA_NS=""
  [[ -f "$d/namespacing/namespace.h" ]] && EXTRA_NS="-include $d/namespacing/namespace.h"

  # ---------- compilar objetos ----------
  for s in $SRCS; do
    base=${s#./}; base=${base%.c}
    out="$OBJDIR/$base.o"
    mkdir -p "$(dirname "$out")"
    cc -O3 -std=c11 -Wall -Wextra -fomit-frame-pointer \
       -include local_namespace.h $EXTRA_NS \
       -I"$d" -I"$d/subroutines" -I"$d/nist" -I"$d/namespacing" -Iexternal/headers \
       ${EXTRA_CFLAGS:-} \
       -c "$d/$s" -o "$out"
  done

  # ---------- compilar bench ----------
  [[ ! -f "$d/api.h" ]] && { echo "[WARN] Falta $d/api.h (me lo salto)"; continue; }
  [[ ! -f "$d/crypto_kem.h" ]] && { echo "[WARN] Falta $d/crypto_kem.h (me lo salto)"; continue; }

  BENCHO="$OBJDIR/bench_mceliece.o"
  cc -O3 -std=c11 -Wall -Wextra -fomit-frame-pointer \
     -include local_namespace.h $EXTRA_NS \
     -I"$d" -I"$d/nist" -I"$d/namespacing" -Iexternal/headers \
     -include "$d/api.h" -include "$d/crypto_kem.h" \
     -c bench_mceliece.c -o "$BENCHO"

  # ---------- enlazar ----------
  objs=$(find "$OBJDIR" -type f -name '*.o' | LC_ALL=C sort)
  ldextra=""
  [[ -f "external/XKCP/bin/generic64/libXKCP.a" ]] && ldextra="external/XKCP/bin/generic64/libXKCP.a"

  outexe="build/bench_${param}_ref"
  cc $objs $ldextra -lcrypto -o "$outexe"
  ln -sf "../$outexe" "bin/${param}.ref"
done

echo "OK: Reference compilada. Ejecutables en build/bench_*_ref y enlaces en bin/*.ref"
