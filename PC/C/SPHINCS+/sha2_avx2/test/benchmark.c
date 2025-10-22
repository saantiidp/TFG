#define _POSIX_C_SOURCE 199309L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <sys/stat.h>  // Para verificar si el archivo existe

#include "../api.h"

#define MLEN 59
#define NUM_ITERATIONS 70 // Número de iteraciones para medir el tiempo

char *showhex(uint8_t a[], int size);

char *showhex(uint8_t a[], int size) {
    char *s = malloc(size * 2 + 1);
    for (int i = 0; i < size; i++)
        sprintf(s + i * 2, "%02x", a[i]);
    return s;
}

// Función para calcular la desviación estándar
double stddev(double times[], int n) {
    double mean = 0.0;
    double sum_deviation = 0.0;
    for (int i = 0; i < n; i++) {
        mean += times[i];
    }
    mean /= n;

    for (int i = 0; i < n; i++) {
        sum_deviation += (times[i] - mean) * (times[i] - mean);
    }
    return sqrt(sum_deviation / n);
}

// Función para verificar si un archivo existe
int file_exists(const char *filename) {
    struct stat buffer;
    return (stat(filename, &buffer) == 0);
}

int main(void) {
    size_t i, j;
    int ret;
    size_t mlen, smlen;
    uint8_t b;
    uint8_t m[MLEN + CRYPTO_BYTES];
    uint8_t m2[MLEN + CRYPTO_BYTES];
    uint8_t sm[MLEN + CRYPTO_BYTES];
    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];
    
    // Arreglos para almacenar los tiempos
    double keygen_times[NUM_ITERATIONS];
    double sign_times[NUM_ITERATIONS];
    double verify_times[NUM_ITERATIONS];

    // Obtener el nombre del algoritmo de la constante CRYPTO_ALGNAME
    const char *version_name = CRYPTO_ALGNAME;
    
    // Crear el nombre del archivo basado en el nombre de la versión del algoritmo
    char filename[100];
    snprintf(filename, sizeof(filename), "%s.csv", version_name);

    // Abrir archivo CSV en modo añadir ("a")
    FILE *csv_file = fopen(filename, "a");
    if (!csv_file) {
        perror("No se pudo abrir el archivo");
        return -1;
    }

    // Verificar si el archivo está vacío o es nuevo para añadir el encabezado
    if (!file_exists(filename) || ftell(csv_file) == 0) {
        fprintf(csv_file, "Iteración,Tiempo Generación Claves (ms),Tiempo Firma (ms),Tiempo Verificación (ms),Tiempo Total (ms)\n");
    }

    // Medir la generación de claves y escribir en el archivo
    for (i = 0; i < NUM_ITERATIONS; i++) {
        clock_t start_time = clock();
        crypto_sign_keypair(pk, sk);
        clock_t end_time = clock();
        keygen_times[i] = (double)(end_time - start_time) / CLOCKS_PER_SEC * 1000;  // Convertir a ms
    }

    // Medir la firma y escribir en el archivo
    for (i = 0; i < NUM_ITERATIONS; i++) {
        randombytes(m, MLEN);
        clock_t start_time = clock();
        crypto_sign(sm, &smlen, m, MLEN, sk);
        clock_t end_time = clock();
        sign_times[i] = (double)(end_time - start_time) / CLOCKS_PER_SEC * 1000; 
    }

    // Medir la verificación y escribir en el archivo
    for (i = 0; i < NUM_ITERATIONS; i++) {
        randombytes(m, MLEN);
        crypto_sign(sm, &smlen, m, MLEN, sk);
        clock_t start_time = clock();
        ret = crypto_sign_open(m2, &mlen, sm, smlen, pk);
        clock_t end_time = clock();
        verify_times[i] = (double)(end_time - start_time) / CLOCKS_PER_SEC * 1000; 
    }

    // Escribir los tiempos de cada iteración en el archivo CSV
    for (i = 0; i < NUM_ITERATIONS; i++) {
        double total_time = keygen_times[i] + sign_times[i] + verify_times[i];
        fprintf(csv_file, "%zu,%.4f,%.4f,%.4f,%.4f\n", i + 1, keygen_times[i], sign_times[i], verify_times[i], total_time);
    }

    // Cerrar el archivo CSV
    fclose(csv_file);

    // Calcular desviación estándar de los tiempos
    double keygen_stddev = stddev(keygen_times, NUM_ITERATIONS);
    double sign_stddev = stddev(sign_times, NUM_ITERATIONS);
    double verify_stddev = stddev(verify_times, NUM_ITERATIONS);

    // Mostrar los resultados en consola
    printf("NAME: %s\n", CRYPTO_ALGNAME);
    printf("Key Generation Time: %.4f ms (+-%.4f ms)\n", 
           keygen_times[NUM_ITERATIONS - 1], keygen_stddev);
    printf("Signature Time: %.4f ms (+-%.4f ms)\n", 
           sign_times[NUM_ITERATIONS - 1], sign_stddev);
    printf("Verification Time: %.4f ms (+-%.4f ms)\n", 
           verify_times[NUM_ITERATIONS - 1], verify_stddev);

    return 0;
}
