#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include "kem.h"
#include "randombytes.h"

#define NTESTS 1000
#define VERSION_STR(x) ((x) == 2 ? "Kyber512" : (x) == 3 ? "Kyber768" : "Kyber1024")

int main(void)
{
  unsigned int i;

  // Arreglos para almacenar los tiempos individuales
  double times_keygen[NTESTS];
  double times_enc[NTESTS];
  double times_dec[NTESTS];
  double times_total[NTESTS];

  char filename[256];
  snprintf(filename, sizeof(filename), "%s_REF_results.csv", VERSION_STR(KYBER_K));

  // Archivo para escribir los resultados
  FILE *csv_file = fopen(filename, "w");
  if (csv_file == NULL) {
    perror("Error al abrir el archivo CSV");
    return 1;
  }
  fprintf(csv_file, "Iteración,Tiempo Keygen (ms),Tiempo Encapsulación (ms),Tiempo Decapsulación (ms),Tiempo Total (ms)\n");

  // Variables para acumulación de tiempos totales
  double total_time_keygen = 0;
  double total_time_enc = 0;
  double total_time_dec = 0;
  double total_time_total = 0;

  for (i = 0; i < NTESTS; i++) {
    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];
    uint8_t ct[CRYPTO_CIPHERTEXTBYTES];
    uint8_t key_a[CRYPTO_BYTES];
    uint8_t key_b[CRYPTO_BYTES];

    // Variables de tiempo para cada operación
    clock_t start, end;
    double time_keygen, time_enc, time_dec, time_total;

    // Medir tiempo de generación de claves
    start = clock();
    crypto_kem_keypair(pk, sk);
    end = clock();
    time_keygen = ((double)(end - start)) / CLOCKS_PER_SEC * 1000; // Convertir a ms
    times_keygen[i] = time_keygen;
    total_time_keygen += time_keygen;

    // Medir tiempo de encapsulamiento
    start = clock();
    crypto_kem_enc(ct, key_b, pk);
    end = clock();
    time_enc = ((double)(end - start)) / CLOCKS_PER_SEC * 1000; // Convertir a ms
    times_enc[i] = time_enc;
    total_time_enc += time_enc;

    // Medir tiempo de decapsulamiento
    start = clock();
    crypto_kem_dec(key_a, ct, sk);
    end = clock();
    time_dec = ((double)(end - start)) / CLOCKS_PER_SEC * 1000; // Convertir a ms
    times_dec[i] = time_dec;
    total_time_dec += time_dec;

    // Verificar si las claves coinciden
    if (memcmp(key_a, key_b, CRYPTO_BYTES)) {
      printf("ERROR keys\n");
      fclose(csv_file);
      return 1;
    }

   // Calcular el tiempo total de la iteración
   time_total = time_keygen + time_enc + time_dec;
   times_total[i] = time_total;
   total_time_total += time_total;

    // Escribir los tiempos en el archivo CSV
    fprintf(csv_file, "%u,%.3f,%.3f,%.3f,%.3f\n", i + 1, time_keygen, time_enc, time_dec, time_total);
  }

  // Calcular los promedios
  double avg_time_keygen = total_time_keygen / NTESTS;
  double avg_time_enc = total_time_enc / NTESTS;
  double avg_time_dec = total_time_dec / NTESTS;
  double avg_time_total = total_time_total / NTESTS;

  // Calcular las desviaciones estándar
  double sum_sq_diff_keygen = 0, sum_sq_diff_enc = 0, sum_sq_diff_dec = 0, sum_sq_diff_total = 0;

  for (i = 0; i < NTESTS; i++) {
    sum_sq_diff_keygen += (times_keygen[i] - avg_time_keygen) * (times_keygen[i] - avg_time_keygen);
    sum_sq_diff_enc += (times_enc[i] - avg_time_enc) * (times_enc[i] - avg_time_enc);
    sum_sq_diff_dec += (times_dec[i] - avg_time_dec) * (times_dec[i] - avg_time_dec);
    sum_sq_diff_total += (times_total[i] - avg_time_total) * (times_total[i] - avg_time_total);
  }

  double std_dev_keygen = sqrt(sum_sq_diff_keygen / NTESTS);
  double std_dev_enc = sqrt(sum_sq_diff_enc / NTESTS);
  double std_dev_dec = sqrt(sum_sq_diff_dec / NTESTS);
  double std_dev_total = sqrt(sum_sq_diff_total / NTESTS);

  // Imprimir los tiempos promedio y desviaciones estándar
  printf("Tiempo promedio de generación de claves: %.4f ms (+-%.4f ms(σ))\n", avg_time_keygen, std_dev_keygen);
  printf("Tiempo promedio de encapsulamiento: %.4f ms (+-%.4f ms)\n", avg_time_enc, std_dev_enc);
  printf("Tiempo promedio de decapsulamiento: %.4f ms (+-%.4f ms)\n", avg_time_dec, std_dev_dec);
  printf("Tiempo total promedio por iteración: %.4f ms (+-%.4f ms)\n", avg_time_total, std_dev_total);

  // Información de tamaño de claves
  printf("CRYPTO_SECRETKEYBYTES:  %d\n", CRYPTO_SECRETKEYBYTES);
  printf("CRYPTO_PUBLICKEYBYTES:  %d\n", CRYPTO_PUBLICKEYBYTES);
  printf("CRYPTO_CIPHERTEXTBYTES: %d\n", CRYPTO_CIPHERTEXTBYTES);

  // Cerrar el archivo CSV
  fclose(csv_file);
  printf("Resultados escritos en '%s'.\n", filename);

  return 0;
}
