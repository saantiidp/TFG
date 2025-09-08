#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

CSV_IN = "falcon_python_ops.csv"
PNG_OUT = "falcon_python_boxplot_total.png"

# Leer CSV
df = pd.read_csv(CSV_IN)

# Nos aseguramos de que la columna existe
if "Total(ms)" not in df.columns:
    raise ValueError(f"El CSV {CSV_IN} no tiene columna 'Total(ms)'. Columnas: {df.columns}")

# Algoritmos presentes
versions = df["Version"].unique().tolist()

# Preparar datos para boxplot
series = []
positions = []
owners = []
group_gap = 1.5
box_w = 0.4
centers = np.arange(1) * group_gap + 1.0  # solo 1 operación: Tiempo total

offs = np.linspace(-box_w*(len(versions)-1),
                   box_w*(len(versions)-1),
                   len(versions))/2

for vi, v in enumerate(versions):
    vals = df.loc[df["Version"] == v, "Total(ms)"].dropna().values
    if len(vals) == 0:
        vals = np.array([np.nan])
    positions.append(centers[0] + offs[vi])
    series.append(vals)
    owners.append(v)

# Ajuste de escala logarítmica
valid = [s[~np.isnan(s)] for s in series if len(s) > 0 and not np.all(np.isnan(s))]
all_vals = np.concatenate(valid) if valid else np.array([1.0])
p1, p99 = np.percentile(all_vals, [1, 99]) if all_vals.size > 0 else (1e-3, 1.0)
ymin, ymax = max(p1/1.5, 1e-3), p99*1.5

# Dibujar boxplot
plt.figure(figsize=(8, 5))
bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                 showfliers=True, patch_artist=True)

palette = {"Falcon-512": "#4c78a8", "Falcon-1024": "#54a24b"}
for b, v in zip(bp["boxes"], owners):
    c = palette.get(v, "#888")
    b.set_facecolor(c)
    b.set_edgecolor(c)
    b.set_alpha(0.7)

plt.xticks(centers, ["Tiempo total"])
plt.ylabel("Tiempo (ms)")
plt.title("Falcon (Python / oqs) — Tiempo total")
plt.yscale("log")
plt.ylim(ymin, ymax)
plt.grid(True, which="both", axis="y", linestyle="--", alpha=0.5)

handles = [mpatches.Patch(facecolor=palette.get(v, "#888"),
                          edgecolor=palette.get(v, "#888"),
                          label=v, alpha=0.7) for v in versions]
plt.legend(handles=handles, title="Versión", loc="upper left")

plt.tight_layout()
plt.savefig(PNG_OUT, dpi=150)
print(f"OK -> {PNG_OUT}")
