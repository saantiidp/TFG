import os
import pandas as pd
import numpy as np

pd.options.display.float_format = "{:.2f}".format

BASE = os.getcwd()
RAW_RES = "falcon_cs_resources_raw.csv"
STATS_RES = "falcon_cs_resources_stats.csv"
TABCSV = "tabla_falcon_Csharp.csv"
TABTEX = "tabla_falcon_Csharp.tex"

# CSVs de rendimiento que esperamos (nombres con y sin 'ñ')
PERF_DIR = "FalconC_sharp_Grafica"
CANDIDATOS = [
    "Falcon512_pequeño_performance.csv",
    "Falcon512_pequeno_performance.csv",
    "Falcon512_grande_performance.csv",
    "Falcon1024_pequeño_performance.csv",
    "Falcon1024_pequeno_performance.csv",
    "Falcon1024_grande_performance.csv",
]

def leer_total_ms_flexible(path):
    """
    Devuelve Serie con 'total_ms' (float) si encuentra columna total en ms,
    o suma de columnas keygen/sign/verify (en ms) si existen.
    Acepta encabezados en español/inglés de forma laxa.
    """
    df = pd.read_csv(path)
    # Normaliza nombres para búsqueda laxa
    norm = {c: c.strip().lower() for c in df.columns}
    inv = {v: k for k, v in norm.items()}

    # 1) columnas candidatas de total
    total_keys = [k for k,v in norm.items() if "total" in v and "ms" in v]
    if total_keys:
        col = total_keys[0]
        s = pd.to_numeric(df[col], errors="coerce")
        if s.notna().any():
            return s.dropna()

    # 2) sumar keygen/sign/verify
    # variantes en español/inglés (muy laxo)
    def pick_one(keys):
        for key in keys:
            for k, v in norm.items():
                if key in v:
                    return k
        return None

    keygen_col = pick_one(["keygen", "generación", "generacion", "clave"])
    sign_col   = pick_one(["sign", "firma"])
    verify_col = pick_one(["verify", "verificación", "verificacion", "verif"])

    if keygen_col and sign_col and verify_col:
        ks = pd.to_numeric(df[keygen_col], errors="coerce")
        ss = pd.to_numeric(df[sign_col],   errors="coerce")
        vs = pd.to_numeric(df[verify_col], errors="coerce")
        tot = ks.add(ss, fill_value=np.nan).add(vs, fill_value=np.nan)
        if tot.notna().any():
            return tot.dropna()

    raise ValueError("No encuentro columna de total ni keygen/sign/verify en ms")

def nombre_version_desde_archivo(fname):
    """
    'Falcon512_pequeño_performance.csv' -> 'Falcon C# 512 pequeño'
    'Falcon1024_grande_performance.csv' -> 'Falcon C# 1024 grande'
    """
    base = os.path.basename(fname).lower()
    level = "512" if "512" in base else ("1024" if "1024" in base else "?")
    if "peque" in base or "pequeno" in base:
        msg = "pequeño"
    elif "grande" in base:
        msg = "grande"
    else:
        msg = "?"
    return f"Falcon C# {level} {msg}"

# 1) Carga performance (tiempos) de cada CSV válido
filas_perf = []
for cand in CANDIDATOS:
    path = os.path.join(PERF_DIR, cand)
    if not os.path.exists(path):
        continue
    try:
        tot_ms = leer_total_ms_flexible(path)
        # promedio (ms -> s)
        tsec = tot_ms.mean() / 1000.0
        ver = nombre_version_desde_archivo(cand)
        filas_perf.append((ver, tsec))
    except Exception as e:
        print(f"AVISO: problema leyendo {path}: {e}")

perf = pd.DataFrame(filas_perf, columns=["VERSIÓN", "TSEC"]).drop_duplicates()

# 2) Carga recursos (CPU/RSS) de la app global (si existe)
cpu_mean = rss_mean = wall_mean = np.nan
if os.path.exists(RAW_RES):
    rr = pd.read_csv(RAW_RES)
    for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
        if c in rr.columns:
            rr[c] = pd.to_numeric(rr[c], errors="coerce")
    wall_mean = rr.get("Wall_s", pd.Series(dtype=float)).mean()
    cpu_mean  = rr.get("CPU_pct", pd.Series(dtype=float)).mean()
    rss_mean  = rr.get("MaxRSS_kB", pd.Series(dtype=float)).mean()

# 3) Arma tabla final (si no hay performance, usa el wall medio del run como tiempo)
if perf.empty:
    versiones = [
        "Falcon C# 512 pequeño", "Falcon C# 512 grande",
        "Falcon C# 1024 pequeño","Falcon C# 1024 grande"
    ]
    tsec_fallback = wall_mean if pd.notna(wall_mean) else np.nan
    perf = pd.DataFrame({"VERSIÓN": versiones, "TSEC": [tsec_fallback]*len(versiones)})

# 4) Construye tabla memoria
def fila(version, tsec, cpu, rss):
    tshow = "—" if pd.isna(tsec) else f"{tsec:.2f}"
    cshow = "—" if pd.isna(cpu)  else f"{cpu:.0f}%"
    rshow = "—" if pd.isna(rss)  else f"{int(round(rss))}"
    return pd.Series({
        "LENGUAJE": "C#",
        "VERSIÓN":  version,
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": tshow,
        "USO CPU (%)": cshow,
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": rshow
    })

tabla = pd.concat([fila(r.VERSIÓN, r.TSEC, cpu_mean, rss_mean) for _, r in perf.iterrows()],
                  axis=1).T

# 5) Stats de recursos (si hay datos)
if os.path.exists(RAW_RES):
    rr = pd.read_csv(RAW_RES)
    for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
        if c in rr.columns:
            rr[c] = pd.to_numeric(rr[c], errors="coerce")
    stats = (rr.assign(Impl="Falcon C#")
               .groupby("Impl", as_index=False)
               .agg(Wall_mean=("Wall_s","mean"),
                    Wall_std =("Wall_s","std"),
                    CPU_mean =("CPU_pct","mean"),
                    CPU_std  =("CPU_pct","std"),
                    RSS_mean =("MaxRSS_kB","mean"),
                    RSS_std  =("MaxRSS_kB","std")))
    stats.to_csv(STATS_RES, index=False)
else:
    # crea un stats vacío/placeholder
    pd.DataFrame(columns=["Impl","Wall_mean","Wall_std","CPU_mean","CPU_std","RSS_mean","RSS_std"]).to_csv(STATS_RES, index=False)

# 6) Exporta tabla
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS_RES}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
