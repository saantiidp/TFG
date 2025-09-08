import pandas as pd
import matplotlib.pyplot as plt
import os

# Asociar archivo y nombre de versión
archivos = {
    "falcon512.csv": "falcon512",
    "falcon512avx2.csv": "falcon512avx2",
    "falcon1024.csv": "falcon1024",
    "falcon1024avx2.csv": "falcon1024avx2"
}

# Leer y validar los archivos
dataframes = []
for archivo, version in archivos.items():
    if not os.path.exists(archivo) or os.path.getsize(archivo) == 0:
        print(f"[!] Archivo no encontrado o vacío: {archivo}")
        continue
    try:
        df = pd.read_csv(archivo, skiprows=11, header=None)
        if df.shape[1] < 8:
            print(f"[!] Archivo {archivo} tiene solo {df.shape[1]} columnas.")
            continue
        df["Versión"] = version
        df.columns = [
            "Iteración",
            "Keygen Cycles", "Keygen ms",
            "Sign Cycles", "Sign ms",
            "Verify Cycles", "Verify ms",
            "Total ms",
            "Versión"
        ]
        dataframes.append(df)
    except Exception as e:
        print(f"[!] Error leyendo {archivo}: {e}")

# Unir todos los DataFrames válidos
if not dataframes:
    print("❌ No se pudo cargar ningún archivo válido.")
    exit(1)

df_all = pd.concat(dataframes, ignore_index=True)

# Crear el boxplot del tiempo total
plt.figure(figsize=(12, 6))
orden = [df["Versión"].iloc[0] for df in dataframes]
plt.boxplot(
    [df_all[df_all["Versión"] == v]["Total ms"] for v in orden],
    labels=orden
)
plt.title("Comparación de tiempos totales de ejecución (ms) entre versiones de Falcon")
plt.xlabel("Versión de Falcon")
plt.ylabel("Tiempo total (ms)")
plt.grid(True)
plt.tight_layout()
plt.savefig("falcon_boxplot.png")
plt.show()
