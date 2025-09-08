import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Archivos CSV esperados
csv_files = [
    "HQC_hqc-128_iter_iter.csv",
    "HQC_hqc-192_iter_iter.csv",
    "HQC_hqc-256_iter_iter.csv"
]

df_list = []

# Leer y combinar todos los CSV
for file in csv_files:
    if os.path.exists(file):
        df = pd.read_csv(file)
        df["Versión"] = df["Version"]
        df_list.append(df)

if df_list:
    df_all = pd.concat(df_list)

    # Crear gráfico con escala del eje Y ajustada
    plt.figure(figsize=(10, 5))
    sns.boxplot(x="Versión", y="Tiempo_Total", data=df_all)
    plt.ylim(0, 100)  # <-- AJUSTE CRUCIAL: reduce el límite superior del eje Y
    plt.title("Comparación de Tiempos Totales HQC por Versión")
    plt.xlabel("Versión HQC")
    plt.ylabel("Tiempo Total (ms)")
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.savefig("hqc_boxplot_scaled.png")
    plt.show()
else:
    print("❌ No se encontraron archivos CSV válidos para graficar.")
