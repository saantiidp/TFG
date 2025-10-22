import os, re, pandas as pd, numpy as np

pd.options.display.float_format = '{:.2f}'.format

RAW = "mceliece_cs_resources_raw.csv"
STATS = "mceliece_cs_resources_stats.csv"
TABCSV = "tabla_mceliece_Csharp.csv"
TABTEX = "tabla_mceliece_Csharp.tex"

# ---------- 1) Agregar CPU/RSS si existen ----------
cpu = rss = np.nan
if os.path.exists(RAW) and os.path.getsize(RAW) > 0:
    raw = pd.read_csv(RAW)
    for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
        if c in raw.columns:
            raw[c] = pd.to_numeric(raw[c], errors="coerce")
    agg = (raw
           .assign(MaxRSS_kB=pd.to_numeric(raw["MaxRSS_kB"], errors="coerce"))
           .agg({"CPU_pct":"mean","MaxRSS_kB":"mean","Wall_s":"mean"}))
    cpu = float(agg.get("CPU_pct", np.nan)) if not np.isnan(agg.get("CPU_pct", np.nan)) else np.nan
    rss = float(agg.get("MaxRSS_kB", np.nan)) if not np.isnan(agg.get("MaxRSS_kB", np.nan)) else np.nan
    # guarda stats por si quieres comprobar
    pd.DataFrame([{"Impl":"McEliece C# app","Wall_mean":agg.get("Wall_s",np.nan),
                   "CPU_mean":cpu,"RSS_mean":rss}]).to_csv(STATS, index=False)
else:
    # crea un stats vacío para que no falle el entorno
    pd.DataFrame(columns=["Impl","Wall_mean","CPU_mean","RSS_mean"]).to_csv(STATS, index=False)

# ---------- 2) Leer tiempos de los *_iter.csv ----------
def total_seconds_from_csv(path):
    df = pd.read_csv(path)
    cols = [c.lower().strip() for c in df.columns]
    # busca 'total' en ms
    total_idx = next((i for i,c in enumerate(cols) if "total" in c and "ms" in c), None)
    if total_idx is not None:
        t_ms = pd.to_numeric(df.iloc[:, total_idx], errors="coerce").dropna()
        if len(t_ms): return float(t_ms.mean())/1000.0
    # si no, suma keygen+encaps/enc+decaps/dec
    def find(name):
        idx = next((i for i,c in enumerate(cols) if name in c and "ms" in c), None)
        return pd.to_numeric(df.iloc[:, idx], errors="coerce") if idx is not None else None
    key = find("key")  # keygen
    enc = find("enc")  # encaps
    dec = find("dec")  # decaps
    parts = [s for s in [key, enc, dec] if s is not None]
    if parts:
        tot = sum(s.fillna(0) for s in parts)
        return float(tot.mean())/1000.0
    raise ValueError("No encuentro columnas de total ni key/enc/dec en ms")

patterns = [
    "mceliece348864_iter.csv",   "mceliece348864f_iter.csv",
    "mceliece460896_iter.csv",   "mceliece460896f_iter.csv",
    "mceliece6688128_iter.csv",  "mceliece6688128f_iter.csv",
    "mceliece6960119_iter.csv",  "mceliece6960119f_iter.csv",
    "mceliece8192128_iter.csv",  "mceliece8192128f_iter.csv",
]

rows = []
for p in patterns:
    if not os.path.exists(p): 
        continue
    # versión bonita: "McEliece C# 348864" o "McEliece C# 348864f"
    m = re.search(r"mceliece(\d+)(f)?_iter\.csv$", p)
    if not m: 
        continue
    ver = f"McEliece C# {m.group(1)}" + ("" if m.group(2) is None else "f")
    try:
        tsec = total_seconds_from_csv(p)
    except Exception as e:
        # si falla lectura, deja tiempo como NaN para mostrar “—”
        tsec = np.nan
    rows.append((ver, tsec))

# si no hay ningún CSV, crea entradas vacías estándar (para que veas la tabla)
if not rows:
    rows = [(f"McEliece C# {s}", np.nan) for s in
            ["348864","460896","6688128","6960119","8192128"]]

# ---------- 3) Construir tabla final ----------
def dash_if_nan(x, fmt):
    return "—" if (x is None or np.isnan(x)) else fmt(x)

tabla = pd.DataFrame([
    {
      "LENGUAJE": "C#",
      "VERSIÓN": ver,
      "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": dash_if_nan(t, lambda v: f"{v:.2f}"),
      "USO CPU (%)": dash_if_nan(cpu, lambda v: f"{v:.0f}%"),
      "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": dash_if_nan(rss, lambda v: f"{int(round(v))}")
    }
    for (ver, t) in rows
])

# ---------- 4) Exportar ----------
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
