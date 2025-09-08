import pandas as pd
import matplotlib.pyplot as plt
import glob
from pathlib import Path

# Archivo CSV generado por tu script de rendimiento
CSV_IN = "mceliece_rendimiento.csv"

# Orden de variantes (si faltan algunas, se muestran solo las presentes)
ORDER = [
    "Classic-McEliece-348864",  "Classic-McEliece-348864f",
    "Classic-McEliece-460896",  "Classic-McEliece-460896f",
    "Classic-McEliece-6688128", "Classic-McEliece-6688128f",
    "Classic-McEliece-6960119", "Classic-McEliece-6960119f",
    "Classic-McEliece-8192128", "Classic-McEliece-8192128f",
]

# Columnas a graficar
METRICS = [
    ("Tiempo_Generacion_Claves", "KeyGen (ms)"),
    ("Tiempo_Encapsulacion", "Encaps (ms)"),
    ("Tiempo_Decapsulacion", "Decaps (ms)"),
    ("Tiempo_Total", "Total (ms)"),
]

def main():
    df = pd.read_csv(CSV_IN)

    present_algs = df["Algoritmo"].unique().tolist()
    # Mantener el orden definido arriba
    order_idx = {name: i for i, name in enumerate(ORDER)}
    present_sorted = sorted(present_algs, key=lambda a: order_idx.get(a, 999))

    for col, ylabel in METRICS:
        data, labels = [], []
        for alg in present_sorted:
            vals = pd.to_numeric(df.loc[df["Algoritmo"] == alg, col], errors="coerce").dropna()
            if len(vals) == 0:
                continue
            data.append(vals)
            labels.append(alg)

        if not data:
            print(f"[AVISO] Sin datos para {col}")
            continue

        plt.figure(figsize=(11, 6))
        plt.boxplot(data, labels=labels, patch_artist=True)
        plt.title(f"Classic McEliece - {ylabel}")
        plt.ylabel(ylabel)
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        out_png = f"mceliece_boxplot_{col}.png"
        plt.savefig(out_png, dpi=120)
        plt.close()
        print(f"✅ Guardado: {out_png}")

if __name__ == "__main__":
    main()
