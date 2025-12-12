#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include "api.h"
#include <math.h> // Para usar sqrt() y operaciones matemáticas

// Assembler CNTVCT_EL0 Function to Measure Clock Cycles on ARM
static inline uint64_t read_cntvct(void) {
    uint64_t cnt;
    asm volatile("mrs %0, cntvct_el0" : "=r" (cnt));
    return cnt;
}

// Para obtener la frecuencia del contador
static inline uint64_t read_cntfrq(void) {
    uint64_t freq;
    asm volatile("mrs %0, cntfrq_el0" : "=r" (freq));
    return freq;
}

int main() {
    unsigned char       *m = "lasquinceletrasmascuarentaycuatroletrascincuentaynuevebytes"; // 59 Bytes Message like SUPERCOP Project 
    unsigned char       *m1 = NULL, *sm = NULL;
    unsigned long long  mlen = 0, mlen1 = 0, smlen = 0;
    unsigned char       pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES];
    uint64_t            tmp1 = 0, tmp2 = 0, tiempo1 = 0, tiempo2 = 0, tiempo3 = 0, tiempo4 = 0, tiempoKeyGen1 = 0, tiempoKeyGen2 = 0;
    double              tiempos = 0, tiempov = 0, tiempokeygen = 0;
    long long int       ciclosign = 0, cicloverify = 0, ciclokeygen = 0;
    double              sumsq_sign = 0, sumsq_verify = 0, sumsq_keygen = 0;
    double              std_sign = 0, std_verify = 0, std_keygen = 0;
    int                 ret_valg = -9, ret_vals = -9, ret_valv = -9; 
    
    uint64_t freq = read_cntfrq(); // Leer frecuencia del contador

    m = (unsigned char *) calloc(mlen, sizeof(unsigned char));
    m1 = (unsigned char *) calloc(mlen+CRYPTO_BYTES, sizeof(unsigned char));
    sm = (unsigned char *) calloc(mlen+CRYPTO_BYTES, sizeof(unsigned char));

    // Abrir el archivo CSV para guardar los resultados
    FILE *file = fopen("falcon1024.csv", "w");
    if (file == NULL) {
        perror("No se pudo abrir el archivo para escribir");
        return 1;
    }

    // Escribir los encabezados del CSV
    fprintf(file, "Iteración,KeyGen (Ciclos),KeyGen (ms),Sign (Ciclos),Sign (ms),Verify (Ciclos),Verify (ms),Tiempo Total (ms)\n");

    // CPU Warming Block
    for (int i = 0; i < 1000000000; i++) {
        int a = rand(), b = rand(); 
        double c = 0, d = 0, e = 0;
        c = a * b;
        d = c / i;
        e = a ^ b;
    }

    for (int i = 0; i < 1000; i++) {
        // Keypair Generation Timing Block
        tiempoKeyGen1 = read_cntvct();
        ret_valg = crypto_sign_keypair(pk, sk);  
        tiempoKeyGen2 = read_cntvct();
        ciclokeygen += tiempoKeyGen2 - tiempoKeyGen1;

        // Promedio dinámico de KeyGen
        double avg_keygen = (double)ciclokeygen / (i + 1);

        // Sign Block
        tiempo1 = read_cntvct();
        ret_vals = crypto_sign(sm, &smlen, m, mlen, sk);
        tiempo2 = read_cntvct();
        ciclosign += tiempo2 - tiempo1;

        // Promedio dinámico de Sign
        double avg_sign = (double)ciclosign / (i + 1);

        // Verify Block
        tiempo3 = read_cntvct();
        ret_valv = crypto_sign_open(m1, &mlen1, sm, smlen, pk);
        tiempo4 = read_cntvct();
        cicloverify += tiempo4 - tiempo3;

        // Promedio dinámico de Verify
        double avg_verify = (double)cicloverify / (i + 1);

        // Sumar los cuadrados de las diferencias para la desviación estándar
        sumsq_sign += (tiempo2 - tiempo1 - avg_sign) * (tiempo2 - tiempo1 - avg_sign);
        sumsq_verify += (tiempo4 - tiempo3 - avg_verify) * (tiempo4 - tiempo3 - avg_verify);
        sumsq_keygen += (tiempoKeyGen2 - tiempoKeyGen1 - avg_keygen) * (tiempoKeyGen2 - tiempoKeyGen1 - avg_keygen);

        // Escribir los datos de la iteración en el archivo CSV
        double tiempo_keygen_ms = (double)(tiempoKeyGen2 - tiempoKeyGen1) / freq * 1000;
        double tiempo_sign_ms = (double)(tiempo2 - tiempo1) / freq * 1000;
        double tiempo_verify_ms = (double)(tiempo4 - tiempo3) / freq * 1000;
        double tiempo_total_ms = tiempo_keygen_ms + tiempo_sign_ms + tiempo_verify_ms;

        fprintf(file, "%d,%lld,%f,%lld,%f,%lld,%f,%f\n", 
                i + 1, 
                tiempoKeyGen2 - tiempoKeyGen1, tiempo_keygen_ms, 
                tiempo2 - tiempo1, tiempo_sign_ms, 
                tiempo4 - tiempo3, tiempo_verify_ms, 
                tiempo_total_ms);
    }

    // Calcular desviaciones estándar finales
    std_sign = sqrt(sumsq_sign / 1000);
    std_verify = sqrt(sumsq_verify / 1000);
    std_keygen = sqrt(sumsq_keygen / 1000);

    // Imprimir resultados
    printf("FALCON: ref-1024 sk-2305-bytes pk-1793-bytes\n"); 
    printf("Key Generation Clock Cycles: %lld\n", ciclokeygen / 1000);
    printf("Key Generation Time ms: %f\n", (double)ciclokeygen / freq / 1000 * 1000);
    printf("Key Generation Standard Deviation ms: %f\n", std_keygen * 1000 / freq);
    printf("Sign Clock Cycles: %lld\n", ciclosign / 1000);
    printf("Sign Time ms: %f\n", (double)ciclosign / freq / 1000 * 1000);
    printf("Sign Time Standard Deviation ms: %f\n", std_sign * 1000 / freq);
    printf("Verify Clock Cycles: %lld\n", cicloverify / 1000);
    printf("Verify Time ms: %f\n", (double)cicloverify / freq / 1000 * 1000);
    printf("Verify Time Standard Deviation ms: %f\n", std_verify * 1000 / freq);

    fclose(file);
    free(m);
    free(m1);
    free(sm);
    return 0;
}
