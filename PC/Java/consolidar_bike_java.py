#!/usr/bin/env python3
import os, math
import pandas as pd

BASE   = os.path.dirname(os.path.abspath(__file__))
RAW    = os.path.join(BASE, "bike_java_resources_raw.csv")
TABCSV = os.path.join(BASE, "tabla_bike_Java.csv")
TABTEX = os.path.join(BASE, "tabla_bike_Java.tex")

# CSVs de rendimiento (si existen): intentamos leer un "Total (ms)" o
# columnas KeyGen/Encaps/Decaps (ms) para sumar.
perf_files = {
    128: os.path.join(BASE, "BIKE_bike-128_iter.csv"),
    192: os.path.join(BASE, "BIKE_bike-192_iter.csv"),
    256: os.path.join(BASE, "BIKE_bike-256_iter.csv"),
}

def total_seconds_from_perf(csv_path):
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return None

    cols = [c.lower().strip() for c in df.columns]
    # Intento 1: 'total (ms)'
    for c in df.columns:
        if c.lower().strip() in ("total (ms)", "total_ms", "total"):
            ms = pd.to_numeric(df[c], errors="coerce").dropna()
            if len(ms):
                return ms.mean() / 1000.0

    # Intento 2: sumar keygen/encaps/decaps en ms
    key_candidates = [c for c in df.columns if "key" in c.lower() and "ms" in c.lower()]
    enc_candidates = [c for c in df.columns if "enc" in c.lower() and "ms" in c.lower()]
    dec_candidates = [c for c in df.columns if ("dec" in c.lower() or "decap" in c.lower()) and "ms" in c.lower()]

    if key_candidates and enc_candidates and dec_candidates:
        key = pd.to_numeric(df[key_candidates[0]], errors="coerce")
        enc = pd.to_numeric(df[enc_candidates[0]], errors="coerce")
        dec = pd.to_numeric(df[dec_candidates[0]], errors="coerce")
        s = (key + enc + dec).dropna()
        if len(s):
            return s.mean() / 1000.0

    return None

# 1) Stats de recursos (CPU/RSS) desde RAW
cpu, rss = {}, {}
if os.path.exists(RAW):
    df = pd.read_csv(RAW)
    # Limpieza
    for c in df.columns:
        if "CPU" in c:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        if "Wall" in c:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        if "RSS" in c or "MaxRSS" in c:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    agg = df.groupby("Level", as_index=False).agg(
        Wall_mean=("Wall_s", "mean"),
        CPU_mean =("CPU_pct", "mean"),
        RSS_mean =("MaxRSS_kB", "mean"),
    )

    for _, r in agg.iterrows():
        level = int(r.Level)
        cpu[level] = None if pd.isna(r.CPU_mean) else float(r.CPU_mean)
        rss[level] = None if pd.isna(r.RSS_mean) else float(r.RSS_mean)

# 2) Tiempo: preferimos performance CSV; si no, Wall_mean del RAW
time_sec = {}
for level, path in perf_files.items():
    t = total_seconds_from_perf(path)
    if t is not None and not math.isnan(t):
        time_sec[level] = float(t)

if os.path.exists(RAW):
    df = pd.read_csv(RAW)
    if "Wall_s" in df.columns and "Level" in df.columns:
        wall_agg = df.groupby("Level", as_index=False)["Wall_s"].mean()
        for _, r in wall_agg.iterrows():
            lvl = int(r.Level)
            if lvl not in time_sec:
                time_sec[lvl] = float(r.Wall_s)

# 3) Montar tabla
rows = []
for lvl in (128, 192, 256):
    lang   = "Java"
    version= f"BIKE Java {lvl}"

    tsec = time_sec.get(lvl, None)
    cp   = cpu.get(lvl, None)
    rs   = rss.get(lvl, None)

    t_str  = f"{tsec:.2f}" if (tsec is not None and not math.isnan(tsec)) else "—"
    cpu_str= f"{cp:.0f}%"  if (cp   is not None and not math.isnan(cp))   else "—"
    rss_str= f"{int(round(rs))}" if (rs is not None and not math.isnan(rs)) else "—"

    rows.append([lang, version, t_str, cpu_str, rss_str])

tabla = pd.DataFrame(rows, columns=[
    "LENGUAJE",
    "VERSIÓN",
    "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)",
    "USO CPU (%)",
    "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)",
])

# Orden razonable
ord_map = {128:0, 192:1, 256:2}
tabla["__k"] = tabla["VERSIÓN"].str.extract(r'(\d+)$').astype(int).map(ord_map)
tabla = tabla.sort_values("__k").drop(columns="__k").reset_index(drop=True)

# 4) Escribir CSV + LaTeX
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {os.path.relpath(TABCSV, BASE)}")
print(f"OK: escrito {os.path.relpath(TABTEX, BASE)}")
