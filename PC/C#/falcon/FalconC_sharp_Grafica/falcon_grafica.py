# plot_falcon_por_operacion.py
import glob, re, unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ---------------- Config ----------------
RANGE_MODE = "auto"      # "auto" o "manual"
YMIN, YMAX = 0.05, 300.0 # si RANGE_MODE == "manual"

# Colores fijos por configuración
PALETTE = {
    "Falcon512_grande":   "#1f77b4",
    "Falcon512_pequeño":  "#ff7f0e",
    "Falcon1024_grande":  "#2ca02c",
    "Falcon1024_pequeño": "#d62728",
}

# Patrones de ficheros (puedes ampliar si cambian nombres)
FILE_PATTERNS = [
    "Falcon512_*performance*.csv",
    "Falcon1024_*performance*.csv",
]

# -------------- Utilidades --------------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def normalize_col(c: str) -> str:
    c = strip_accents(str(c)).lower().replace("ñ", "n")
    c = re.sub(r"[^a-z0-9]+", "_", c)
    c = re.sub(r"_+", "_", c).strip("_")
    return c

def to_float_series(s: pd.Series) -> pd.Series:
    return (s.astype(str)
             .str.replace(r"[^\d,.\-eE+]", "", regex=True)
             .str.replace(",", ".", regex=False)
             .replace({"": np.nan, ".": np.nan, "-": np.nan})
             .astype(float))

def read_any_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, sep=None, engine="python")
    except Exception:
        return pd.read_csv(path)

def pick(df_norm: pd.DataFrame, patterns):
    cols = list(df_norm.columns)
    for pat in patterns:
        rx = re.compile(pat)
        for c in cols:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

# Columnas (sobre nombres normalizados)
PATS = {
    "keygen": [r"(keygen|generacion|gen.*claves)", r"tiempo_generacion_claves", r"keygen_ms"],
    "sign":   [r"(sign|firma)",                   r"tiempo_firma",              r"sign_ms"],
    "verify": [r"(verify|verif|verificacion)",    r"tiempo_verificacion",       r"verify_ms"],
    "total":  [r"(total)",                        r"tiempo_total",              r"total_ms"],
    # metadatos
    "version": [r"(falcon.*version)", r"version"],
    "size":    [r"(tamano|tamanio|tam|message.*size)", r"tamano_mensaje"],
}

def load_falcon_csv(path: str) -> pd.DataFrame:
    raw = read_any_csv(path)
    df = raw.rename(columns={c: normalize_col(c) for c in raw.columns}).copy()

    k = pick(df, PATS["keygen"])
    s = pick(df, PATS["sign"])
    v = pick(df, PATS["verify"])
    t = pick(df, PATS["total"])
    ver = pick(df, PATS["version"])
    siz = pick(df, PATS["size"])

    # construir dataframe normalizado
    out = pd.DataFrame()
    if k: out["Keygen ms"] = to_float_series(df[k])
    if s: out["Sign ms"]   = to_float_series(df[s])
    if v: out["Verify ms"] = to_float_series(df[v])
    if t: out["Total ms"]  = to_float_series(df[t])
    elif all(c in out.columns for c in ["Keygen ms","Sign ms","Verify ms"]):
        out["Total ms"] = out["Keygen ms"] + out["Sign ms"] + out["Verify ms"]

    # etiqueta de configuración
    if ver in df.columns and siz in df.columns:
        cfg = (df[ver].astype(str).str.strip() + "_" + df[siz].astype(str).str.strip())
        # normalizar 'pequeño' y 'grande' por si vienen con acentos
        cfg = cfg.str.replace("pequeño", "pequeño", regex=False)
        out["Config"] = cfg
    else:
        # fallback: deducir del nombre del archivo
        name = path.replace("\\", "/").split("/")[-1]
        if "512" in name and "grande" in name.lower():   out["Config"] = "Falcon512_grande"
        elif "512" in name and "peque" in name.lower():  out["Config"] = "Falcon512_pequeño"
        elif "1024" in name and "grande" in name.lower():out["Config"] = "Falcon1024_grande"
        elif "1024" in name and "peque" in name.lower(): out["Config"] = "Falcon1024_pequeño"
        else:                                            out["Config"] = "Falcon_desconocido"

    # limpiar configuraciones a las 4 esperadas
    out["Config"] = (out["Config"]
                     .str.replace(r".*512.*grande.*",  "Falcon512_grande",  regex=True)
                     .str.replace(r".*512.*peque.*",   "Falcon512_pequeño", regex=True)
                     .str.replace(r".*1024.*grande.*", "Falcon1024_grande", regex=True)
                     .str.replace(r".*1024.*peque.*",  "Falcon1024_pequeño",regex=True))
    return out[["Keygen ms","Sign ms","Verify ms","Total ms","Config"]]

# -------------- Carga --------------
frames = []
files = sorted({f for pat in FILE_PATTERNS for f in glob.glob(pat)})
if not files:
    raise SystemExit("No se encontraron CSV de Falcon.")
for f in files:
    try:
        frames.append(load_falcon_csv(f))
        print(f"[OK] {f}")
    except Exception as e:
        print(f"[X]  {f} -> {e}")

df = pd.concat(frames, ignore_index=True)

# -------------- Plot por operación --------------
configs = ["Falcon512_grande","Falcon512_pequeño","Falcon1024_grande","Falcon1024_pequeño"]
ops = [("Keygen ms","Keygen"), ("Sign ms","Firma"),
       ("Verify ms","Verificación"), ("Total ms","Total")]

# Rango Y
if RANGE_MODE == "auto":
    vals = pd.concat([df[c].dropna() for c,_ in ops if c in df.columns])
    p1, p99 = np.percentile(vals, [1, 99])
    YMIN, YMAX = max(p1/1.5, 1e-3), p99*1.5
    print(f"[RANGO AUTO] y∈[{YMIN:.4g}, {YMAX:.4g}]")

plt.figure(figsize=(14,6))
group_gap, box_w = 1.25, 0.26
centers = np.arange(len(ops)) * group_gap + 1.0
positions, series, owners = [], [], []

for gi, (col, lab) in enumerate(ops):
    offs = np.linspace(-box_w*(len(configs)-1), box_w*(len(configs)-1), len(configs))/2
    for ci, cfg in enumerate(configs):
        vals = df[df["Config"]==cfg][col].dropna().values if col in df.columns else np.array([])
        positions.append(centers[gi] + offs[ci])
        series.append(vals)
        owners.append(cfg)

bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                 showfliers=True, patch_artist=True,
                 medianprops=dict(linewidth=2, color="black"),
                 whiskerprops=dict(linewidth=1.4),
                 capprops=dict(linewidth=1.4),
                 boxprops=dict(linewidth=1.4))

for box, cfg in zip(bp["boxes"], owners):
    c = PALETTE.get(cfg, "#777777")
    box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.55)

plt.xticks(centers, [lab for _, lab in ops])
plt.yscale("log")
plt.ylim(YMIN, YMAX)
plt.ylabel("Tiempo (ms)")
plt.xlabel("Operación")
plt.title("Falcon — Comparación por operación (512/1024 × pequeño/grande)")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

legend_handles = [Patch(facecolor=PALETTE[cfg], edgecolor=PALETTE[cfg], alpha=0.55, label=cfg)
                  for cfg in configs if (df[df['Config']==cfg].shape[0] > 0)]
plt.legend(handles=legend_handles, title="Configuración", loc="upper left")

plt.tight_layout()
plt.savefig("falcon_boxplot_por_operacion.png", dpi=150)
# plt.show()
