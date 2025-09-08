import pandas as pd
import matplotlib.pyplot as plt

# Leer el CSV
df = pd.read_csv("bike_rendimiento.csv")

# Crear boxplot con escala logarítmica
plt.figure(figsize=(6, 5))
plt.boxplot(
    [df["Keygen Time (ms)"], df["Enc Time (ms)"], df["Dec Time (ms)"]],
    labels=["KeyGen", "Encaps", "Decaps"]
)

plt.yscale("log")
plt.title("Rendimiento BIKE (en milisegundos)")
plt.ylabel("Tiempo [ms] (escala logarítmica)")
plt.grid(True, axis='y', which='both', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("bike_rendimiento_log.png", dpi=300)
# plt.show()  # Descomenta si deseas visualizar en pantalla
