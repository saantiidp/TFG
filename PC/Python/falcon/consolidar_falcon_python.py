#!/usr/bin/env python3
import os, pandas as pd, numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
RAW   = os.path.join(BASE, "runs_falcon_py_resources.csv")
STATS = os.path.join(BASE, "falcon_py_resources_stats.csv")
TABCSV= os.path.join(BASE, "tabla_falcon_Python.csv")
TABTEX= os.path.join(BASE, "tabla_falcon_Python.tex")

pd.options.display.float_format = "{:.2f}".format

# 1) Cargar recursos si existen
df = None
if os.path.exists(RAW):
    df = pd.read_csv(RAW)
    for c in ["Level","Wall_s","CPU_pct","MaxRSS_kB"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
else:
    df = pd.DataFrame(columns=["Level","Wall_s","CPU_pct","MaxRSS_kB"])

# 2) Estadísticas por nivel
if len(df):
    agg = (df.groupby("Level", as_index=False)
             .agg(Wall_mean=("Wall_s","mean"),
                  CPU_mean =("CPU_pct","mean"),
                  RSS_mean =("MaxRSS_kB","mean")))
    agg.to_csv(STATS, index=False)
else:
    agg = pd.DataFrame(columns=["Level","Wall_mean","CPU_mean","RSS_mean"])
    # crea un stats vacío para evitar confusiones
    pd.DataFrame(columns=["Level","Wall(s)_mean","CPU(%)_mean","MaxRSS(kB)_mean"]).to_csv(STATS, index=False)

# 3) Intentar leer tiempos “de rendimiento” si existen (opcionales)
#    Si no hay, usamos el Wall_mean como “Tiempo total de ejecución”.
tsec_por_level = {}
# Busca un CSV con totales por nivel; si no existe, omite
candidatos = [
    os.path.join(BASE, "falcon_python_ops.csv"),    # si lo tienes
    os.path.join(BASE, "Falcon_python_ops.csv"),
    os.path.join(BASE, "falcon_total_times.csv"),
]
for path in candidatos:
    if os.path.exists(path):
        try:
            perf = pd.read_csv(path)
            # Adapta aquí si tu archivo usa otro esquema:
            # esperamos columnas: Level, Total_ms  (o Total (ms))
            if "Level" in perf.columns:
                # nombre compatible para total:
                total_col = next((c for c in perf.columns if "total" in c.lower() and "ms" in c.lower()), None)
                if total_col:
                    perf["Level"] = pd.to_numeric(perf["Level"], errors="coerce")
                    perf[total_col] = pd.to_numeric(perf[total_col], errors="coerce")
                    for _, r in perf.dropna().iterrows():
                        tsec_por_level[int(r["Level"])] = float(r[total_col]) / 1000.0
        except Exception:
            pass

# 4) Construir tabla final
filas = []
levels = sorted(set(agg["Level"].dropna().astype(int))) if len(agg) else [512, 1024]
for lvl in levels:
    row = {"LENGUAJE":"Python",
           "VERSIÓN": f"Falcon Python {lvl}",
           "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": "—",
           "USO CPU (%)": "—",
           "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": "—"}
    sub = agg[agg["Level"]==lvl]
    if len(sub):
        w = float(sub["Wall_mean"].iloc[0])
        c = float(sub["CPU_mean"].iloc[0])
        r = float(sub["RSS_mean"].iloc[0])
        # Tiempo: si hay rendimiento para ese nivel, úsalo; si no, Wall_mean
        tsec = tsec_por_level.get(lvl, w if np.isfinite(w) else np.nan)
        if np.isfinite(tsec):
            row["TIEMPO TOTAL DE\nEJECUCIÓN (segundos)"] = f"{tsec:.2f}"
        if np.isfinite(c):
            row["USO CPU (%)"] = f"{c:.0f}%"
        if np.isfinite(r):
            row["MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)"] = f"{int(round(r))}"
    filas.append(row)

tabla = pd.DataFrame(filas)

# 5) Exportar
tabla.to_csv(TABCSV, index=False)

latex = tabla.to_latex(index=False, escape=False,
                       column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
print(f"(stats de recursos en {STATS})")
