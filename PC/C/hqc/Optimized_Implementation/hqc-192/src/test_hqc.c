#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include "api.h"

#define NTESTS 1000

int main(void) {
    printf("USANDO clock() - OK\n");

    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];
    uint8_t ct[CRYPTO_CIPHERTEXTBYTES];
    uint8_t ss[CRYPTO_BYTES], ss2[CRYPTO_BYTES];

    clock_t t0, t1;
    double t_keygen, t_enc, t_dec;

    FILE *f = fopen("bench_hqc192_avx2.csv", "w");
    if (!f) {
        perror("fopen");
        return 1;
    }

    fprintf(f, "keygen_ms,enc_ms,dec_ms\n");

    for (int i = 0; i < NTESTS; i++) {
        t0 = clock();
        crypto_kem_keypair(pk, sk);
        t1 = clock();
        t_keygen = ((double)(t1 - t0)) * 1000.0 / CLOCKS_PER_SEC;

        t0 = clock();
        crypto_kem_enc(ct, ss, pk);
        t1 = clock();
        t_enc = ((double)(t1 - t0)) * 1000.0 / CLOCKS_PER_SEC;

        t0 = clock();
        crypto_kem_dec(ss2, ct, sk);
        t1 = clock();
        t_dec = ((double)(t1 - t0)) * 1000.0 / CLOCKS_PER_SEC;

        if (memcmp(ss, ss2, CRYPTO_BYTES) != 0) {
            fprintf(stderr, "ERROR: shared secrets do not match\n");
            fclose(f);
            return 1;
        }

        fprintf(f, "%.3f,%.3f,%.3f\n", t_keygen, t_enc, t_dec);
    }

    fclose(f);
    return 0;
}
