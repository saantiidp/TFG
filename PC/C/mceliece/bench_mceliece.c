// bench_mceliece.c - microbench CSV para Classic McEliece (ref vs avx)
// compila enlazando con las fuentes de la impl. elegida (ver Makefile)
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Los headers api.h vienen de crypto_kem/<param>/<impl>/
#include "api.h"

static double now_ms(void){
    struct timespec ts;
#if defined(CLOCK_MONOTONIC_RAW)
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
#else
    clock_gettime(CLOCK_MONOTONIC, &ts);
#endif
    return (double)ts.tv_sec*1000.0 + (double)ts.tv_nsec/1.0e6;
}

int main(int argc, char**argv){
    int iters = (argc>1)? atoi(argv[1]) : 100;  // iteraciones
    const char* version = (argc>2)? argv[2] : "ref"; // etiqueta (ref/avx)
    const char* param   = (argc>3)? argv[3] : "mcelieceXXXX"; // etiqueta parámetro

    unsigned char *pk  = malloc(CRYPTO_PUBLICKEYBYTES);
    unsigned char *sk  = malloc(CRYPTO_SECRETKEYBYTES);
    unsigned char *ct  = malloc(CRYPTO_CIPHERTEXTBYTES);
    unsigned char *ss1 = malloc(CRYPTO_BYTES);
    unsigned char *ss2 = malloc(CRYPTO_BYTES);
    if(!pk||!sk||!ct||!ss1||!ss2){ fprintf(stderr,"mem\n"); return 1; }

    // CSV header
    printf("Iteracion,Version,Parametro,Tiempo_KeyGen_ms,Tiempo_Encaps_ms,Tiempo_Decaps_ms,Tiempo_Total_ms\n");

    for(int i=1;i<=iters;i++){
        double t_all0 = now_ms();

        // KeyGen
        double t0 = now_ms();
        int r = crypto_kem_keypair(pk, sk);
        double t1 = now_ms();
        if(r){ fprintf(stderr,"keypair fail\n"); return 2; }
        double t_key = t1 - t0;

        // Encaps
        t0 = now_ms();
        r = crypto_kem_enc(ct, ss1, pk);
        t1 = now_ms();
        if(r){ fprintf(stderr,"enc fail\n"); return 3; }
        double t_enc = t1 - t0;

        // Decaps
        t0 = now_ms();
        r = crypto_kem_dec(ss2, ct, sk);
        t1 = now_ms();
        if(r){ fprintf(stderr,"dec fail\n"); return 4; }
        double t_dec = t1 - t0;

        if(memcmp(ss1, ss2, CRYPTO_BYTES)!=0){
            fprintf(stderr,"shared secret mismatch\n");
            return 5;
        }

        double t_all1 = now_ms();
        double t_tot = t_all1 - t_all0;

        printf("%d,%s,%s,%.6f,%.6f,%.6f,%.6f\n",
               i, version, param, t_key, t_enc, t_dec, t_tot);
        fflush(stdout);
    }

    free(pk); free(sk); free(ct); free(ss1); free(ss2);
    return 0;
}
