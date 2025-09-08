# hqc_java_por_operacion.py
import os, re, unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

CSV_FILES = [
    "HQC_hqc-128_iter_iter.csv",
    "HQC_hqc-192_iter_iter.csv",
    "HQC_hqc-256_iter_iter.csv",
]

# ===== Apariencia / opciones =====
LOG_Y = True             # escala log en Y (útil por diferencias grandes)
RANGE_MODE = "auto"      # "auto" o "manual"
YMIN, YMAX = 0.05, 400.0 # si RANGE_MODE == "manual"

PALETTE = {"HQC-128":"#1f77b4","HQC-192":"#ff7f0e","HQC-256":"#2ca02c"}

# ===== Utilidades =====
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn")

def normalize_col(c: str) -> str:
    c = strip_accents(c).lower().replace("ñ","n")
    c = re.sub(r"[^a-z0-9]+","_",c)
    c = re.sub(r"_+","_",c).strip("_")
    return c

def read_any_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, sep=None, engine="python")
    except Exception:
        return pd.read_csv(path)

def to_ms(s: pd.Series) -> pd.Series:
    return (s.astype(str)
             .str.replace(r"[^\d,.\-eE+]", "", regex=True)
             .str.replace(",", ".", regex=False)
             .replace({"": np.nan, ".": np.nan, "-": np.nan})
             .astype(float))

def pick(df_norm: pd.DataFrame, patterns):
    for pat in patterns:
        rx = re.compile(pat)
        for c in df_norm.columns:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

# patrones sobre columnas normalizadas (soporta ES/EN)
PATS = {
    "version": [r"(version|algoritmo|hqc.*(128|192|256))"],
    "keygen":  [r"(keygen|generacion|gen.*claves)", r"tiempo_generacion_claves", r"keygen_ms"],
    "enc":     [r"(encapsu|enc\b)",                 r"tiempo_encapsulacion",     r"enc_ms"],
    "dec":     [r"(decapsu|dec\b)",                 r"tiempo_decapsulacion",     r"dec_ms"],
    "total":   [r"(total)",                         r"tiempo_total",             r"total_ms"],
}

frames = []
for f in CSV_FILES:
    if not os.path.exists(f):
        continue
    raw = read_any_csv(f)
    df = raw.rename(columns={c: normalize_col(c) for c in raw.columns}).copy()

    c_ver = pick(df, PATS["version"])
    c_k   = pick(df, PATS["keygen"])
    c_e   = pick(df, PATS["enc"])
    c_d   = pick(df, PATS["dec"])
    c_t   = pick(df, PATS["total"])

    if c_ver is None:
        # deduce de nombre de archivo si no hay columna
        stem = os.path.basename(f).lower()
        if "128" in stem: ver = "HQC-128"
        elif "192" in stem: ver = "HQC-192"
        elif "256" in stem: ver = "HQC-256"
        else: ver = "HQC-?"
        ver_col = pd.Series([ver]*len(df), name="version")
    else:
        ver_col = df[c_ver].astype(str).str.upper()
        ver_col = (ver_col
                   .str.replace(r".*HQC[-_ ]?128.*","HQC-128",regex=True)
                   .str.replace(r".*HQC[-_ ]?192.*","HQC-192",regex=True)
                   .str.replace(r".*HQC[-_ ]?256.*","HQC-256",regex=True))

    out = pd.DataFrame({"Versión": ver_col})
    if c_k: out["Keygen ms"] = to_ms(df[c_k])
    if c_e: out["Enc ms"]    = to_ms(df[c_e])
    if c_d: out["Dec ms"]    = to_ms(df[c_d])
    if c_t: out["Total ms"]  = to_ms(df[c_t])
    elif all(c in out.columns for c in ["Keygen ms","Enc ms","Dec ms"]):
        out["Total ms"] = out["Keygen ms"] + out["Enc ms"] + out["Dec ms"]

    frames.append(out)

if not frames:
    raise SystemExit("No se encontraron CSV válidos.")

data = pd.concat(frames, ignore_index=True)

# qué versiones/operaciones existen realmente
versions = [v for v in ["HQC-128","HQC-192","HQC-256"] if (data["Versión"]==v).any()]
ops = [(c,l) for c,l in [
    ("Keygen ms","Keygen"),
    ("Enc ms","Encapsulación"),
    ("Dec ms","Decapsulación"),
    ("Total ms","Total"),
] if c in data.columns]

if not ops:
    raise SystemExit("No se encontraron columnas de operación (Keygen/Enc/Dec/Total) en los CSV.")

# rango Y
all_vals = pd.concat([data[c].dropna() for c,_ in ops])
if RANGE_MODE == "auto":
    p1, p99 = np.percentile(all_vals, [1,99])
    ymin, ymax = max(p1/1.5, 1e-3), p99*1.5
else:
    ymin, ymax = YMIN, YMAX

# ===== Plot =====
plt.figure(figsize=(14,6))
group_gap, box_w = 1.30, 0.26
centers = np.arange(len(ops)) * group_gap + 1.0

positions, series, owners = [], [], []
for gi, (col, lab) in enumerate(ops):
    offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
    for vi, v in enumerate(versions):
        vals = data.loc[data["Versión"]==v, col].dropna().values
        positions.append(centers[gi] + offs[vi])
        series.append(vals)
        owners.append(v)

bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                 showfliers=True, patch_artist=True,
                 medianprops=dict(linewidth=2, color="black"),
                 whiskerprops=dict(linewidth=1.4),
                 capprops=dict(linewidth=1.4),
                 boxprops=dict(linewidth=1.4))

for box, v in zip(bp["boxes"], owners):
    c = PALETTE.get(v, "#777777")
    box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.55)

plt.xticks(centers, [lab for _,lab in ops])
if LOG_Y: plt.yscale("log")
plt.ylim(ymin, ymax)
plt.ylabel("Tiempo (ms)")
plt.xlabel("Operación")
plt.title("HQC (Java) — Comparación por operación")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.55, label=v)
           for v in versions]
plt.legend(handles=handles, title="Versión", loc="upper left")

plt.tight_layout()
plt.savefig("hqc_java_boxplot_por_operacion.png", dpi=150)
# plt.show()
print("Gráfico guardado en: hqc_java_boxplot_por_operacion.png")
