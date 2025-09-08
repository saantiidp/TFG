import csv
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

paths = {
    "bike-128": Path("BIKE_bike-128_iter.csv"),
    "bike-192": Path("BIKE_bike-192_iter.csv"),
    "bike-256": Path("BIKE_bike-256_iter.csv"),
}

def _looks_digits(s: str) -> bool:
    return s.isdigit()

def _to_float_robust(a: str, b: str = None):
    a = a.strip()
    if '.' in a:
        return float(a)
    if b is not None and _looks_digits(a) and _looks_digits(b):
        return float(a + "." + b)
    return float(a.replace(',', '.'))

def read_bike_csv_robust(path: Path) -> pd.DataFrame:
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.reader(f, delimiter=',')
        header = next(r, None)
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
                b = parts[i+1] if (i + 1) < len(parts) else None
                try:
                    if '.' in a:
                        val = float(a); i += 1
                    elif b is not None and _looks_digits(a) and _looks_digits(b):
                        val = _to_float_robust(a, b); i += 2
                    else:
                        val = _to_float_robust(a); i += 1
                except ValueError:
                    i += 1; continue
                nums.append(val)
            if len(nums) == 4:
                gen, enc, dec, tot = nums
                rows.append((it, ver, gen, enc, dec, tot))
    df = pd.DataFrame(rows, columns=[
        "Iteracion","Version",
        "Tiempo_Generacion_Claves","Tiempo_Encapsulacion",
        "Tiempo_Decapsulacion","Tiempo_Total"
    ])
    return df

dfs = {k: read_bike_csv_robust(p) for k, p in paths.items()}
labels = list(dfs.keys())
data = [dfs[k]["Tiempo_Total"].values for k in labels]

plt.figure(figsize=(7,5))
plt.boxplot(data, labels=labels, showfliers=False)
plt.title("Boxplot - Tiempo Total (BIKE)")
plt.ylabel("Tiempo (ms)")
plt.grid(True)
plt.tight_layout()
plt.savefig("boxplot_bike_total_parser_robusto.png")
print("✅ Gráfico guardado en boxplot_bike_total_parser_robusto.png")