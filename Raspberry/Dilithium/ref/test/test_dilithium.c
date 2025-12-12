#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>  // Para medir el tiempo
#include "../randombytes.h"
#include "../sign.h"
#include <math.h>  // Para usar sqrt()

#define VERSION_STR(x) ((x) == 2 ? "Dilithium2" : (x) == 3 ? "Dilithium3" : "Dilithium5")

#define MLEN 1000
#define CTXLEN 14
#define NTESTS 1000 // 1000 bytes de tamaño de mensaje

int main(void)
{
    size_t i, j;
    int ret;
    size_t mlen, smlen;
    uint8_t b;
    uint8_t ctx[CTXLEN] = {0};
    uint8_t m[MLEN + CRYPTO_BYTES];
    uint8_t m2[MLEN + CRYPTO_BYTES];
    uint8_t sm[MLEN + CRYPTO_BYTES];
    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];

    char filename[256];
    snprintf(filename, sizeof(filename), "%s_REF_results.csv", VERSION_STR(DILITHIUM_MODE));


    // Variables para medir el tiempo total
    clock_t start_time, end_time;
    double keygen_time = 0.0, sign_time = 0.0, verify_time = 0.0;
    double keygen_sq_time = 0.0, sign_sq_time = 0.0, verify_sq_time = 0.0;
    double total_sq_time = 0.0;
    double total_time = 0.0;

    // Abrir archivo CSV para escritura
    FILE *csv_file = fopen(filename, "w");
    if (!csv_file) {
        fprintf(stderr, "Error opening file for writing\n");
        return -1;
    }

    // Escribir el encabezado del archivo CSV
    fprintf(csv_file, "Iteration,Keygen Time (ms),Sign Time (ms),Verify Time (ms),Total Time (ms)\n");

    for (i = 0; i < NTESTS; ++i) {
        randombytes(m, MLEN);

        // Medir tiempo de generación de claves
        start_time = clock();
        crypto_sign_keypair(pk, sk);
        end_time = clock();
        double keygen_iter_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC * 1000;
        keygen_time += keygen_iter_time;  // Acumular el tiempo de keygen
        keygen_sq_time += keygen_iter_time * keygen_iter_time;  // Acumular el cuadrado del tiempo de keygen

        // Medir tiempo de firma
        start_time = clock();
        crypto_sign(sm, &smlen, m, MLEN, ctx, CTXLEN, sk);
        end_time = clock();
        double sign_iter_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC * 1000;
        sign_time += sign_iter_time;  // Acumular el tiempo de firma
        sign_sq_time += sign_iter_time * sign_iter_time;  // Acumular el cuadrado del tiempo de firma

        // Medir tiempo de verificación
        start_time = clock();
        ret = crypto_sign_open(m2, &mlen, sm, smlen, ctx, CTXLEN, pk);
        end_time = clock();
        double verify_iter_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC * 1000;
        verify_time += verify_iter_time;  // Acumular el tiempo de verificación
        verify_sq_time += verify_iter_time * verify_iter_time;  // Acumular el cuadrado del tiempo de verificación

        // Calcular tiempo total de la iteración
        double iteration_time = keygen_iter_time + sign_iter_time + verify_iter_time;
        total_time += iteration_time;  // Acumula el tiempo total
        total_sq_time += iteration_time * iteration_time;  // Acumula el cuadrado del tiempo total

        // Escribir los resultados de esta iteración en el archivo CSV
        fprintf(csv_file, "%zu,%.4f,%.4f,%.4f,%.4f\n", i + 1, keygen_iter_time, sign_iter_time, verify_iter_time, iteration_time);

        // Validaciones de la firma
        if (ret) {
            fprintf(stderr, "Verification failed\n");
            fclose(csv_file);
            return -1;
        }
        if (smlen != MLEN + CRYPTO_BYTES) {
            fprintf(stderr, "Signed message lengths wrong\n");
            fclose(csv_file);
            return -1;
        }
        if (mlen != MLEN) {
            fprintf(stderr, "Message lengths wrong\n");
            fclose(csv_file);
            return -1;
        }
        for (j = 0; j < MLEN; ++j) {
            if (m2[j] != m[j]) {
                fprintf(stderr, "Messages don't match\n");
                fclose(csv_file);
                return -1;
            }
        }

        // Prueba de forjamiento
        randombytes((uint8_t *)&j, sizeof(j));
        do {
            randombytes(&b, 1);
        } while (!b);
        sm[j % (MLEN + CRYPTO_BYTES)] += b;
        ret = crypto_sign_open(m2, &mlen, sm, smlen, ctx, CTXLEN, pk);
        if (!ret) {
            fprintf(stderr, "Trivial forgeries possible\n");
            fclose(csv_file);
            return -1;
        }
    }

    // Imprimir resultados generales
    printf("CRYPTO_PUBLICKEYBYTES = %d\n", CRYPTO_PUBLICKEYBYTES);
    printf("CRYPTO_SECRETKEYBYTES = %d\n", CRYPTO_SECRETKEYBYTES);
    printf("CRYPTO_BYTES = %d\n", CRYPTO_BYTES);

    // Calcular la desviación típica
    double keygen_stddev = sqrt((keygen_sq_time / NTESTS) - (keygen_time / NTESTS) * (keygen_time / NTESTS));
    double sign_stddev = sqrt((sign_sq_time / NTESTS) - (sign_time / NTESTS) * (sign_time / NTESTS));
    double verify_stddev = sqrt((verify_sq_time / NTESTS) - (verify_time / NTESTS) * (verify_time / NTESTS));
    
    // Cálculos para el tiempo total y su desviación estándar
    double total_time_mean = total_time / NTESTS;
    double total_stddev = sqrt((total_sq_time / NTESTS) - (total_time_mean * total_time_mean));

    // Mostrar el tiempo medio y la desviación estándar
    printf("Medio keygen time: %.4f ms\n", (keygen_time / NTESTS));  // Mostrar tiempo medio
    printf("Desviación típica keygen time: %.4f ms\n", keygen_stddev);  // Mostrar desviación típica

    printf("Media sign time: %.4f ms\n", (sign_time / NTESTS));  
    printf("Desviación típica sign time: %.4f ms\n", sign_stddev);  

    printf("Media verify time: %.4f ms\n", (verify_time / NTESTS));  
    printf("Desviación típica verify time: %.4f ms\n", verify_stddev);  

    printf("Tiempo total medio: %.4f ms\n", total_time_mean);
    printf("Desviación típica tiempo total: %.4f ms\n", total_stddev);
    // Cerrar el archivo CSV
    fclose(csv_file);

    return 0;
}
