# ========= Configuración de McEliece =========
PARAM            ?= mceliece348864
IMPL             ?= ref   # ref | opt

# Raíces de las dos variantes
REF_ROOT         := Reference_Implementation/kem
OPT_ROOT         := Optimized_Implementation/kem

# Normaliza IMPL
IMPL_NORM := $(IMPL)
ifeq ($(IMPL),optimized)
  IMPL_NORM := opt
endif

# Selecciona carpeta raíz e include según IMPL
ifeq ($(IMPL_NORM),ref)
  ROOT_DIR  := $(REF_ROOT)
  XKCP_TARGET := generic64
  EXTRA_SIMD :=
else ifeq ($(IMPL_NORM),opt)
  ROOT_DIR  := $(OPT_ROOT)
  XKCP_TARGET := AVX2
  EXTRA_SIMD := -mavx2 -mbmi2 -mpopcnt
else
  $(error IMPL debe ser 'ref' u 'opt')
endif

PARAM_DIR := $(ROOT_DIR)/$(PARAM)

# ========= Keccak (XKCP) =========
# Librería y cabeceras ya preparadas en external/XKCP por los pasos previos
XKCP_DIR      := external/XKCP
XKCP_LIBDIR   := $(XKCP_DIR)/bin/$(XKCP_TARGET)
XKCP_LIB      := $(XKCP_LIBDIR)/libXKCP.a
# Enlace simbólico a headers con el nombre que espera el código de McEliece:
KECCAK_HEADERS := external/headers/libkeccak.a.headers

# ========= Flags =========
CC      := cc
CFLAGS  := -O3 -std=c11 -Wall -Wextra -fomit-frame-pointer -include local_namespace.h $(EXTRA_SIMD)
CPPFLAGS:= -I$(PARAM_DIR) \
           -I$(PARAM_DIR)/subroutines \
           -I$(PARAM_DIR)/nist \
           -I$(PARAM_DIR)/namespacing \
           -I$(KECCAK_HEADERS)

LDFLAGS := -L$(XKCP_LIBDIR)
LDLIBS  := -lXKCP

# ========= Fuentes =========
MCELIECE_SRCS := \
  benes.c bm.c controlbits.c encrypt.c decrypt.c gf.c operations.c \
  pk_gen.c root.c sk_gen.c synd.c transpose.c util.c

SRCS := $(addprefix $(PARAM_DIR)/,$(MCELIECE_SRCS)) bench_mceliece.c
OBJS := $(addprefix build/impl_,$(notdir $(MCELIECE_SRCS:.c=.o))) build/bench_mceliece.o

BIN  := build/bench_$(PARAM)_$(IMPL_NORM)

# ========= Reglas =========
.PHONY: all info clean ref opt

all: $(BIN)

info:
	@echo "PARAM      = $(PARAM)"
	@echo "IMPL       = $(IMPL)  (normalizado: $(IMPL_NORM))"
	@echo "ROOT_DIR   = $(ROOT_DIR)"
	@echo "PARAM_DIR  = $(PARAM_DIR)"
	@echo "XKCP_LIB   = $(XKCP_LIB)"
	@echo "CFLAGS     = $(CFLAGS)"
	@echo "Fuentes    = $(words $(MCELIECE_SRCS)) archivos (McEliece) + libXKCP"

# Asegura que la lib de XKCP existe
$(XKCP_LIB):
	@echo ">> Falta $(XKCP_LIB). Compila XKCP con:"
	@echo "   make -C external/XKCP $(XKCP_TARGET)/libXKCP.a"
	@false

build:
	mkdir -p build

# Objetos de McEliece
build/impl_%.o: $(PARAM_DIR)/%.c | build $(XKCP_LIB)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

# bench_mceliece.c (tu archivo de medición)
build/bench_mceliece.o: bench_mceliece.c | build $(XKCP_LIB)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

# Enlace final
$(BIN): $(OBJS) $(XKCP_LIB)
	$(CC) $(CFLAGS) $(OBJS) $(LDFLAGS) $(LDLIBS) -o $@

# Atajos
ref:
	$(MAKE) IMPL=ref all

opt:
	$(MAKE) IMPL=opt all

clean:
	rm -rf build
