// test/bench_csv.c
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "api.h"   // vendrá por -I<ruta variante> desde el Makefile

// cronómetro en ms (double)
static double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
}

static int read_env_u32(const char *name, int defval) {
    const char *s = getenv(name);
    if (!s || !*s) return defval;
    char *end = NULL;
    long v = strtol(s, &end, 10);
    if (!end || *end || v <= 0 || v > 100000) return defval;
    return (int)v;
}

int main(void) {
    // Iteraciones: por defecto 8 como en tu ejemplo; puedes cambiar con ITERS=...
    const int iters = read_env_u32("ITERS", 8);

    unsigned char *pk = malloc(CRYPTO_PUBLICKEYBYTES);
    unsigned char *sk = malloc(CRYPTO_SECRETKEYBYTES);
    if (!pk || !sk) return 1;

    // Mensaje fijo (no hace falta RNG para SPHINCS+)
    const size_t mlen = 32;
    unsigned char m[32];
    for (size_t i = 0; i < mlen; i++) m[i] = (unsigned char)i;

    // Buffers para firma
    size_t siglen = 0;
    unsigned char *sig = malloc(CRYPTO_BYTES);
    if (!sig) return 1;

    // Cabecera CSV
    printf("Iteracion,Algoritmo,KeyGen_ms,Sign_ms,Verify_ms,Total_ms\n");

    for (int i = 1; i <= iters; i++) {
        // KeyGen
        double t0 = now_ms();
        if (crypto_sign_keypair(pk, sk) != 0) return 2;
        double t1 = now_ms();

        // Sign
        double t2 = now_ms();
        if (crypto_sign_signature(sig, &siglen, m, (unsigned long long)mlen, sk) != 0) return 3;
        double t3 = now_ms();

        // Verify
        double t4 = now_ms();
        if (crypto_sign_verify(sig, siglen, m, (unsigned long long)mlen, pk) != 0) return 4;
        double t5 = now_ms();

        double key_ms = t1 - t0;
        double sig_ms = t3 - t2;
        double ver_ms = t5 - t4;
        double tot_ms = key_ms + sig_ms + ver_ms;

        // Algoritmo = SPHINCS+ (como pides)
        printf("%d,SPHINCS+,%0.4f,%0.4f,%0.4f,%0.4f\n",
               i, key_ms, sig_ms, ver_ms, tot_ms);
    }

    free(pk);
    free(sk);
    free(sig);
    return 0;
}
