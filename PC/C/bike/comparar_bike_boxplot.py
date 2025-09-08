import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar CSVs
ref = pd.read_csv("bike_rendimiento.csv")
avx2 = pd.read_csv("bike_avx2_rendimiento.csv")

# Añadir columna de versión
ref["Version"] = "Reference"
avx2["Version"] = "AVX2"

# Unir y renombrar columna de tiempo total
ref = ref[["Total Time (ms)", "Version"]].rename(columns={"Total Time (ms)": "Tiempo (ms)"})
avx2 = avx2[["Total Time (ms)", "Version"]].rename(columns={"Total Time (ms)": "Tiempo (ms)"})

df_total = pd.concat([ref, avx2], ignore_index=True)

# Crear boxplot solo con tiempo total
plt.figure(figsize=(6, 6))
sns.boxplot(x="Version", y="Tiempo (ms)", data=df_total)

# Opción: ajustar escala logarítmica o eje Y manualmente
# plt.yscale("log")
# plt.ylim(0, 40)

plt.title("Comparación de Tiempo Total: Reference vs AVX2")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("comparacion_bike_total_boxplot.png")
plt.show()
