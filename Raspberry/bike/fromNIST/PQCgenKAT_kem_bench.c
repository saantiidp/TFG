// ============================================================================
//  BIKE Benchmark (Santiago de Prada, 2025)
//  Mide tiempo medio y desviación estándar de KeyGen / Encaps / Decaps
//  para las tres variantes: BIKE-128, BIKE-192 y BIKE-256.
//  Compilar con:
//     make bike-bench-128
//     make bike-bench-192
//     make bike-bench-256
// ============================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include "api.h"
#include "kem.h"

#define NTESTS_DEFAULT 1000

// --------------------------------------------------------------------------
// Calcula la diferencia entre dos marcas de tiempo en milisegundos
// --------------------------------------------------------------------------
static double timediff_ms(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) * 1000.0 +
           (end.tv_nsec - start.tv_nsec) / 1.0e6;
}

// --------------------------------------------------------------------------
// Programa principal
// --------------------------------------------------------------------------
int main(int argc, char *argv[]) {
    int ntests = NTESTS_DEFAULT;
    if (argc > 1) ntests = atoi(argv[1]);

    // Detectar la versión de BIKE compilada (definida por el Makefile)
#if defined(BIKE1_L1)
    int variant = 128;
    printf("🔹 Usando parámetros BIKE-128 (Level 1)\n");
#elif defined(BIKE1_L3)
    int variant = 192;
    printf("🔹 Usando parámetros BIKE-192 (Level 3)\n");
#elif defined(BIKE1_L5)
    int variant = 256;
    printf("🔹 Usando parámetros BIKE-256 (Level 5)\n");
#else
    int variant = 128;
    printf("⚠️ Versión no definida, usando BIKE-128 por defecto.\n");
#endif

    printf("=== BIKE Benchmark (%d iteraciones) ===\n", ntests);

    // Buffers para claves y mensajes
    unsigned char pk[CRYPTO_PUBLICKEYBYTES];
    unsigned char sk[CRYPTO_SECRETKEYBYTES];
    unsigned char ct[CRYPTO_CIPHERTEXTBYTES];
    unsigned char ss1[CRYPTO_BYTES];
    unsigned char ss2[CRYPTO_BYTES];

    // Arrays para almacenar los tiempos por iteración
    double keygen_times[ntests];
    double enc_times[ntests];
    double dec_times[ntests];

    struct timespec t1, t2;

    // ----------------------------------------------------------------------
    // Bucle principal de medición
    // ----------------------------------------------------------------------
    for (int i = 0; i < ntests; i++) {
        // --- KeyGen ---
        clock_gettime(CLOCK_MONOTONIC, &t1);
        crypto_kem_keypair(pk, sk);
        clock_gettime(CLOCK_MONOTONIC, &t2);
        keygen_times[i] = timediff_ms(t1, t2);

        // --- Encaps ---
        clock_gettime(CLOCK_MONOTONIC, &t1);
        crypto_kem_enc(ct, ss1, pk);
        clock_gettime(CLOCK_MONOTONIC, &t2);
        enc_times[i] = timediff_ms(t1, t2);

        // --- Decaps ---
        clock_gettime(CLOCK_MONOTONIC, &t1);
        crypto_kem_dec(ss2, ct, sk);
        clock_gettime(CLOCK_MONOTONIC, &t2);
        dec_times[i] = timediff_ms(t1, t2);

        // Verificación
        if (memcmp(ss1, ss2, CRYPTO_BYTES) != 0) {
            printf("❌ Error en iteración %d: ss1 != ss2\n", i);
            return 1;
        }
    }

    // ----------------------------------------------------------------------
    // Cálculo de medias y desviaciones estándar
    // ----------------------------------------------------------------------
    double k_mean=0, e_mean=0, d_mean=0;
    double k_std=0, e_std=0, d_std=0;

    for (int i=0; i<ntests; i++) {
        k_mean += keygen_times[i];
        e_mean += enc_times[i];
        d_mean += dec_times[i];
    }
    k_mean /= ntests;
    e_mean /= ntests;
    d_mean /= ntests;

    for (int i=0; i<ntests; i++) {
        k_std += pow(keygen_times[i]-k_mean,2);
        e_std += pow(enc_times[i]-e_mean,2);
        d_std += pow(dec_times[i]-d_mean,2);
    }
    k_std = sqrt(k_std/ntests);
    e_std = sqrt(e_std/ntests);
    d_std = sqrt(d_std/ntests);

    double total_mean = k_mean + e_mean + d_mean;
    double total_std  = sqrt(k_std*k_std + e_std*e_std + d_std*d_std);

    // ----------------------------------------------------------------------
    // Resultados finales
    // ----------------------------------------------------------------------
    printf("\n=== Resultados BIKE-%d ===\n", variant);
    printf("KeyGen: %.4f ms (± %.4f)\n", k_mean, k_std);
    printf("Encaps: %.4f ms (± %.4f)\n", e_mean, e_std);
    printf("Decaps: %.4f ms (± %.4f)\n", d_mean, d_std);
    printf("Total:  %.4f ms (± %.4f)\n", total_mean, total_std);
    printf("========================\n");

    return 0;
}

