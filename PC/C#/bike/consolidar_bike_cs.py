import pandas as pd, numpy as np, os, re

pd.options.display.float_format = '{:.2f}'.format
BASE = os.path.dirname(__file__)

RAW_RES   = os.path.join(BASE, "bike_cs_resources_raw.csv")
STATS_RES = os.path.join(BASE, "bike_cs_resources_stats.csv")
TABCSV    = os.path.join(BASE, "tabla_bike_Csharp.csv")
TABTEX    = os.path.join(BASE, "tabla_bike_Csharp.tex")

# -------- utilidades --------
def try_read_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else None

def total_seconds_from(df):
    """Busca una columna de 'total' y devuelve el promedio en segundos."""
    if df is None or df.empty:
        return None
    cols = {c.lower(): c for c in df.columns}
    # candidatos por nombre
    cand = [c for c in df.columns if re.search(r'total', c, re.I)]
    if not cand:
        # si no hay total, intenta sumar columnas keygen/enc/dec si existen
        key = next((cols.get(k) for k in ["keygen time (ms)","keygen (ms)","keygen"]), None)
        enc = next((cols.get(k) for k in ["enc time (ms)","enc (ms)","enc"]), None)
        dec = next((cols.get(k) for k in ["dec time (ms)","dec (ms)","dec"]), None)
        if key and enc and dec:
            s = pd.to_numeric(df[key], errors="coerce") + pd.to_numeric(df[enc], errors="coerce") + pd.to_numeric(df[dec], errors="coerce")
            return float(np.nanmean(s) / 1000.0)
        return None

    # usa la primera columna que tenga números
    c = cand[0]
    s = pd.to_numeric(df[c], errors="coerce")
    # heurística: si está en ms (valores grandes), pasa a segundos
    if s.dropna().median() > 50:  # 50 ms como umbral
        s = s / 1000.0
    return float(np.nanmean(s))

def load_resources_means():
    """Carga CPU% y MaxRSS_kB medios del raw de recursos y devuelve (cpu_mean, rss_mean)."""
    if not os.path.exists(RAW_RES):
        return (None, None)
    raw = pd.read_csv(RAW_RES)
    for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
        if c not in raw.columns:
            return (None, None)
    raw["CPU_pct"]   = pd.to_numeric(raw["CPU_pct"], errors="coerce")
    raw["MaxRSS_kB"] = pd.to_numeric(raw["MaxRSS_kB"], errors="coerce")
    cpu_mean = float(np.nanmean(raw["CPU_pct"])) if len(raw) else None
    rss_mean = float(np.nanmean(raw["MaxRSS_kB"])) if len(raw) else None

    # guarda stats de recursos por si quieres verlos
    agg = pd.DataFrame({
        "CPU_mean":[cpu_mean],
        "CPU_std":[float(np.nanstd(raw["CPU_pct"])) if len(raw) else np.nan],
        "RSS_mean":[rss_mean],
        "RSS_std":[float(np.nanstd(raw["MaxRSS_kB"])) if len(raw) else np.nan],
        "Wall_mean":[float(np.nanmean(pd.to_numeric(raw["Wall_s"], errors="coerce")))],
        "Wall_std":[float(np.nanstd(pd.to_numeric(raw["Wall_s"], errors="coerce")))]
    })
    agg.to_csv(STATS_RES, index=False)
    return (cpu_mean, rss_mean)

# -------- lee tiempos por nivel --------
perf_paths = {
    "128": os.path.join(BASE, "BIKE_C_sharp_Grafica", "bike128_performance.csv"),
    "192": os.path.join(BASE, "BIKE_C_sharp_Grafica", "bike192_performance.csv"),
    "256": os.path.join(BASE, "BIKE_C_sharp_Grafica", "bike256_performance.csv"),
}
totals = {}
for lvl, p in perf_paths.items():
    df = try_read_csv(p)
    t = total_seconds_from(df)
    totals[lvl] = t

# -------- lee recursos globales --------
cpu_mean, rss_mean = load_resources_means()

# -------- arma la tabla --------
rows = []
for lvl in ["128","192","256"]:
    t = totals.get(lvl)
    rows.append({
        "LENGUAJE": "C#",
        "VERSIÓN": f"BIKE C# {lvl}",
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": f"{t:.2f}" if t is not None and not np.isnan(t) else "—",
        "USO CPU (%)": f"{round(cpu_mean):.0f}%" if cpu_mean is not None and not np.isnan(cpu_mean) else "—",
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": f"{int(round(rss_mean))}" if rss_mean is not None and not np.isnan(rss_mean) else "—",
    })

tabla = pd.DataFrame(rows)

# exporta
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(
    index=False, escape=False, longtable=False,
    column_format="llrrr"
)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS_RES}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
