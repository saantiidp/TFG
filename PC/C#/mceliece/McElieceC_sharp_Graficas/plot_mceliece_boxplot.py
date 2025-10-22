import pandas as pd, numpy as np, os, re
pd.options.display.float_format = "{:.2f}".format

# Archivos de trabajo en el directorio actual
RAW_RES   = "mceliece_cs_resources_raw.csv"
STATS_RES = "mceliece_cs_resources_stats.csv"
TABCSV    = "tabla_mceliece_Csharp.csv"
TABTEX    = "tabla_mceliece_Csharp.tex"

# === 1) Cargar recursos (CPU/RSS/Wall) si existen ===
cpu_mean = rss_mean = wall_mean = None
if os.path.exists(RAW_RES):
    r = pd.read_csv(RAW_RES)
    for c in ("Wall_s","CPU_pct","MaxRSS_kB"):
        if c in r.columns:
            r[c] = pd.to_numeric(r[c], errors="coerce")
    cpu_mean = float(r["CPU_pct"].mean()) if "CPU_pct" in r else None
    rss_mean = float(r["MaxRSS_kB"].mean()) if "MaxRSS_kB" in r else None
    wall_mean = float(r["Wall_s"].mean()) if "Wall_s" in r else None

# Guarda stats de recursos (si hay datos)
stats_rows = []
if wall_mean is not None or cpu_mean is not None or rss_mean is not None:
    stats_rows.append({
        "Impl":"McEliece C#",
        "Wall_mean": wall_mean if wall_mean is not None else np.nan,
        "CPU_mean":  cpu_mean  if cpu_mean  is not None else np.nan,
        "RSS_mean":  rss_mean  if rss_mean  is not None else np.nan,
    })
pd.DataFrame(stats_rows).to_csv(STATS_RES, index=False)

# === 2) Cargar tiempos por parámetro desde mceliece*_iter.csv ===
# Acepta nombres como:
#   mceliece348864_iter.csv, mceliece348864f_iter.csv, ...
candidatos = [fn for fn in os.listdir(".") if re.match(r"mceliece\d+(f)?_iter\.csv$", fn)]
if not candidatos:
    print("AVISO: no encontré ficheros mceliece*_iter.csv en el directorio actual; "
          "la tabla usará solo CPU/RSS si están disponibles.")
times = []  # (version_str, seconds)
for fn in sorted(candidatos):
    try:
        df = pd.read_csv(fn)
    except Exception as e:
        print(f"AVISO: no pude leer {fn}: {e}")
        continue

    # Normaliza cabeceras
    low = {c.strip().lower(): c for c in df.columns}
    # Intenta hallar 'total' (ms) o sumar keygen/encaps/decaps (ms)
    total_col = None
    for k in low:
        if "total" in k and "ms" in k:
            total_col = low[k]
            break
    total_ms = None
    if total_col and total_col in df:
        total_ms = pd.to_numeric(df[total_col], errors="coerce")
    else:
        # Buscar keygen / encaps / decaps en ms
        def find_col(word):
            for k, orig in low.items():
                if word in k and "ms" in k:
                    return orig
            return None
        kg = find_col("key") or find_col("keygen")
        en = find_col("enc") or find_col("encaps")
        de = find_col("dec") or find_col("decaps")
        if kg and en and de:
            total_ms = pd.to_numeric(df[kg], errors="coerce") \
                     + pd.to_numeric(df[en], errors="coerce") \
                     + pd.to_numeric(df[de], errors="coerce")

    if total_ms is None:
        print(f"AVISO: no encuentro columna de total ni keygen/encaps/decaps en {fn}")
        continue

    tsec = float(np.nanmean(total_ms) / 1000.0)  # a segundos
    # Obtiene versión desde el nombre: mceliece<param>(f)?_iter.csv
    m = re.match(r"mceliece(\d+(f)?)_iter\.csv$", fn)
    ver = m.group(1) if m else fn
    # etiqueta legible
    version_str = f"McEliece C# {ver}"
    times.append((version_str, tsec))

# Si no hay *_iter.csv válidos, crea entradas vacías (—)
if not times:
    # Por si quieres mostrar al menos las cinco versiones clásicas:
    base_versions = ["348864","460896","6688128","6960119","8192128"]
    times = [(f"McEliece C# {v}", np.nan) for v in base_versions]

# === 3) Construir la tabla de la memoria ===
def fmt_cpu(x):
    return f"{int(round(x))}%" if np.isfinite(x) else "—"

def fmt_rss(x):
    return f"{int(round(x))}" if np.isfinite(x) else "—"

def fmt_sec(x):
    return f"{x:.2f}" if np.isfinite(x) else "—"

cpu_str = fmt_cpu(cpu_mean) if cpu_mean is not None else "—"
rss_str = fmt_rss(rss_mean) if rss_mean is not None else "—"

rows = []
for version_str, tsec in times:
    rows.append({
        "LENGUAJE": "C#",
        "VERSIÓN": version_str,
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": fmt_sec(tsec),
        "USO CPU (%)": cpu_str,
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": rss_str,
    })

tabla = pd.DataFrame(rows)

# Ordena por número dentro del nombre (mantiene f justo detrás de su base)
def key_order(s):
    # Extrae número grande de la versión
    m = re.search(r"(\d+)", s)
    base = int(m.group(1)) if m else 10**12
    # f después
    suf = 1 if s.endswith("f") else 0
    return (base, suf, s)
tabla = tabla.sort_values(by="VERSIÓN", key=lambda s: s.map(key_order)).reset_index(drop=True)

# Exporta CSV/LaTeX
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS_RES}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
