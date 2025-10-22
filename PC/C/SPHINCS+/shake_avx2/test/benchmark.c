#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <stdint.h>
#include <stdlib.h>
#include "api.h"   // lo encuentra por -Icrypto_sign/<variante>

static double ns_to_ms(long ns) { return (double)ns / 1e6; }

static long diff_ns(struct timespec a, struct timespec b) {
    long sec = b.tv_sec - a.tv_sec;
    long nsec = b.tv_nsec - a.tv_nsec;
    return sec * 1000000000L + nsec;
}

int main(void) {
    const int N = 10;  // número de iteraciones
    unsigned char *pk = malloc(CRYPTO_PUBLICKEYBYTES);
    unsigned char *sk = malloc(CRYPTO_SECRETKEYBYTES);
    unsigned char m[32] = {0};
    unsigned char sig[CRYPTO_BYTES];
    size_t siglen = 0;

    if (!pk || !sk) {
        fprintf(stderr, "alloc failed\n");
        return 1;
    }

    printf("Iteracion,Algoritmo,KeyGen_ms,Sign_ms,Verify_ms,Total_ms\n");

    for (int i = 1; i <= N; i++) {
        struct timespec t0, t1, t2, t3, t4;
        long ns_key=0, ns_sign=0, ns_ver=0, ns_total=0;

        // KeyGen
        clock_gettime(CLOCK_MONOTONIC, &t0);
        if (CRYPTO_PUBLICKEYBYTES == 0 || CRYPTO_SECRETKEYBYTES == 0) return 1;
        if (crypto_sign_keypair(pk, sk) != 0) { fprintf(stderr, "keypair fail\n"); return 1; }
        clock_gettime(CLOCK_MONOTONIC, &t1);

        // Sign
        clock_gettime(CLOCK_MONOTONIC, &t2);
        siglen = CRYPTO_BYTES;
        if (crypto_sign_signature(sig, &siglen, m, sizeof m, sk) != 0) { fprintf(stderr, "sign fail\n"); return 1; }
        clock_gettime(CLOCK_MONOTONIC, &t3);

        // Verify
        clock_gettime(CLOCK_MONOTONIC, &t4); // t4 reusa después
        if (crypto_sign_verify(sig, siglen, m, sizeof m, pk) != 0) { fprintf(stderr, "verify fail\n"); return 1; }
        struct timespec t5; clock_gettime(CLOCK_MONOTONIC, &t5);

        ns_key  = diff_ns(t0, t1);
        ns_sign = diff_ns(t2, t3);
        ns_ver  = diff_ns(t4, t5);
        ns_total = diff_ns(t0, t5);

        printf("%d,SPHINCS+,%.4f,%.4f,%.4f,%.4f\n",
               i,
               ns_to_ms(ns_key),
               ns_to_ms(ns_sign),
               ns_to_ms(ns_ver),
               ns_to_ms(ns_total));
        fflush(stdout);
    }

    free(pk); free(sk);
    return 0;
}
