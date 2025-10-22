#!/usr/bin/env python3
import os, math
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
RAW   = os.path.join(BASE, "runs_sphincs_py_resources.csv")
TABCSV= os.path.join(BASE, "tabla_sphincs_Python.csv")
TABTEX= os.path.join(BASE, "tabla_sphincs_Python.tex")

# Variantes en el orden deseado para la tabla:
ORDER = ["sha2-128s","sha2-192s","sha2-256s","shake-128s","shake-192s","shake-256s"]

def safe_fmt_time(x):
    try:
        if x is None or (isinstance(x,float) and math.isnan(x)):
            return "—"
        return f"{float(x):.2f}"
    except Exception:
        return "—"

def safe_fmt_cpu(x):
    try:
        if x is None or (isinstance(x,float) and math.isnan(x)):
            return "—"
        return f"{float(x):.0f}%"
    except Exception:
        return "—"

def safe_fmt_rss(x):
    try:
        if x is None or (isinstance(x,float) and math.isnan(x)):
            return "—"
        return f"{int(round(float(x)))}"
    except Exception:
        return "—"

# Cargar raw si existe
if os.path.exists(RAW) and os.path.getsize(RAW) > 0:
    df = pd.read_csv(RAW)
    # Limpieza mínima:
    for col in ["Wall_s","CPU_pct","MaxRSS_kB"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    agg = (df.groupby("Variant", as_index=False)
             .agg(Wall_mean=("Wall_s","mean"),
                  CPU_mean =("CPU_pct","mean"),
                  RSS_mean =("MaxRSS_kB","mean")))
else:
    agg = pd.DataFrame(columns=["Variant","Wall_mean","CPU_mean","RSS_mean"])

# Construir tabla final
rows = []
for v in ORDER:
    rec = agg.loc[agg["Variant"]==v].iloc[0] if (v in agg["Variant"].values) else None
    wall = safe_fmt_time(rec["Wall_mean"]) if rec is not None else "—"
    cpu  = safe_fmt_cpu(rec["CPU_mean"])   if rec is not None else "—"
    rss  = safe_fmt_rss(rec["RSS_mean"])   if rec is not None else "—"

    rows.append(["Python",
                 f"SPHINCS+ Python {v.upper().replace('-','-')}",
                 wall, cpu, rss])

tabla = pd.DataFrame(rows, columns=[
    "LENGUAJE",
    "VERSIÓN",
    "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)",
    "USO CPU (%)",
    "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)",
])

# Guardar CSV y LaTeX
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
