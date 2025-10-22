# =========================================================
# Makefile - SHA2 AVX2 (optimized) - SPHINCS+ benchmark -> CSV
# =========================================================

# --- Toolchain ---
CC      ?= cc
CFLAGS  ?= -O3 -Wall -Wextra -Wpedantic -std=c99 -D_POSIX_C_SOURCE=200809L
CFLAGS  += -mavx2 -mbmi2
LDFLAGS ?=
LDLIBS  ?= -lssl -lcrypto -lm -ldl

# --- Layout ---
ROOT_BENCH := test/benchmark.c
CSV_DIR    := csv

# --- Paramsets SHA2 (simple) ---
SHA2_PARAMS := \
  sphincs-sha256-128s-simple \
  sphincs-sha256-128f-simple \
  sphincs-sha256-192s-simple \
  sphincs-sha256-192f-simple \
  sphincs-sha256-256s-simple \
  sphincs-sha256-256f-simple

# --- Helpers de nombres para CSV ---
define NAME_FOR
$(patsubst sphincs-sha256-%,sha2-avx-sha2-%,$(patsubst %-simple,%,$(1)))
endef

# ---------------------------------------------------------
# Targets de alto nivel
# ---------------------------------------------------------
.PHONY: all runs csv-sha2-avx clean help
all: runs

runs: $(addsuffix /run,$(addprefix build/,$(SHA2_PARAMS)))

csv-sha2-avx: $(CSV_DIR) $(SHA2_PARAMS)
	@echo "[OK] CSVs generados en '$(CSV_DIR)'"

clean:
	@rm -rf build $(CSV_DIR)

help:
	@echo "Targets:"
	@echo "  runs            - compila todos los binarios (SHA2 AVX2)"
	@echo "  csv-sha2-avx    - ejecuta y guarda CSVs como sha2-avx-sha2-*.csv"
	@echo "  clean           - borra build/ y csv/"
	@echo "Sugerencia: usa -j"

$(CSV_DIR):
	@mkdir -p $(CSV_DIR)

# ---------------------------------------------------------
# CSV por paramset (seguro con -j)
# ---------------------------------------------------------
.PHONY: $(SHA2_PARAMS)
$(SHA2_PARAMS): %: | $(CSV_DIR) build/%/run
	@echo "==== [$@ -> CSV] ===="
	@sh -c 'set -e; \
	  cd build/$@; \
	  rm -f *.csv; \
	  ./run >/dev/null; \
	  f=$$(ls *.csv 2>/dev/null | head -n1); \
	  [ -n "$$f" ] || { echo "[ERROR] No se encontró CSV tras ejecutar $@"; exit 1; }; \
	  mv "$$f" "../../$(CSV_DIR)/$(call NAME_FOR,$@).csv"'
	@echo "[OK] -> $(CSV_DIR)/$(call NAME_FOR,$@).csv"

# ---------------------------------------------------------
# Compilación y link por paramset
# ---------------------------------------------------------

build/%/benchmark.o: $(ROOT_BENCH)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -Icrypto_sign/$* -c $< -o $@

# Enlaza con fuentes del paramset (sin PQCgenKAT_sign.c)
build/%/run: build/%/benchmark.o
	@rm -f $@
	@sh -c 'set -e; \
	  d="crypto_sign/$*"; \
	  case "$*" in \
	    *robust*) THASH=thash_sha256_robust.c ;; \
	    *)        THASH=thash_sha256_simple.c ;; \
	  esac; \
	  SRCS="hash_sha256.c wots.c rng.c sign.c $$THASH address.c sha256.c fors.c utils.c"; \
	  $(CC) $(CFLAGS) "$<" $$(printf "%s " $$(for s in $$SRCS; do printf "%s/%s " "$$d" "$$s"; done)) \
	    $(LDFLAGS) -o "$@" $(LDLIBS)'
	@echo "[INFO] linked $@"

# ---------------------------------------------------------
# Atajo: compilar un solo paramset
#   make one VAR=sphincs-sha256-192s-simple
# ---------------------------------------------------------
.PHONY: one
one:
	@[ -n "$(VAR)" ] || { echo "Uso: make one VAR=<paramset>"; exit 2; }
	@$(MAKE) -s build/$(VAR)/run
	@echo "[OK] build/$(VAR)/run listo"
