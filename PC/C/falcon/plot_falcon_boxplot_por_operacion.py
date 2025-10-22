# plot_falcon_boxplots_por_operacion.py
import os, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from matplotlib.patches import Patch

# Nombres bonitos y orden
PRETTY = {
    "falcon512":              "falcon512",
    "falcon512avx2":          "falconavx2_512",
    "falcon512avx2native":    "nativefalcon512avx2",
    "falcon1024":             "falcon1024",
    "falcon1024avx2":         "falconavx2_1024",
    "falcon1024avx2native":   "nativefalcon1024avx2",
}

ORDER = [
    "falcon512",
    "falcon512avx2native",
    "falcon512avx2",
    "falcon1024",
    "falcon1024avx2native",
    "falcon1024avx2",
]

PALETTE = {
    "falcon512":            "#1f77b4",
    "falcon512avx2native":  "#2ca02c",
    "falcon512avx2":        "#9467bd",
    "falcon1024":           "#8c564b",
    "falcon1024avx2native": "#17becf",
    "falcon1024avx2":       "#ff7f0e",
}

def parse_falcon_csv(path):
    """
    Intenta leer filas del CSV en el formato:
    Iter, KeygenCycles, Keygen ms, SignCycles, Sign ms, VerifyCycles, Verify ms, Total ms
    Tolera texto extra en cada celda (extrae el primer número).
    """
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 8:
                continue
            vals = []
            for i in range(8):
                m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", parts[i])
                vals.append(float(m.group(0)) if m else np.nan)
            # filtra filas sin ms válidos
            if all(np.isfinite([vals[2], vals[4], vals[6], vals[7]])):
                rows.append(vals[:8])
    if not rows:
        raise ValueError(f"Sin datos válidos en {path}")
    return pd.DataFrame(rows, columns=[
        "Iteración",
        "Keygen Cycles","Keygen ms",
        "Sign Cycles","Sign ms",
        "Verify Cycles","Verify ms",
        "Total ms"
    ])

def load_all(pattern="falcon*.csv"):
    files = sorted(glob(pattern))
    if not files:
        raise SystemExit(f"No se encontraron archivos con patrón {pattern}")
    data = {}
    for fp in files:
        name = os.path.basename(fp).replace(".csv","")
        try:
            data[name] = parse_falcon_csv(fp)
        except Exception as e:
            print(f"[!] {name}: {e}")
    if not data:
        raise SystemExit("No se pudo cargar ningún CSV válido.")
    return data

def ensure_colors(versions):
    colors = {}
    tab = plt.get_cmap("tab10")
    i = 0
    for v in versions:
        colors[v] = PALETTE.get(v, tab(i % 10))
        i += 1
    return colors

def boxplot_por_operacion(data, ylog=True, out_dir=".", dpi=160):
    # versiones en orden, ignorando faltantes y añadiendo extras al final
    versions = [v for v in ORDER if v in data] + [v for v in data if v not in ORDER]
    colors = ensure_colors(versions)

    ops = [
        ("Keygen ms",  "Boxplot_Falcon_Keygen.png",  "Keygen"),
        ("Sign ms",    "Boxplot_Falcon_Sign.png",    "Sign"),
        ("Verify ms",  "Boxplot_Falcon_Verify.png",  "Verify"),
        ("Total ms",   "Boxplot_Falcon_Total.png",   "Total"),
    ]

    for col, fname, nice in ops:
        series = [data[v][col].dropna().values for v in versions]
        labels = [PRETTY.get(v, v) for v in versions]
        cols   = [colors[v] for v in versions]

        plt.figure(figsize=(10,6))
        bp = plt.boxplot(
            series,
            labels=labels,
            showfliers=True,
            patch_artist=True,
            medianprops=dict(linewidth=2, color="black"),
            whiskerprops=dict(linewidth=1.5),
            capprops=dict(linewidth=1.5),
            boxprops=dict(linewidth=1.5),
        )
        for box, c in zip(bp["boxes"], cols):
            box.set_facecolor(c)
            box.set_edgecolor(c)
            box.set_alpha(0.55)

        plt.ylabel("Tiempo (ms)")
        plt.title(f"Falcon – {nice}")
        if ylog:
            plt.yscale("log")
        plt.grid(True, axis="y", which="both", ls="--", alpha=0.5)

        # Leyenda compacta (solo colores por versión)
        legend_handles = [Patch(facecolor=colors[v], edgecolor=colors[v], alpha=0.55,
                                label=PRETTY.get(v,v)) for v in versions]
        plt.legend(handles=legend_handles, title="Versión", loc="upper right", ncol=1)
        plt.tight_layout()
        out_path = os.path.join(out_dir, fname)
        plt.savefig(out_path, dpi=dpi)
        plt.close()
        print(f"Guardado: {out_path}")

def main():
    data = load_all("falcon*.csv")
    boxplot_por_operacion(data, ylog=True, out_dir=".")

if __name__ == "__main__":
    main()
