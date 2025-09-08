import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Leer CSV
df = pd.read_csv("bike_rendimiento.csv")

operaciones = ["Keygen Time (ms)", "Enc Time (ms)", "Dec Time (ms)", "Total Time (ms)"]
versiones = df["Algoritmo"].unique()

# Paleta de colores
colores = {
    "BIKE-L1": "skyblue",
    "BIKE-L3": "orange",
    "BIKE-L5": "lightgreen"
}

fig, ax = plt.subplots(figsize=(12, 6))

posiciones = []
datos = []
colores_box = []

sep = len(versiones) + 1  # separación entre grupos

for idx_op, op in enumerate(operaciones):
    start = idx_op * sep + 1
    for idx_ver, ver in enumerate(versiones):
        subset = df[df["Algoritmo"] == ver][op]
        posiciones.append(start + idx_ver)
        datos.append(subset)
        colores_box.append(colores[ver])

# Dibujar boxplots con colores
bp = ax.boxplot(datos, positions=posiciones, widths=0.6, patch_artist=True, showmeans=True)

for patch, color in zip(bp["boxes"], colores_box):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

ax.set_xticks([i * sep + 1 + (len(versiones) - 1) / 2 for i in range(len(operaciones))])
ax.set_xticklabels(["Keygen", "Encaps", "Decaps", "Total"])
ax.set_ylabel("Tiempo (ms)")
ax.set_title("BIKE - Comparación por operación")
ax.grid(axis='y')

# Leyenda
handles = [plt.Line2D([0], [0], color=colores[v], lw=4, label=v) for v in versiones]
ax.legend(handles=handles, title="Versión", loc="upper left")

plt.tight_layout()
plt.savefig("bike_boxplot_por_operacion_colores.png", dpi=150)
plt.show()
