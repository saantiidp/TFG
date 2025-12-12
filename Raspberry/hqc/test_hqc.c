// test_hqc.c
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

// ===== Selección de nivel (define uno en la línea de compilación): HQC128 / HQC192 / HQC256 =====
#if defined(HQC128)
  #include "hqc-128/clean/api.h"
  #define CRYPTO_PUBLICKEYBYTES    PQCLEAN_HQC128_CLEAN_CRYPTO_PUBLICKEYBYTES
  #define CRYPTO_SECRETKEYBYTES    PQCLEAN_HQC128_CLEAN_CRYPTO_SECRETKEYBYTES
  #define CRYPTO_CIPHERTEXTBYTES   PQCLEAN_HQC128_CLEAN_CRYPTO_CIPHERTEXTBYTES
  #define CRYPTO_BYTES             PQCLEAN_HQC128_CLEAN_CRYPTO_BYTES
  #define crypto_kem_keypair       PQCLEAN_HQC128_CLEAN_crypto_kem_keypair
  #define crypto_kem_enc           PQCLEAN_HQC128_CLEAN_crypto_kem_enc
  #define crypto_kem_dec           PQCLEAN_HQC128_CLEAN_crypto_kem_dec
#elif defined(HQC192)
  #include "hqc-192/clean/api.h"
  #define CRYPTO_PUBLICKEYBYTES    PQCLEAN_HQC192_CLEAN_CRYPTO_PUBLICKEYBYTES
  #define CRYPTO_SECRETKEYBYTES    PQCLEAN_HQC192_CLEAN_CRYPTO_SECRETKEYBYTES
  #define CRYPTO_CIPHERTEXTBYTES   PQCLEAN_HQC192_CLEAN_CRYPTO_CIPHERTEXTBYTES
  #define CRYPTO_BYTES             PQCLEAN_HQC192_CLEAN_CRYPTO_BYTES
  #define crypto_kem_keypair       PQCLEAN_HQC192_CLEAN_crypto_kem_keypair
  #define crypto_kem_enc           PQCLEAN_HQC192_CLEAN_crypto_kem_enc
  #define crypto_kem_dec           PQCLEAN_HQC192_CLEAN_crypto_kem_dec
#elif defined(HQC256)
  #include "hqc-256/clean/api.h"
  #define CRYPTO_PUBLICKEYBYTES    PQCLEAN_HQC256_CLEAN_CRYPTO_PUBLICKEYBYTES
  #define CRYPTO_SECRETKEYBYTES    PQCLEAN_HQC256_CLEAN_CRYPTO_SECRETKEYBYTES
  #define CRYPTO_CIPHERTEXTBYTES   PQCLEAN_HQC256_CLEAN_CRYPTO_CIPHERTEXTBYTES
  #define CRYPTO_BYTES             PQCLEAN_HQC256_CLEAN_CRYPTO_BYTES
  #define crypto_kem_keypair       PQCLEAN_HQC256_CLEAN_crypto_kem_keypair
  #define crypto_kem_enc           PQCLEAN_HQC256_CLEAN_crypto_kem_enc
  #define crypto_kem_dec           PQCLEAN_HQC256_CLEAN_crypto_kem_dec
#else
  #error "Define HQC128 o HQC192 o HQC256 al compilar"
#endif

// ---- utilidades de tiempo ----
static inline double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
}

typedef struct {
    double mean;
    double std;
} stat_t;

static stat_t stats(const double *v, int n) {
    double s = 0.0, s2 = 0.0;
    for (int i=0;i<n;i++){ s += v[i]; s2 += v[i]*v[i]; }
    double mu = s / n;
    double var = (s2 / n) - (mu * mu);
    if (var < 0) var = 0; // por estabilidad numérica
    stat_t out = { mu, sqrt(var) };
    return out;
}

int main(void) {
    // buffers
    unsigned char pk[CRYPTO_PUBLICKEYBYTES];
    unsigned char sk[CRYPTO_SECRETKEYBYTES];
    unsigned char ct[CRYPTO_CIPHERTEXTBYTES];
    unsigned char ss1[CRYPTO_BYTES], ss2[CRYPTO_BYTES];

    // iteraciones (puedes ajustar aquí)
    const int ITERS = 1000;

    // vectores de tiempos
    double t_key[ITERS], t_enc[ITERS], t_dec[ITERS], t_tot[ITERS];

    for (int i = 0; i < ITERS; i++) {
        double t0 = now_ms();
        double t1, t2, t3, t4;

        // KeyGen
        t1 = now_ms();
        crypto_kem_keypair(pk, sk);
        t2 = now_ms();

        // Encaps
        crypto_kem_enc(ct, ss1, pk);
        t3 = now_ms();

        // Decaps
        crypto_kem_dec(ss2, ct, sk);
        t4 = now_ms();

        // comprobar
        if (memcmp(ss1, ss2, CRYPTO_BYTES) != 0) {
            fprintf(stderr, "Shared secret mismatch en iter %d\n", i);
            return 1;
        }

        t_key[i] = (t2 - t1);
        t_enc[i] = (t3 - t2);
        t_dec[i] = (t4 - t3);
        t_tot[i] = (t4 - t0);
    }

    stat_t skey = stats(t_key, ITERS);
    stat_t senc = stats(t_enc, ITERS);
    stat_t sdec = stats(t_dec, ITERS);
    stat_t stot = stats(t_tot, ITERS);

    printf("KeyGen: %.4f ms (± %.4f)\n", skey.mean, skey.std);
    printf("Encaps: %.4f ms (± %.4f)\n", senc.mean, senc.std);
    printf("Decaps: %.4f ms (± %.4f)\n", sdec.mean, sdec.std);
    printf("Total:  %.4f ms (± %.4f)\n", stot.mean, stot.std);
    return 0;
}

