import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

CSV = "kyber_python_ops.csv"
PALETTE = {
    "Kyber512": "#1f77b4",
    "Kyber768": "#ff7f0e",
    "Kyber1024": "#2ca02c",
}
VERSIONS = ["Kyber512", "Kyber768", "Kyber1024"]
OPS = ["Keygen", "Encaps", "Decaps", "Total"]

df = pd.read_csv(CSV)

# Rango Y auto
vals = df["Time (ms)"].dropna().values
p1, p99 = np.percentile(vals, [1, 99])
ymin, ymax = max(p1 / 1.5, 1e-3), p99 * 1.5

plt.figure(figsize=(10, 6))
group_gap, box_w = 1.25, 0.25
centers = np.arange(len(OPS)) * group_gap + 1.0

positions, series, owners = [], [], []
for gi, op in enumerate(OPS):
    offs = np.linspace(
        -box_w * (len(VERSIONS) - 1),
        box_w * (len(VERSIONS) - 1),
        len(VERSIONS),
    ) / 2
    for vi, ver in enumerate(VERSIONS):
        subset = df[(df["Version"] == ver) & (df["Operation"] == op)]
        positions.append(centers[gi] + offs[vi])
        series.append(subset["Time (ms)"].values)
        owners.append(ver)

bp = plt.boxplot(
    series,
    positions=positions,
    widths=box_w * 0.95,
    showfliers=True,
    patch_artist=True,
    medianprops=dict(linewidth=2, color="black"),
)

for box, ver in zip(bp["boxes"], owners):
    c = PALETTE.get(ver, "#777777")
    box.set_facecolor(c)
    box.set_edgecolor(c)
    box.set_alpha(0.55)

plt.xticks(centers, OPS)
plt.yscale("log")
plt.ylim(ymin, ymax)
plt.ylabel("Tiempo (ms)")
plt.xlabel("Operación")
plt.title("Kyber (Python) — Comparación por operación")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

# Leyenda corregida
handles = [
    Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.55, label=v)
    for v in VERSIONS
]
plt.legend(handles=handles, title="Versión", loc="upper left")

plt.tight_layout()
plt.savefig("kyber_python_boxplot_por_operacion.png", dpi=150)
# plt.show()
