###############################################################################
# BIKE Reference Implementation (v5.2) – Makefile adaptado para Raspberry Pi 5
# Autor: Santiago de Prada
# Características:
#   • Compatible con ARMv8.2-A (NEON + FPU) y x86_64 (AVX2)
#   • Separa compilador C y C++ (gcc / g++)
#   • Corrige duplicación de main (PQCgenKAT_kem.c)
#   • Añade target "benchmark" con medición de recursos (/usr/bin/time -v)
###############################################################################

VERBOSE = 0

# Compiladores
CC  := gcc
CXX := g++

# Detección automática de arquitectura
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_M),x86_64)
    CFLAGS := -O3 -m64 -march=x86-64 -mtune=native
    OPT_MSG := "Compilando para x86_64 (AVX2 posible)"
else ifneq (,$(findstring armv8,$(UNAME_M)))
    CFLAGS := -O3 -march=armv8.2-a+simd -mtune=cortex-a76 -mfpu=neon-fp-armv8
    OPT_MSG := "Compilando para ARMv8.2-A (NEON + FPU)"
else
    CFLAGS := -O3
    OPT_MSG := "Compilando con configuración genérica (-O3)"
endif

# Librerías
INCLUDE := -I. -I/usr/include -L/usr/lib \
           -lcrypto -lssl -lm -ldl -lntl -lgmp -lgf2x -lpthread

# Fuentes
SRC_C   := $(wildcard *.c FromNIST/*.c)
SRC_CPP := ntl.cpp

$(info ================================================)
$(info $(OPT_MSG))
$(info CFLAGS = $(CFLAGS))
$(info ================================================)

###############################################################################
# Targets principales
###############################################################################

all: bike-nist-kat

# --------------------------------------------------------------------------
# Compila los tests NIST KAT (oficiales)
# --------------------------------------------------------------------------
bike-nist-kat: $(SRC_C) $(SRC_CPP)
	$(CXX) $(CFLAGS) $(filter-out FromNIST/PQCgenKAT_kem.c,$(SRC_C)) \
	FromNIST/PQCgenKAT_kem.c $(SRC_CPP) $(INCLUDE) \
	-DVERBOSE=$(VERBOSE) -DNIST_RAND=1 -o $@
	@echo "\nCompilación completada: bike-nist-kat"

# --------------------------------------------------------------------------
# Compila pruebas de demostración (opcional)
# --------------------------------------------------------------------------
bike-demo-test: $(SRC_C) $(SRC_CPP)
	$(CXX) $(CFLAGS) tests/test.c $(SRC_C) $(SRC_CPP) $(INCLUDE) \
	-DVERBOSE=$(VERBOSE) -DNIST_RAND=1 -o $@
	@echo "\nCompilación completada: bike-demo-test"

###############################################################################
# Benchmark automático (1000 iteraciones + medición de recursos)
###############################################################################
benchmark:
	@echo "🚀 Ejecutando benchmark de BIKE..."
	@mkdir -p results
	@for version in 128 192 256; do \
	    echo "\n🔹 BIKE-$$version (1000 iteraciones)" | tee -a results/benchmark_bike.log; \
	    /usr/bin/time -v ./bike-nist-kat $$version 1000 2>&1 | tee -a results/benchmark_bike.log; \
	done
	@echo "\nBenchmark completado. Resultados en results/benchmark_bike.log"

###############################################################################
# Limpieza
###############################################################################
clean:
	rm -f PQCkemKAT_* bike-nist-kat bike-demo-test
	@echo "Archivos de compilación eliminados correctamente."

###############################################################################
# Información de uso
###############################################################################
# ▶ make bike-nist-kat
#     Compila la referencia oficial de BIKE (NIST KAT)
#
# ▶ make benchmark
#     Ejecuta 1000 iteraciones de cada versión (128/192/256) y mide tiempo,
#     CPU y memoria usando /usr/bin/time -v. Resultados en results/benchmark_bike.log
#
# ▶ make clean
#     Elimina binarios y temporales
#
# Dependencias requeridas (instalar una sola vez):
#   sudo apt install libntl-dev libgmp-dev libgf2x-dev libssl-dev
#
# Nota: Añadir '#include <stdbool.h>' en sampling.h, sampling.c y kem.c si
#       aparece error de tipo 'bool' al compilar.
###############################################################################

