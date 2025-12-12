CC ?= gcc
AR ?= ar
CFLAGS = -O3 -Wall -Wextra -Wpedantic -Wshadow -Wvla -Werror \
         -Wredundant-decls -Wmissing-prototypes -std=c99 -I../../common

PORTABLE_OBJS = \
	code.o fft.o gf.o gf2x.o hqc.o kem.o parsing.o \
	reed_muller.o reed_solomon.o shake_ds.o shake_prng.o vector.o

NEON_FLAGS = -march=armv8.2-a+simd -funroll-loops -ftree-vectorize -mcpu=cortex-a76

.PHONY: all clean

all: libhqc-128_portable.a libhqc-128_neon.a

libhqc-128_portable.a: $(PORTABLE_OBJS)
	$(AR) -r $@ $^

libhqc-128_neon.a:
	$(MAKE) clean
	$(CC) $(CFLAGS) $(NEON_FLAGS) -c *.c
	$(AR) -r $@ *.o

clean:
	rm -f *.o
	rm -f libhqc-128_portable.a
	rm -f libhqc-128_neon.a

