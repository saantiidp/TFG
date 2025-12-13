#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include "api.h"
#include <math.h>  // Para usar sqrt() y operaciones matemáticas

// Assembler rdtsc Function to Measure Clock Cycles
static inline uint64_t rdtsc(void)
{
    unsigned int eax, edx;
    asm volatile("rdtsc" : "=a" (eax), "=d" (edx));
    return ((uint64_t) edx << 32) | eax;
}

int main()
{
    unsigned char       *m = "lasquinceletrasmascuarentaycuatroletrascincuentaynuevebytes";
    unsigned char       *m1 = NULL, *sm = NULL;
    unsigned long long  mlen = 0, mlen1 = 0, smlen = 0;
    unsigned char       pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES];
    uint64_t            tmp1 = 0, tmp2 = 0, tiempo1 = 0, tiempo2 = 0, tiempo3 = 0, tiempo4 = 0, tiempoKeyGen1 = 0, tiempoKeyGen2 = 0;
    double              tiempos = 0, tiempov = 0, tiempokeygen = 0;
    long long int       ciclosign = 0, cicloverify = 0, ciclokeygen = 0;
    long long int       totalsign = 0, totalverify = 0, totalkeygen = 0;
    double              sumsq_sign = 0, sumsq_verify = 0, sumsq_keygen = 0;  // Para almacenar la suma de los cuadrados de las diferencias
    double              std_sign = 0, std_verify = 0, std_keygen = 0;  // Para la desviación estándar
    int                 ret_valg = -9, ret_vals = -9, ret_valv = -9; 
    
    m = (unsigned char *) calloc(mlen, sizeof(unsigned char));
    m1 = (unsigned char *) calloc(mlen+CRYPTO_BYTES, sizeof(unsigned char));
    sm = (unsigned char *) calloc(mlen+CRYPTO_BYTES, sizeof(unsigned char));

    // Abrir el archivo CSV para guardar los resultados
    FILE *file = fopen("falcon1024.csv", "w");
    if (file == NULL)
    {
        perror("No se pudo abrir el archivo para escribir");
        return 1;
    }

    // Escribir los encabezados del CSV
    fprintf(file, "Iteración,KeyGen (Ciclos),KeyGen (ms),Sign (Ciclos),Sign (ms),Verify (Ciclos),Verify (ms),Tiempo Total (ms)\n");

    // CPU Warming Block
    for (int i = 0; i < 1000000000; i++)
    {
        int a = rand(), b = rand(); 
        double c = 0, d = 0, e = 0;
        c = a * b;
        d = c / i;
        e = a ^ b;
    }

    for (int i = 0; i < 1000; i++)
    {
        // Keypair Generation Timing Block - Ahora se realiza en cada iteración
        tiempoKeyGen1 = rdtsc();
        ret_valg = crypto_sign_keypair(pk, sk);  
        tiempoKeyGen2 = rdtsc();
        ciclokeygen = tiempoKeyGen2 - tiempoKeyGen1;
        
        // Sign Block
        tiempo1 = rdtsc();
        // START MEASURING
        ret_vals = crypto_sign(sm, &smlen, m, mlen, sk);
        //printf("crypto_sign status: <%d>\n", ret_vals);
        // END MEASURING
        tiempo2 = rdtsc();

        // Verify Block
        tiempo3 = rdtsc();
        // START MEASURING
        ret_valv = crypto_sign_open(m1, &mlen1, sm, smlen, pk);
        //printf("crypto_sign_open status: <%d>\n", ret_valv);
        // END MEASURING
        tiempo4 = rdtsc();

        tmp1 = tiempo2 - tiempo1;
        tmp2 = tiempo4 - tiempo3;
        ciclosign = ciclosign + tmp1;
        cicloverify = cicloverify + tmp2;

        // Sumar los cuadrados de las diferencias para la desviación estándar
        sumsq_sign += (tmp1 - (double)totalsign) * (tmp1 - (double)totalsign);
        sumsq_verify += (tmp2 - (double)totalverify) * (tmp2 - (double)totalverify);
        sumsq_keygen += (ciclokeygen - (double)totalkeygen) * (ciclokeygen - (double)totalkeygen);

        // Escribir los datos de la iteración en el archivo CSV
        double tiempo_keygen_ms = (double)ciclokeygen / 1895000000 * 1000;  // Convertir a milisegundos
        double tiempo_sign_ms = (double)tmp1 / 1895000000 * 1000;
        double tiempo_verify_ms = (double)tmp2 / 1895000000 * 1000;
        double tiempo_total_ms = tiempo_keygen_ms + tiempo_sign_ms + tiempo_verify_ms;

        // Escribir los resultados de la iteración
        fprintf(file, "%d,%lld,%f,%lld,%f,%lld,%f,%f\n", 
                i+1, 
                ciclokeygen, tiempo_keygen_ms, 
                tmp1, tiempo_sign_ms, 
                tmp2, tiempo_verify_ms, 
                tiempo_total_ms);
    }

    totalsign = ciclosign / 1000;
    totalverify = cicloverify / 1000;
    totalkeygen = ciclokeygen; // La generación de claves ocurre en cada iteración, por lo que no la dividimos
    tiempos = (double) totalsign / 1895000000; // clock cycles of the testing CPU
    tiempov = (double) totalverify / 1895000000; // clock cycles of the testing CPU
    tiempokeygen = (double) totalkeygen / 1895000000; // clock cycles of the testing CPU
    
    // Calcular la desviación estándar de la firma, verificación y generación de claves
    std_sign = sqrt(sumsq_sign / 1000);
    std_verify = sqrt(sumsq_verify / 1000);
    std_keygen = sqrt(sumsq_keygen / 1000);  // En este caso, se calcularía también para la generación de claves.

    printf("FALCON: ref-1024 sk-2305-bytes pk-1793-bytes\n"); 
    printf("Key Generation Clock Cycles: %llu\n", totalkeygen);
    printf("Key Generation Time ms: %f\n", tiempokeygen*1000); // Time in milliseconds for key generation
    printf("Key Generation Standard Deviation ms: %f\n", std_keygen * 1000 / 1895000000);  // Desviación estándar de la generación de claves
    printf("Sign Clock Cycles: %llu\n", totalsign);
    printf("Sign Time ms: %f\n", tiempos*1000);
    printf("Sign Time Standard Deviation ms: %f\n", std_sign * 1000 / 1895000000); // Desviación estándar de la firma
    printf("Verify Clock Cycles: %llu\n", totalverify);
    printf("Verify Time ms: %f\n", tiempov*1000);
    printf("Verify Time Standard Deviation ms: %f\n", std_verify * 1000 / 1895000000); // Desviación estándar de la verificación

    fclose(file);  // Cerrar el archivo después de escribir los resultados

    free(m);
    free(m1);
    free(sm);
    return 0;
}


