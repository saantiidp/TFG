#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>

#include "api.h"

#define NTESTS 50  // puedes cambiar a 1000 si quieres más precisión

// mide tiempo en milisegundos
static double get_time_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (tv.tv_sec * 1000.0) + (tv.tv_usec / 1000.0);
}

int main(void) {
    printf("McEliece Performance Test\n");
    printf("Iterations: %d\n", NTESTS);
    printf("====================================\n");

    FILE *csv = fopen("../mceliece_rendimiento.csv", "w");
    if (!csv) {
        perror("Error creando CSV");
        return 1;
    }
    fprintf(csv, "Iteration,Keygen (ms),Encaps (ms),Decaps (ms),Total (ms)\n");

    for (int i = 0; i < NTESTS; i++) {
        unsigned char pk[CRYPTO_PUBLICKEYBYTES];
        unsigned char sk[CRYPTO_SECRETKEYBYTES];
        unsigned char ct[CRYPTO_CIPHERTEXTBYTES];
        unsigned char ss1[CRYPTO_BYTES];
        unsigned char ss2[CRYPTO_BYTES];

        double t0, t1;
        double keygen_time, enc_time, dec_time, total_time;

        // KeyGen
        t0 = get_time_ms();
        crypto_kem_keypair(pk, sk);
        t1 = get_time_ms();
        keygen_time = t1 - t0;

        // Encapsulation
        t0 = get_time_ms();
        crypto_kem_enc(ct, ss1, pk);
        t1 = get_time_ms();
        enc_time = t1 - t0;

        // Decapsulation
        t0 = get_time_ms();
        crypto_kem_dec(ss2, ct, sk);
        t1 = get_time_ms();
        dec_time = t1 - t0;

        total_time = keygen_time + enc_time + dec_time;

        printf("[%02d] KeyGen: %.3f ms | Enc: %.3f ms | Dec: %.3f ms | Total: %.3f ms\n",
               i + 1, keygen_time, enc_time, dec_time, total_time);

        fprintf(csv, "%d,%.6f,%.6f,%.6f,%.6f\n",
                i + 1, keygen_time, enc_time, dec_time, total_time);
    }

    fclose(csv);
    printf("Resultados guardados en ../mceliece_rendimiento.csv\n");
    return 0;
}

