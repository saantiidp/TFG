#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

CSV_IN = "hqc_rendimiento.csv"
PNG_OUT = "hqc_boxplot_por_operacion.png"

PALETTE = {"HQC-128":"#1f77b4", "HQC-192":"#ff7f0e", "HQC-256":"#d62728"}
VERS = ["HQC-128","HQC-192","HQC-256"]
OPS  = [("Tiempo_Generacion_Claves","Keygen"),
        ("Tiempo_Encapsulacion","Encapsulación"),
        ("Tiempo_Decapsulacion","Decapsulación"),
        ("Tiempo_Total","Total")]

df = pd.read_csv(CSV_IN)

# filtra versiones presentes y operaciones realmente disponibles
versions = [v for v in VERS if (df["Algoritmo"]==v).any()]
ops = [(c,l) for c,l in OPS if c in df.columns]

# rango Y auto por percentiles (escala log para cubrir L128 vs L256)
vals = pd.concat([df[c].astype(float) for c,_ in ops])
p1,p99 = np.percentile(vals, [1,99])
ymin, ymax = max(p1/1.5, 1e-3), p99*1.5

plt.figure(figsize=(16,6))
group_gap, box_w = 1.35, 0.27
centers = np.arange(len(ops)) * group_gap + 1.0

positions, series, owners = [], [], []
for gi, (col, lab) in enumerate(ops):
    offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
    for vi, v in enumerate(versions):
        vals = df.loc[df["Algoritmo"]==v, col].astype(float).values
        positions.append(centers[gi] + offs[vi]); series.append(vals); owners.append(v)

bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                 showfliers=True, patch_artist=True,
                 medianprops=dict(linewidth=2, color="black"),
                 whiskerprops=dict(linewidth=1.4), capprops=dict(linewidth=1.4),
                 boxprops=dict(linewidth=1.4))

for box, v in zip(bp["boxes"], owners):
    c = PALETTE.get(v, "#777777")
    box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.55)

plt.xticks(centers, [lab for _,lab in ops])
plt.yscale("log")
plt.ylim(ymin, ymax)
plt.ylabel("Tiempo (ms)")
plt.xlabel("Operación")
plt.title("HQC — Comparación por operación")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.55, label=v) for v in versions]
plt.legend(handles=handles, title="Versión", loc="upper left")

plt.tight_layout()
plt.savefig(PNG_OUT, dpi=150)
# plt.show()
print(f"[OK] Gráfico guardado: {PNG_OUT}")
