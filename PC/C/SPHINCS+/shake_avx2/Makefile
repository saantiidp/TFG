# ==============================
# SPHINCS+ SHAKE AVX2 - Makefile CSV
# ==============================

CC      := cc
CFLAGS  := -O3 -Wall -Wextra -Wpedantic -std=c99 -mavx2 -mbmi2
LDFLAGS := -lssl -lcrypto -lm -ldl

BUILD_DIR := build
CSV_DIR   := csv

# Variantes "simple" (optimizadas AVX2 en este repo)
VARIANTS := \
  sphincs-shake256-128s-simple \
  sphincs-shake256-128f-simple \
  sphincs-shake256-192s-simple \
  sphincs-shake256-192f-simple \
  sphincs-shake256-256s-simple \
  sphincs-shake256-256f-simple

.PHONY: all clean runs csv-shake-avx csv-all

all: runs

clean:
	@echo "[CLEAN] $(BUILD_DIR)/ eliminado"
	@rm -rf $(BUILD_DIR) $(CSV_DIR)

# -----------------------------------------------------------------------------
# Compilar SIEMPRE el benchmark CSV de nivel superior:
# (ojo: NO usamos crypto_sign/%/test/benchmark.c)
# -----------------------------------------------------------------------------
$(BUILD_DIR)/%/benchmark.o: test/benchmark.c
	@mkdir -p $(dir $@)
	@echo "cc $< -> $@"
	@$(CC) $(CFLAGS) -Icrypto_sign/$* -c $< -o $@

# -----------------------------------------------------------------------------
# Enlazado de ejecutable para cada variante (sin PQCgenKAT_sign.c)
# -----------------------------------------------------------------------------
define LINK_SHAKE
$(CC) $< \
  crypto_sign/$*/fips202.c \
  crypto_sign/$*/hash_shake256.c \
  crypto_sign/$*/wots.c \
  crypto_sign/$*/rng.c \
  crypto_sign/$*/sign.c \
  crypto_sign/$*/address.c \
  crypto_sign/$*/fors.c \
  crypto_sign/$*/utils.c \
  crypto_sign/$*/thash_shake256_simple.c \
  -o $@ $(LDFLAGS)
endef

$(BUILD_DIR)/%/run: $(BUILD_DIR)/%/benchmark.o
	@echo "[INFO] linking $@"
	@$(LINK_SHAKE)
	@[ -x $@ ] || { echo "[ERROR] no se generó ejecutable: $@"; exit 1; }

# -----------------------------------------------------------------------------
# Ejecutar y volcar CSV con el patrón pedido: shake-avx-shake-XXX.csv
# -----------------------------------------------------------------------------
$(CSV_DIR)/shake-avx-shake-%.csv: $(BUILD_DIR)/sphincs-shake256-%/run
	@mkdir -p $(CSV_DIR)
	@echo "==== [sphincs-shake256-$* -> CSV] ===="
	@./$< > $@ || { echo "[ERROR] No se generó CSV para $*"; rm -f $@; exit 1; }

# -----------------------------------------------------------------------------
# Targets globales
# -----------------------------------------------------------------------------
runs: $(patsubst %, $(BUILD_DIR)/%/run, $(VARIANTS))

csv-shake-avx: $(patsubst sphincs-shake256-%, $(CSV_DIR)/shake-avx-shake-%.csv, $(VARIANTS))

# Alias cómodo
csv-all: csv-shake-avx
