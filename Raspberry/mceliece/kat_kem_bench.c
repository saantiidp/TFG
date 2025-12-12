#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "crypto_kem.h"
#include "rng.h"

static double now()
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

int main()
{
    unsigned char *pk = malloc(crypto_kem_PUBLICKEYBYTES);
    unsigned char *sk = malloc(crypto_kem_SECRETKEYBYTES);
    unsigned char *ct = malloc(crypto_kem_CIPHERTEXTBYTES);
    unsigned char *ss = malloc(crypto_kem_BYTES);
    unsigned char *ss2 = malloc(crypto_kem_BYTES);

    if (!pk || !sk || !ct || !ss || !ss2)
    {
        fprintf(stderr, "Memory alloc error\n");
        return 1;
    }

    unsigned char entropy[48];
    for (int i = 0; i < 48; i++)
        entropy[i] = i;
    randombytes_init(entropy, NULL, 256);

    double t1, t2;
    double t_keygen, t_enc, t_dec, t_total;
    double t_start = now();

    t1 = now();
    crypto_kem_keypair(pk, sk);
    t2 = now();
    t_keygen = t2 - t1;

    t1 = now();
    crypto_kem_enc(ct, ss, pk);
    t2 = now();
    t_enc = t2 - t1;

    t1 = now();
    crypto_kem_dec(ss2, ct, sk);
    t2 = now();
    t_dec = t2 - t1;

    t_total = now() - t_start;

    printf("MCELIECE_BENCH,keygen=%.6f,enc=%.6f,dec=%.6f,total=%.6f\n",
           t_keygen, t_enc, t_dec, t_total);

    return 0;
}

