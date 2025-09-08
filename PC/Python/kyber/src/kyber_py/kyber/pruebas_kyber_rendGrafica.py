import time
import csv
import matplotlib.pyplot as plt
from default_parameters import Kyber512, Kyber768, Kyber1024
import numpy as np

def run_performance_tests(kyber_instance, iterations):
    # Listas para almacenar los tiempos individuales
    keygen_times = []
    encaps_times = []
    decaps_times = []

    for _ in range(iterations):
        # Medir el tiempo de generación de claves
        start_time = time.time()
        pk, sk = kyber_instance.keygen()
        keygen_times.append(time.time() - start_time)

        # Medir el tiempo de encapsulación
        start_time = time.time()
        K, c = kyber_instance.encaps(pk)
        encaps_times.append(time.time() - start_time)

        # Medir el tiempo de decapsulación
        start_time = time.time()
        shared_key = kyber_instance.decaps(sk, c)
        decaps_times.append(time.time() - start_time)

    # Calcular promedios y desviaciones estándar
    avg_keygen = np.mean(keygen_times) * 1000  # ms
    avg_encaps = np.mean(encaps_times) * 1000  # ms
    avg_decaps = np.mean(decaps_times) * 1000  # ms

    std_keygen = np.std(keygen_times) * 1000  # ms
    std_encaps = np.std(encaps_times) * 1000  # ms
    std_decaps = np.std(decaps_times) * 1000  # ms

    # Tiempo total por iteración
    total_times = [(kg + ec + dc) * 1000 for kg, ec, dc in zip(keygen_times, encaps_times, decaps_times)]

    print(f"\nResultados para {kyber_instance.__class__.__name__}:")
    print(f"Tiempo promedio de generación de claves: {avg_keygen:.4f} ms (+-{std_keygen:.4f})")
    print(f"Tiempo promedio de encapsulación: {avg_encaps:.4f} ms (+-{std_encaps:.4f})")
    print(f"Tiempo promedio de decapsulación: {avg_decaps:.4f} ms (+-{std_decaps:.4f})")

    return avg_keygen, std_keygen, avg_encaps, std_encaps, avg_decaps, std_decaps, total_times

def main():
    iterations = 1000  # Número de iteraciones para las pruebas de rendimiento
    kyber_versions = [Kyber512, Kyber768, Kyber1024]
    version_labels = ["Kyber512", "Kyber768", "Kyber1024"]
    all_total_times = []  # Para los gráficos
    csv_data = []  # Para el archivo CSV
    means = []  # Lista para almacenar los promedios de tiempos totales


    for version, label in zip(kyber_versions, version_labels):
        print(f"\nEjecutando pruebas para {label}...")
        avg_keygen, std_keygen, avg_encaps, std_encaps, avg_decaps, std_decaps, total_times = run_performance_tests(version, iterations)

        # Agregar datos para el CSV
        csv_data.append([
            label,
            f"{avg_keygen:.4f} (+/- {std_keygen:.4f})",
            f"{avg_encaps:.4f} (+/- {std_encaps:.4f})",
            f"{avg_decaps:.4f} (+/- {std_decaps:.4f})"
        ])

        # Guardar tiempos totales para el gráfico
        all_total_times.append(total_times)

        # Calcular y almacenar la media de los tiempos totales
        means.append(np.mean(total_times))

    # Exportar los datos a un archivo CSV
    with open("kyber_performance_summary.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Versión", "Tiempo Generación Claves (+/- Desviación)", "Tiempo Encapsulación (+/- Desviación)", "Tiempo Decapsulación (+/- Desviación)"])
        writer.writerows(csv_data)

    # Generar gráfico de diagramas de cajas para tiempos totales
    plt.figure(figsize=(10, 6))
    box = plt.boxplot(all_total_times, labels=version_labels, patch_artist=True)
    # Superponer los valores promedio como triángulos verdes
    for i, mean in enumerate(means, start=1):  # `start=1` porque los gráficos de cajas indexan desde 1
        plt.scatter(i, mean, color='green', marker='^', s=100, label="Media" if i == 1 else "")  # Añadir etiqueta solo una vez

    plt.title("Tiempo total del algoritmo por versión")
    plt.ylabel("Tiempo total (ms)")
    plt.xlabel("Versión de Kyber")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig("kyber_total_times_boxplot.png")
    plt.show()

if __name__ == "__main__":
    main()