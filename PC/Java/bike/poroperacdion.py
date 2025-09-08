# bike_boxplots_ops_parser_robusto.py
import csv
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- Config ---
paths = {
    "bike-128": Path("BIKE_bike-128_iter.csv"),
    "bike-192": Path("BIKE_bike-192_iter.csv"),
    "bike-256": Path("BIKE_bike-256_iter.csv"),
}
columnas = [
    ("Tiempo_Generacion_Claves", "Tiempo_Generacion_Claves"),
    ("Tiempo_Encapsulacion", "Tiempo_Encapsulacion"),
    ("Tiempo_Decapsulacion", "Tiempo_Decapsulacion"),
    # Descomenta si también quieres el total:
    # ("Tiempo_Total", "Tiempo_Total"),
]

# --- Parser robusto (maneja números partidos por comas y decimales con '.') ---
def _looks_digits(s: str) -> bool:
    return s.isdigit()

def _to_float_robust(a: str, b: str = None):
    a = a.strip()
    if "." in a:
        return float(a)
    if b is not None and _looks_digits(a) and _looks_digits(b):
        return float(a + "." + b)
    return float(a.replace(",", "."))

def read_bike_csv_robust(path: Path) -> pd.DataFrame:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f, delimiter=",")
        _ = next(r, None)  # header
        for parts in r:
            if not parts:
                continue
            parts = [p.strip() for p in parts]
            it = int(parts[0])
            ver = parts[1]
            nums = []
            i = 2
            while i < len(parts) and len(nums) < 4:
                a = parts[i]
                b = parts[i + 1] if (i + 1) < len(parts) else None
                try:
                    if "." in a:
                        val = float(a); i += 1
                    elif b is not None and _looks_digits(a) and _looks_digits(b):
                        val = _to_float_robust(a, b); i += 2
                    else:
                        val = _to_float_robust(a); i += 1
                except ValueError:
                    i += 1
                    continue
                nums.append(val)
            if len(nums) == 4:
                gen, enc, dec, tot = nums
                rows.append((it, ver, gen, enc, dec, tot))
    return pd.DataFrame(
        rows,
        columns=[
            "Iteracion",
            "Version",
            "Tiempo_Generacion_Claves",
            "Tiempo_Encapsulacion",
            "Tiempo_Decapsulacion",
            "Tiempo_Total",
        ],
    )

# --- Carga y gráficos ---
dfs = {k: read_bike_csv_robust(p) for k, p in paths.items()}

def boxplot_por_col(col: str, titulo: str):
    etiquetas = list(dfs.keys())
    datos = [dfs[k][col].values for k in etiquetas]
    plt.figure(figsize=(7,5))
    plt.boxplot(datos, labels=etiquetas, showfliers=False)
    plt.title(f"Boxplot - {titulo}")
    plt.ylabel("Tiempo (ms)")
    plt.grid(True)
    plt.tight_layout()
    out = f"boxplot_{col}.png"
    plt.savefig(out)
    plt.close()
    print(f"✅ Guardado {out}")

for col, titulo in columnas:
    boxplot_por_col(col, titulo)

# (Opcional) imprimir estadísticas rápidas en consola
for nombre, df in dfs.items():
    print(f"\n[{nombre}]")
    for col, _ in columnas:
        s = df[col]
        print(
            f"  {col}: n={len(s)}, min={s.min():.3f}, p10={s.quantile(0.10):.3f}, "
            f"mediana={s.median():.3f}, p90={s.quantile(0.90):.3f}, max={s.max():.3f}"
        )
