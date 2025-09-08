# plot_falcon_boxplot_por_operacion_colores.py
import os, re, numpy as np, pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from matplotlib.patches import Patch

# Paleta fija por versión (si falta alguna, se asigna automáticamente)
PALETTE = {
    "falcon512":      "#1f77b4",
    "falcon512avx2":  "#ff7f0e",
    "falcon1024":     "#2ca02c",
    "falcon1024avx2": "#d62728",
}

def parse_falcon_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if (not line) or ("," not in line):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 8:
                continue
            ms_idx = [2,4,6,7]
            ok, vals = True, []
            for i in range(8):
                m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", parts[i])
                vals.append(float(m.group(0)) if m else np.nan)
                if i in ms_idx and (not np.isfinite(vals[-1]) or vals[-1] <= 0):
                    ok = False
            if ok:
                rows.append(vals[:8])
    if not rows:
        raise ValueError(f"No data rows parsed from {path}")
    return pd.DataFrame(rows, columns=[
        "Iteración",
        "Keygen Cycles","Keygen ms",
        "Sign Cycles","Sign ms",
        "Verify Cycles","Verify ms",
        "Total ms"
    ])

def ensure_colors(versions):
    # Asignar colores consistentes; si hay nuevas versiones, usar Tab10
    colors = {}
    tab10 = plt.get_cmap("tab10")
    auto_i = 0
    for v in versions:
        if v in PALETTE:
            colors[v] = PALETTE[v]
        else:
            colors[v] = tab10(auto_i % 10)
            auto_i += 1
    return colors

def main(pattern="falcon*.csv", out_png="comparacion_falcon_boxplot_por_operacion.png", title=None):
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

    versions = list(data.keys())
    colors = ensure_colors(versions)

    operations = [
        ("Keygen ms","Keygen"),
        ("Sign ms","Sign"),
        ("Verify ms","Verify"),
        ("Total ms","Total")
    ]

    # Preparar datos en el orden de versiones
    op_vals = {label: [ data[v][col].dropna().values for v in versions ]
               for col, label in operations}

    # --- Plot ---
    plt.figure(figsize=(14,6))
    group_gap, box_width = 1.3, 0.28
    centers = np.arange(len(operations)) * group_gap + 1.0
    positions, series = [], []

    for gi, (_, label) in enumerate(operations):
        offs = np.linspace(-box_width*(len(versions)-1), box_width*(len(versions)-1), len(versions)) / 2
        for vi, v in enumerate(versions):
            positions.append(centers[gi] + offs[vi])
            series.append(op_vals[label][vi])

    bp = plt.boxplot(
        series,
        positions=positions,
        widths=box_width*0.95,
        showfliers=True,
        patch_artist=True,
        medianprops=dict(linewidth=2, color="black"),
        whiskerprops=dict(linewidth=1.5),
        capprops=dict(linewidth=1.5),
        boxprops=dict(linewidth=1.5)
    )

    # Pintar cada caja según su versión
    for i, box in enumerate(bp["boxes"]):
        v = versions[i % len(versions)]
        box.set_facecolor(colors[v])
        box.set_edgecolor(colors[v])
        box.set_alpha(0.55)           # más legible
    for flier in bp["fliers"]:
        flier.set_alpha(0.8)
        flier.set_markersize(3)

    plt.xticks(centers, [label for _, label in operations])
    plt.yscale("log")
    plt.ylabel("Tiempo (ms)")
    plt.xlabel("Operación")
    plt.title(title or "Falcon - Comparación por operación")
    plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

    # Leyenda con los mismos colores
    legend_handles = [Patch(facecolor=colors[v], edgecolor=colors[v], alpha=0.55, label=v)
                      for v in versions]
    plt.legend(handles=legend_handles, title="Versión", loc="upper left", ncol=1)

    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    print(f"Guardado: {out_png}")

if __name__ == "__main__":
    main()
