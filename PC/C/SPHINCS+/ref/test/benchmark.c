// ref/test/benchmark.c
// Benchmark genérico para todas las variantes SPHINCS+ de la referencia.
// Se compila dentro de cada carpeta de variante y enlaza con su api.h/implementación.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "api.h"  
#include <math.h> 


// cronómetro en ms (CLOCK_MONOTONIC)
static inline double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
}

static double mean(const double *x, int n) {
    double s = 0.0;
    for (int i = 0; i < n; i++) s += x[i];
    return s / (double)n;
}

static double stdev(const double *x, int n, double m) {
    double v = 0.0;
    for (int i = 0; i < n; i++) {
        double d = x[i] - m;
        v += d * d;
    }
    v /= (double)n;
    return sqrt(v);
}

int main(int argc, char **argv) {
    int ITER = 10;
    if (argc >= 2) {
        ITER = atoi(argv[1]);
        if (ITER <= 0) ITER = 10;
    }

    unsigned char *pk = malloc(CRYPTO_PUBLICKEYBYTES);
    unsigned char *sk = malloc(CRYPTO_SECRETKEYBYTES);

    unsigned char message[] = "Benchmark SPHINCS+ reference impl";
    size_t mlen = sizeof(message) - 1;

    unsigned char *sig = malloc(CRYPTO_BYTES);
    size_t siglen = 0;

    double *t_keygen = malloc(sizeof(double)*ITER);
    double *t_sign   = malloc(sizeof(double)*ITER);
    double *t_vrfy   = malloc(sizeof(double)*ITER);

    if (!pk || !sk || !sig || !t_keygen || !t_sign || !t_vrfy) {
        fprintf(stderr, "Memoria insuficiente\n");
        return 1;
    }

    // Cabecera CSV
    // CRYPTO_ALGNAME viene de api.h de cada variante
    printf("Iteracion,Algoritmo,KeyGen_ms,Sign_ms,Verify_ms,Total_ms\n");

    for (int i = 0; i < ITER; i++) {
        double t0, t1;

        // KeyGen
        t0 = now_ms();
        if (crypto_sign_keypair(pk, sk) != 0) {
            fprintf(stderr, "KeyGen fallo\n");
            return 2;
        }
        t1 = now_ms();
        t_keygen[i] = t1 - t0;

        // Sign (firma separada)
        t0 = now_ms();
        if (crypto_sign_signature(sig, &siglen, message, mlen, sk) != 0) {
            fprintf(stderr, "Sign fallo\n");
            return 3;
        }
        t1 = now_ms();
        t_sign[i] = t1 - t0;

        // Verify
        t0 = now_ms();
        if (crypto_sign_verify(sig, siglen, message, mlen, pk) != 0) {
            fprintf(stderr, "Verify fallo\n");
            return 4;
        }
        t1 = now_ms();
        t_vrfy[i] = t1 - t0;

        double total = t_keygen[i] + t_sign[i] + t_vrfy[i];
        printf("%d,%s,%.4f,%.4f,%.4f,%.4f\n",
               i+1, CRYPTO_ALGNAME, t_keygen[i], t_sign[i], t_vrfy[i], total);
        fflush(stdout);
    }

    // Resumen
    double mk = mean(t_keygen, ITER), skd = stdev(t_keygen, ITER, mk);
    double ms = mean(t_sign, ITER),   ssd = stdev(t_sign,   ITER, ms);
    double mv = mean(t_vrfy, ITER),   vsd = stdev(t_vrfy,   ITER, mv);

    fprintf(stderr, "\n[%s] ITER=%d\n", CRYPTO_ALGNAME, ITER);
    fprintf(stderr, "KeyGen:   %.4f ms (± %.4f)\n", mk, skd);
    fprintf(stderr, "Sign:     %.4f ms (± %.4f)\n", ms, ssd);
    fprintf(stderr, "Verify:   %.4f ms (± %.4f)\n", mv, vsd);
    fprintf(stderr, "Total:    %.4f ms (± %.4f)\n", (mk+ms+mv), sqrt(skd*skd+ssd*ssd+vsd*vsd));

    free(pk); free(sk); free(sig);
    free(t_keygen); free(t_sign); free(t_vrfy);
    return 0;
}
