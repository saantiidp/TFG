
import oqs
import time
import csv
import matplotlib.pyplot as plt

iterations = 100
algorithms = ["HQC-128", "HQC-256"]

# Guardar todos los resultados
resultados_totales = []
etiquetas = []

# Archivo CSV de salida
with open("hqc_rendimiento.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Algoritmo", "Iteración", "Keygen Time (ms)", "Enc Time (ms)", "Dec Time (ms)", "Total Time (ms)"])

    for alg in algorithms:
        print(f"Ejecutando pruebas para {alg}")
        keygen_times = []
        enc_times = []
        dec_times = []
        total_times = []

        for i in range(iterations):
            kem = oqs.KeyEncapsulation(alg)

            # Keygen
            t0 = time.time()
            public_key = kem.generate_keypair()
            t1 = time.time()
            keygen_time = (t1 - t0) * 1000

            # Encapsulate
            t0 = time.time()
            ciphertext, shared_secret_enc = kem.encap_secret(public_key)
            t1 = time.time()
            enc_time = (t1 - t0) * 1000

            # Decapsulate
            t0 = time.time()
            shared_secret_dec = kem.decap_secret(ciphertext)
            t1 = time.time()
            dec_time = (t1 - t0) * 1000

            total = keygen_time + enc_time + dec_time

            # Guardar en listas
            keygen_times.append(keygen_time)
            enc_times.append(enc_time)
            dec_times.append(dec_time)
            total_times.append(total)

            # Guardar en CSV
            writer.writerow([alg, i+1, f"{keygen_time:.4f}", f"{enc_time:.4f}", f"{dec_time:.4f}", f"{total:.4f}"])

        resultados_totales.append(total_times)
        etiquetas.append(f"{alg}")

# Graficar boxplot
plt.figure(figsize=(10, 6))
plt.boxplot(resultados_totales, labels=etiquetas, showmeans=True)
plt.title("Comparación de Tiempos Totales - HQC-128 vs HQC-256")
plt.ylabel("Tiempo Total (ms)")
plt.grid(axis='y')
plt.tight_layout()
plt.savefig("hqc_boxplot.png")
plt.show()
