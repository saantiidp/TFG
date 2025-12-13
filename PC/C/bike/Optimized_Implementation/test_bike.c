#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include "kem.h"

#define NTESTS 1000

double get_time_ms() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1000.0 + t.tv_nsec / 1e6;
}

int main() {
    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];
    uint8_t ct[CRYPTO_CIPHERTEXTBYTES];
    uint8_t ss_a[CRYPTO_BYTES], ss_b[CRYPTO_BYTES];

    FILE *csv_file = fopen("bike_rendimiento.csv", "w");
    if (!csv_file) {
        perror("No se pudo abrir el archivo de salida");
        return 1;
    }

    // Cabecera del CSV
    fprintf(csv_file, "Iteration,Keygen Time (ms),Enc Time (ms),Dec Time (ms),Total Time (ms)\n");

    for (int i = 0; i < NTESTS; i++) {
        double t0, t1;
        double keygen_time, enc_time, dec_time, total_time;

        // Keygen
        t0 = get_time_ms();
        crypto_kem_keypair(pk, sk);
        t1 = get_time_ms();
        keygen_time = t1 - t0;

        // Enc
        t0 = get_time_ms();
        crypto_kem_enc(ct, ss_a, pk);
        t1 = get_time_ms();
        enc_time = t1 - t0;

        // Dec
        t0 = get_time_ms();
        crypto_kem_dec(ss_b, ct, sk);
        t1 = get_time_ms();
        dec_time = t1 - t0;

        if (memcmp(ss_a, ss_b, CRYPTO_BYTES) != 0) {
            fprintf(stderr, "ERROR: Las shared secrets no coinciden\n");
            fclose(csv_file);
            return 1;
        }

        total_time = keygen_time + enc_time + dec_time;

        fprintf(csv_file, "%d,%.4f,%.4f,%.4f,%.4f\n",
                i, keygen_time, enc_time, dec_time, total_time);
    }

    fclose(csv_file);
    printf("Resultados guardados en bike_rendimiento.csv\n");
    return 0;
}
