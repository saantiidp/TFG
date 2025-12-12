CC ?= /usr/bin/cc
CFLAGS += -Wall -Wextra -Wpedantic -Wmissing-prototypes -Wredundant-decls \
  -Wshadow -Wpointer-arith -march=armv8.2-a+simd -mtune=cortex-a76 -O3 \
  -fomit-frame-pointer -z noexecstack
NISTFLAGS += -Wno-unused-result -march=armv8.2-a+simd -mtune=cortex-a76 -O3 -fomit-frame-pointer
RM = /bin/rm
LIBPAPI = lib/libpapi.a


SOURCES = kex.c kem.c indcpa.c polyvec.c neon_polyvec.c poly.c neon_poly.c neon_ntt.c cbd.c reduce.c verify.c
SOURCESKECCAK = $(SOURCES) fips202x2.c fips202.c neon_symmetric-shake.c symmetric-shake.c rejsample.c
SOURCESNINETIES = $(SOURCES) sha256.c sha512.c aes256ctr.c symmetric-aes.c
HEADERS = params.h kex.h kem.h indcpa.h polyvec.h poly.h neon_ntt.h cbd.h reduce.h verify.h symmetric.h rejsample.h
HEADERSKECCAK = $(HEADERS) fips202.h fips202x2.h
HEADERSNINETIES = $(HEADERS) aes256ctr.h sha2.h

.PHONY: all shared speed clean

all: \
  test_kyber512 \
  test_kyber768 \
  test_kyber1024 \

shared: \
  libpqcrystals_kyber512_neon.so \
  libpqcrystals_kyber768_neon.so \
  libpqcrystals_kyber1024_neon.so \
  libpqcrystals_kyber512-90s_neon.so \
  libpqcrystals_kyber768-90s_neon.so \
  libpqcrystals_kyber1024-90s_neon.so \
  libpqcrystals_fips202_neon.so \
  libpqcrystals_sha2_neon.so

libpqcrystals_fips202_neon.so: fips202.c fips202.h
	$(CC) -shared -fPIC $(CFLAGS) fips202.c -o libpqcrystals_fips202_neon.so

libpqcrystals_sha2_neon.so: sha256.c sha512.c sha2.h
	$(CC) -shared -fPIC $(CFLAGS) sha256.c sha512.c -o libpqcrystals_sha2_neon.so

libpqcrystals_kyber512_neon.so: $(SOURCES) $(HEADERS) symmetric-shake.c
	$(CC) -shared -fPIC $(CFLAGS) -DKYBER_K=2 $(SOURCES) symmetric-shake.c -o libpqcrystals_kyber512_neon.so

libpqcrystals_kyber768_neon.so: $(SOURCES) $(HEADERS) symmetric-shake.c
	$(CC) -shared -fPIC $(CFLAGS) -DKYBER_K=3 $(SOURCES) symmetric-shake.c -o libpqcrystals_kyber768_neon.so

libpqcrystals_kyber1024_neon.so: $(SOURCES) $(HEADERS) symmetric-shake.c
	$(CC) -shared -fPIC $(CFLAGS) -DKYBER_K=4 $(SOURCES) symmetric-shake.c -o libpqcrystals_kyber1024_neon.so

test_kyber512: $(SOURCESKECCAK) $(HEADERSKECCAK) test_kyber.c randombytes.c
	$(CC) $(CFLAGS) -DKYBER_K=2 $(SOURCESKECCAK) randombytes.c test_kyber.c -o test_kyber512 -lm

test_kyber768: $(SOURCESKECCAK) $(HEADERSKECCAK) test_kyber.c randombytes.c
	$(CC) $(CFLAGS) -DKYBER_K=3 $(SOURCESKECCAK) randombytes.c test_kyber.c -o test_kyber768 -lm

test_kyber1024: $(SOURCESKECCAK) $(HEADERSKECCAK) test_kyber.c randombytes.c
	$(CC) $(CFLAGS) -DKYBER_K=4 $(SOURCESKECCAK) randombytes.c test_kyber.c -o test_kyber1024 -lm

clean:
	-$(RM) -rf *.gcno *.gcda *.lcov *.o *.so *.req
	-$(RM) -rf test_kyber512
	-$(RM) -rf test_kyber768
	-$(RM) -rf test_kyber1024
	-$(RM) -rf test_kex512
	-$(RM) -rf test_kex768
	-$(RM) -rf test_kex1024
	-$(RM) -rf test_vectors512
	-$(RM) -rf test_vectors768
	-$(RM) -rf test_vectors1024
	-$(RM) -rf test_speed512
	-$(RM) -rf test_speed768
	-$(RM) -rf test_speed1024
	-$(RM) -rf test_kyber512-90s
	-$(RM) -rf test_kyber768-90s
	-$(RM) -rf test_kyber1024-90s
	-$(RM) -rf test_kex512-90s
	-$(RM) -rf test_kex768-90s
	-$(RM) -rf test_kex1024-90s
	-$(RM) -rf test_vectors512-90s
	-$(RM) -rf test_vectors768-90s
	-$(RM) -rf test_vectors1024-90s
	-$(RM) -rf test_speed512-90s
	-$(RM) -rf test_speed768-90s
	-$(RM) -rf test_speed1024-90s
	-$(RM) -rf PQCgenKAT_kem512
	-$(RM) -rf PQCgenKAT_kem768
	-$(RM) -rf PQCgenKAT_kem1024
	-$(RM) -rf PQCgenKAT_kem512-90s
	-$(RM) -rf PQCgenKAT_kem768-90s
	-$(RM) -rf PQCgenKAT_kem1024-90s
	-$(RM) -rf test_speedusec512
	-$(RM) -rf test_speedusec768
	-$(RM) -rf test_speedusec1024
	-$(RM) -rf test_speed512keccak
	-$(RM) -rf test_speed768keccak
	-$(RM) -rf test_speed1024keccak
	-$(RM) -rf test_speed_ntt

bench:
	./test_speed512
	./test_speed768
	./test_speed1024
	./test_speed_ntt

bench_keccak:
	taskset 0x1 ./test_speed512keccak
	taskset 0x1 ./test_speed768keccak
	taskset 0x1 ./test_speed1024keccak
