# ================================
# SPHINCS+ SHA2 AVX2 - Makefile
# ================================

CC = gcc
CFLAGS = -O3 -Wall -Wextra -std=c99 -mavx2 -Icrypto_sign/sphincs-sha256-128s-simple
LDFLAGS = -lm -lcrypto -lssl
BUILD_DIR = build/sphincs-sha256-128s-simple
SCHEME = sphincs-sha256-128s-simple

# Objetivos principales
all: PQCgenKAT_sign benchmark

# --------------------------------
# Compilación del programa principal KAT
# --------------------------------
PQCgenKAT_sign: crypto_sign/$(SCHEME)/PQCgenKAT_sign.c \
                crypto_sign/$(SCHEME)/address.c \
                crypto_sign/$(SCHEME)/sign.c \
                crypto_sign/$(SCHEME)/hash_sha256.c \
                crypto_sign/$(SCHEME)/sha256.c \
                crypto_sign/$(SCHEME)/rng.c \
                crypto_sign/$(SCHEME)/utils.c \
                crypto_sign/$(SCHEME)/fors.c \
                crypto_sign/$(SCHEME)/wots.c \
                crypto_sign/$(SCHEME)/thash_sha256_simple.c
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

# --------------------------------
# Benchmark
# --------------------------------
benchmark: test/benchmark.c rng_moderno.c
	mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icrypto_sign/$(SCHEME) test/benchmark.c rng_moderno.c \
		$(LDFLAGS) -o $(BUILD_DIR)/benchmark

# --------------------------------
# Limpieza
# --------------------------------
clean:
	rm -f PQCgenKAT_sign
	rm -rf $(BUILD_DIR)

# --------------------------------
# Utilidades
# --------------------------------
print-%:
	@echo '$*=$($*)'

.PHONY: all clean benchmark

