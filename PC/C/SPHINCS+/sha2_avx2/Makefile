# ========= Toolchain =========
CC      = cc
CFLAGS  = -O3 -Wall -Wextra -Wpedantic -std=c99 -mavx2 -mbmi2
LDFLAGS = -lssl -lcrypto -lm -ldl

BUILD      = build
CRYPTO_DIR = crypto_sign
CSV_DIR    = csv

# ========= Variantes SHA2 (AVX2) =========
VARIANTS = \
  sphincs-sha256-128s-simple \
  sphincs-sha256-128f-simple \
  sphincs-sha256-192s-simple \
  sphincs-sha256-192f-simple \
  sphincs-sha256-256s-simple \
  sphincs-sha256-256f-simple

# Mapeo variante -> nombre de CSV (como pediste)
CSV_NAME_sphincs-sha256-128s-simple = sha2-avx-sha2-128s
CSV_NAME_sphincs-sha256-128f-simple = sha2-avx-sha2-128f
CSV_NAME_sphincs-sha256-192s-simple = sha2-avx-sha2-192s
CSV_NAME_sphincs-sha256-192f-simple = sha2-avx-sha2-192f
CSV_NAME_sphincs-sha256-256s-simple = sha2-avx-sha2-256s
CSV_NAME_sphincs-sha256-256f-simple = sha2-avx-sha2-256f

# ========= Benchmark propio (CSV) =========
BENCH_SRC = test/bench_csv.c

.PHONY: all runs clean csv-sha2-avx

all: runs

runs: $(VARIANTS:%=$(BUILD)/%/run)

# Genera todos los CSV
csv-sha2-avx: $(foreach v,$(VARIANTS),$(CSV_DIR)/$(CSV_NAME_$(v)).csv)

# ===== Regla plantilla por variante =====
define BUILD_ONE
# Compilar nuestro bench CSV con los headers de la variante
$(BUILD)/$(1)/benchmark.o: $(BENCH_SRC)
	@mkdir -p $$(dir $$@)
	@echo "cc $$< -> $$@"
	$$(CC) $$(CFLAGS) -I$(CRYPTO_DIR)/$(1) -c $$< -o $$@

# Enlazar: todas las .c de la variante, EXCEPTO test/*.c y PQCgenKAT_sign.c (traen main)
$(BUILD)/$(1)/run: $(BUILD)/$(1)/benchmark.o
	@echo "[INFO] linking $$@"
	$$(CC) $$< \
		$$(filter-out %/test/%.c $(CRYPTO_DIR)/$(1)/PQCgenKAT_sign.c, \
			$$(wildcard $(CRYPTO_DIR)/$(1)/*.c)) \
		-o $$@ $$(LDFLAGS)

# Ejecutar y volcar CSV con el nombre exacto pedido
$(CSV_DIR)/$(CSV_NAME_$(1)).csv: $(BUILD)/$(1)/run
	@mkdir -p $(CSV_DIR)
	@echo "==== [$(1) -> CSV] ===="
	@./$$< > $$@ || (echo "[ERROR] Falló la ejecución de $(1)" && exit 1)
endef
$(foreach v,$(VARIANTS),$(eval $(call BUILD_ONE,$(v))))

clean:
	@echo "[CLEAN] $(BUILD)/ eliminado"
	@rm -rf $(BUILD) $(CSV_DIR)
