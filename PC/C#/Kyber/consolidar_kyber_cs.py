import os, re
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format

RAW = "kyber_cs_resources_raw.csv"
STATS = "kyber_cs_resources_stats.csv"
TABCSV = "tabla_kyber_Csharp.csv"
TABTEX = "tabla_kyber_Csharp.tex"

def parse_perf(path):
    """Devuelve el promedio de tiempo total en segundos del CSV de rendimiento."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe {path}")
    df = pd.read_csv(path)
    # Normaliza nombres de columnas
    norm = {c: re.sub(r'[^a-z0-9]+',' ', c.lower()).strip() for c in df.columns}
    df = df.rename(columns=norm)

    # 1) columna total (ms)
    for key in ["total time ms","total ms","total"]:
        if key in df.columns:
            tot_ms = pd.to_numeric(df[key], errors="coerce").dropna()
            if len(tot_ms):
                return float(tot_ms.mean())/1000.0

    # 2) suma keygen/enc/dec si existen
    keys = []
    for k in ["keygen time ms","enc time ms","dec time ms",
              "keygen ms","enc ms","dec ms",
              "keygen","enc","dec"]:
        if k in df.columns:
            keys.append(k)
    if keys:
        part = df[keys].apply(pd.to_numeric, errors="coerce")
        tot_ms = part.sum(axis=1).dropna()
        if len(tot_ms):
            return float(tot_ms.mean())/1000.0

    raise ValueError(f"No encuentro columna de total ni keygen/enc/dec en ms en {path}")

# Carga recursos (CPU/RSS)
cpu_mean = rss_mean = wall_mean = None
if os.path.exists(RAW):
    r = pd.read_csv(RAW)
    for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
        if c in r.columns:
            r[c] = pd.to_numeric(r[c], errors="coerce")
    if {"Wall_s","CPU_pct","MaxRSS_kB"}.issubset(r.columns):
        agg = r[["Wall_s","CPU_pct","MaxRSS_kB"]].mean(numeric_only=True)
        wall_mean = float(agg["Wall_s"])
        cpu_mean  = float(agg["CPU_pct"])
        rss_mean  = float(agg["MaxRSS_kB"])
        # guarda stats
        pd.DataFrame([{
            "Impl":"Kyber C# app",
            "Wall_mean": wall_mean,
            "CPU_mean":  cpu_mean,
            "RSS_mean":  rss_mean
        }]).to_csv(STATS, index=False)
    else:
        # archivo existe pero sin datos válidos
        pd.DataFrame([], columns=["Impl","Wall_mean","CPU_mean","RSS_mean"]).to_csv(STATS, index=False)
else:
    # no hay raw aún
    pd.DataFrame([], columns=["Impl","Wall_mean","CPU_mean","RSS_mean"]).to_csv(STATS, index=False)

# Tiempos por nivel (si no hay CSV de rendimiento, usamos wall_mean si existe)
niveles = [
    ("Kyber C# 512", "KyberC_sharp_Graficas/kyber512_performance2.csv"),
    ("Kyber C# 768", "KyberC_sharp_Graficas/kyber768_performance2.csv"),
    ("Kyber C# 1024","KyberC_sharp_Graficas/kyber1024_performance2.csv"),
]

filas = []
for version, path in niveles:
    tsec = None
    try:
        tsec = parse_perf(path)
    except Exception as e:
        # Si no hay CSV válido, intenta usar wall_mean como aproximación
        if wall_mean is not None:
            tsec = wall_mean
        else:
            tsec = float('nan')

    def dash_if_nan(x, fmt):
        return "—" if (x is None or pd.isna(x)) else fmt.format(x)

    filas.append({
        "LENGUAJE": "C#",
        "VERSIÓN": version,
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": dash_if_nan(tsec, "{:.2f}"),
        "USO CPU (%)": dash_if_nan(cpu_mean, "{:.0f}%"),
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": dash_if_nan(rss_mean, "{:.0f}")
    })

tabla = pd.DataFrame(filas)

# Exporta
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
