import time
import statistics
import csv
import matplotlib.pyplot as plt
from Dilithium.default_parameters import Dilithium2, Dilithium3, Dilithium5 

def run_performance_tests(dilithium_instance, iterations):
    # Listas para almacenar los tiempos de cada iteración
    keygen_times = []
    sign_small_times = []
    sign_large_times = []
    verify_small_times = []
    verify_large_times = []

    small_message = b"Your message signed by Dilithium"  # Mensaje pequeño
    large_message = b"A" * 1000  # Mensaje grande de 1,000 bytes (aproximadamente 10 KB)

    for _ in range(iterations):
        # Medir el tiempo de generación de claves
        start_time = time.time()
        pk, sk = dilithium_instance.keygen()
        keygen_times.append(time.time() - start_time)

        # Medir el tiempo de firma para el mensaje pequeño
        start_time = time.time()
        sig_small = dilithium_instance.sign(sk, small_message)
        sign_small_times.append(time.time() - start_time)

        # Medir el tiempo de firma para el mensaje grande
        start_time = time.time()
        sig_large = dilithium_instance.sign(sk, large_message)
        sign_large_times.append(time.time() - start_time)

        # Medir el tiempo de verificación para el mensaje pequeño
        start_time = time.time()
        dilithium_instance.verify(pk, small_message, sig_small)
        verify_small_times.append(time.time() - start_time)

        # Medir el tiempo de verificación para el mensaje grande
        start_time = time.time()
        dilithium_instance.verify(pk, large_message, sig_large)
        verify_large_times.append(time.time() - start_time)

    # Resultados detallados por operación
    results = {
        "keygen": keygen_times,
        "sign_small": sign_small_times,
        "sign_large": sign_large_times,
        "verify_small": verify_small_times,
        "verify_large": verify_large_times,
    }

    print(f"\nResultados para {dilithium_instance.__class__.__name__}:")
    for key, times in results.items():
        avg_time = sum(times) / iterations * 1000
        std_dev = statistics.stdev(times) * 1000
        print(f"{key.replace('_', ' ').capitalize()}:")
        print(f"  Tiempo promedio: {avg_time:.6f} ms")
        print(f"  Desviación estándar: {std_dev:.6f} ms")

    return results

def main():
    iterations = 1000  # Número de iteraciones para las pruebas de rendimiento
    versions = [Dilithium2, Dilithium3, Dilithium5] 
    all_results = []
    labels = []

    # Archivo CSV para almacenar resultados
    csv_filename = "dilithium_performance.csv"
    with open(csv_filename, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            "Version", "Message Type", "Iteration", "Total Time (ms)"
        ])

        j = 0
        # Ejecutar pruebas para cada versión de Dilithium
        for version in versions:
            if j == 3:
                j = 5
            elif j ==2:
                j = 3
            elif j == 0:
                j = 2
            #print ("vALOR I: ", j)        
            dilithium_instance = version  # Crear una instancia de la clase
            print(f"\nEjecutando pruebas para {dilithium_instance.__class__.__name__}{j} ")
            detailed_results = run_performance_tests(dilithium_instance, iterations)

            # Calcular tiempos totales para mensaje corto y largo
            total_times_short = [
                (keygen + sign_small + verify_small) * 1000
                for keygen, sign_small, verify_small in zip(
                    detailed_results["keygen"],
                    detailed_results["sign_small"],
                    detailed_results["verify_small"]
                )
            ]
            total_times_long = [
                (keygen + sign_large + verify_large) * 1000
                for keygen, sign_large, verify_large in zip(
                    detailed_results["keygen"],
                    detailed_results["sign_large"],
                    detailed_results["verify_large"]
                )
            ]

            # Agregar resultados a las listas para las gráficas
            all_results.extend([total_times_short, total_times_long])
            labels.extend([
                f"{dilithium_instance.__class__.__name__}{j} - Mensaje Corto",
                f"{dilithium_instance.__class__.__name__}{j} - Mensaje Largo"
            ])

            # Escribir resultados en el CSV
            for i in range(iterations):
                print("File csv ", i)
                csv_writer.writerow([
                    dilithium_instance.__class__.__name__, "Mensaje Corto", i + 1, total_times_short[i]
                ])
                csv_writer.writerow([
                    dilithium_instance.__class__.__name__, "Mensaje largo", i + 1, total_times_long[i]
                ])

    # Generar gráfico de caja y bigotes
    plt.figure(figsize=(14, 8))
    plt.boxplot(all_results, labels=labels, showmeans=True)
    plt.title("Comparación de Tiempos Totales para Dilithium")
    plt.ylabel("Tiempo Total (ms)")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("dilithium_total_performance_boxplot.png")
    plt.show()

if __name__ == "__main__":
    main()