# =========================
#  Makefile AVX2-only KEMs
# =========================

SHELL := /bin/sh
.ONESHELL:

CC      ?= cc
CFLAGS_BASE := -O3 -std=c11 -Wall -Wextra -fomit-frame-pointer -include local_namespace.h
CFLAGS_AVX  := -mavx2 -mbmi2 -mpopcnt -maes
CFLAGS      := $(CFLAGS_BASE) $(CFLAGS_AVX)

# Biblioteca XKCP (si existe la enlazamos; si no, seguimos sin ella)
XKCP    ?= external/XKCP/bin/generic64/libXKCP.a

# Iteraciones del bench (make N=500 all-avx)
N ?= 200

PARAMS := \
  mceliece348864 mceliece348864f \
  mceliece460896 mceliece460896f \
  mceliece6688128 mceliece6688128f \
  mceliece6960119 mceliece6960119f \
  mceliece8192128 mceliece8192128f

.PHONY: all-avx build-avx run-avx clean \
        $(addprefix build-,$(PARAMS)) \
        $(addprefix run-,$(PARAMS))

# Compila y ejecuta todos (genera CSV)
all-avx: $(addprefix run-,$(PARAMS))

# Sólo construir
build-avx: $(addprefix build-,$(PARAMS))

# Sólo ejecutar (requiere binarios ya construidos)
run-avx: $(addprefix run-,$(PARAMS))

# -----------------------------
#  Reglas por parámetro (build)
# -----------------------------
$(addprefix build-,$(PARAMS)): build-%: build/bench_%_avx
	@true

# Compila todo y enlaza: build/bench_<param>_avx
build/bench_%_avx: bench_mceliece.c
	set -e
	param="$*"
	d="Optimized_Implementation/kem/$$param"
	if [ ! -d "$$d" ]; then
	  echo "[ERROR] No existe $$d"; exit 2
	fi
	echo "===> $$param opt (AVX2)"
	echo "[OK] Usando fuentes: $$d"

	# Descubrir .c (omitimos nist/kat_kem.c)
	SRCS=$$(cd "$$d" && find . -type f -name '*.c' ! -name 'kat_kem.c' | LC_ALL=C sort)
	if [ -z "$$SRCS" ]; then
	  echo "[ERROR] No hay .c en $$d"; exit 3
	fi

	# Preparar objdir y compilar todos los .c del KEM
	OBJDIR="build/$$param"
	mkdir -p "$$OBJDIR"
	for s in $$SRCS; do
	  base=$${s#./}; base=$${base%.c}
	  out="$$OBJDIR/$$base.o"
	  mkdir -p "$$(dirname "$$out")"
	  $(CC) $(CFLAGS) \
	    -I"$$d" -I"$$d/subroutines" -I"$$d/nist" -I"$$d/namespacing" -Iexternal/headers \
	    -c "$$d/$$s" -o "$$out"
	done

	# Compilar bench con api.h + crypto_kem.h + (opcional) namespacing/namespace.h
	if [ ! -f "$$d/api.h" ]; then echo "[ERROR] Falta $$d/api.h"; exit 4; fi
	if [ ! -f "$$d/crypto_kem.h" ]; then echo "[ERROR] Falta $$d/crypto_kem.h"; exit 4; fi
	BENCHO="$$OBJDIR/bench_mceliece.o"
	EXTRA=""
	if [ -f "$$d/namespacing/namespace.h" ]; then EXTRA="$$EXTRA -include $$d/namespacing/namespace.h"; fi
	$(CC) $(CFLAGS) \
	  -I"$$d" -I"$$d/nist" -I"$$d/namespacing" -Iexternal/headers \
	  -include "$$d/api.h" -include "$$d/crypto_kem.h" $$EXTRA \
	  -c bench_mceliece.c -o "$$BENCHO"

	# Enlazar (añadimos XKCP si existe)
	objs=$$(find "$$OBJDIR" -type f -name '*.o' | LC_ALL=C sort)
	ldextra=""
	[ -f "$(XKCP)" ] && ldextra="$(XKCP)"
	$(CC) $$objs $$ldextra -lcrypto -o "build/bench_$${param}_avx"

# -----------------------------
#  Reglas por parámetro (run)
# -----------------------------
$(addprefix run-,$(PARAMS)): run-%: build/bench_%_avx
	set -e
	param="$*"
	echo "[RUN] build/bench_$${param}_avx $(N) opt $$param > $${param}_opt_c.csv"
	./build/bench_$${param}_avx "$(N)" opt "$$param" > "$${param}_opt_c.csv"

# -----------------------------
#  Limpieza
# -----------------------------
clean:
	@echo "Limpiando build y CSV..."
	@rm -rf build
	@rm -f *_opt_c.csv
