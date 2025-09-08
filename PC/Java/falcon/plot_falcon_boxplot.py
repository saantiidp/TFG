# plot_falcon_boxplot.py — Falcon por operación (corto/largo × 512/1024)
import os, re, unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

CSV_FILES = [
    "falcon-512_corto_iter.csv",
    "falcon-512_largo_iter.csv",
    "falcon-1024_corto_iter.csv",
    "falcon-1024_largo_iter.csv",
]

# ===== Opciones de plot =====
LOG_Y = True            # escala log en Y
RANGE_MODE = "auto"     # "auto" o "manual"
YMIN, YMAX = 0.05, 300  # si RANGE_MODE == "manual"

# Paleta por combinación
PALETTE = {
    "falcon-512_corto":  "#1f77b4",
    "falcon-512_largo":  "#ff7f0e",
    "falcon-1024_corto": "#2ca02c",
    "falcon-1024_largo": "#d62728",
}

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

def pick(df: pd.DataFrame, pats):
    for pat in pats:
        rx = re.compile(pat)
        for c in df.columns:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

PATS = {
    "version": [r"(version|falcon.*(512|1024))"],
    "tipo":    [r"(tipo|mensaje|tam.*mensaje|largo|corto)"],
    "keygen":  [r"(keygen|generacion|gen.*claves)", r"tiempo_generacion_claves", r"keygen_ms"],
    "sign":    [r"(sign|firma)",                    r"tiempo_firma",              r"sign_ms"],
    "verify":  [r"(verify|verif|verificacion)",     r"tiempo_verificacion",       r"verify_ms"],
    "total":   [r"(total)",                         r"tiempo_total",              r"total_ms"],
}

# ===== Carga y normalización =====
frames = []
for f in CSV_FILES:
    if not os.path.exists(f):
        continue
    raw = read_any_csv(f)
    df = raw.rename(columns={c: normalize_col(c) for c in raw.columns}).copy()

    c_ver = pick(df, PATS["version"])
    c_tip = pick(df, PATS["tipo"])
    c_k   = pick(df, PATS["keygen"])
    c_s   = pick(df, PATS["sign"])
    c_v   = pick(df, PATS["verify"])
    c_t   = pick(df, PATS["total"])

    # Deducir versión/tipo por nombre de archivo si no vienen en columnas
    stem = os.path.basename(f).lower()
    ver = None
    if c_ver:
        ver = df[c_ver].astype(str).str.lower()
    elif "512" in stem: ver = pd.Series(["falcon-512"]*len(df))
    elif "1024" in stem: ver = pd.Series(["falcon-1024"]*len(df))
    else: ver = pd.Series(["falcon-?"]*len(df))

    tipo = None
    if c_tip:
        tipo = df[c_tip].astype(str).str.lower()
    elif "corto" in stem: tipo = pd.Series(["corto"]*len(df))
    elif "largo" in stem: tipo = pd.Series(["largo"]*len(df))
    else: tipo = pd.Series(["?"]*len(df))

    out = pd.DataFrame()
    out["Combo"] = (ver.str.replace(r".*(falcon[-_ ]?(512|1024)).*", r"\1", regex=True)
                      + "_" + tipo.str.replace(r".*(corto|largo).*", r"\1", regex=True))
    if c_k: out["Keygen ms"] = to_ms(df[c_k])
    if c_s: out["Sign ms"]   = to_ms(df[c_s])
    if c_v: out["Verify ms"] = to_ms(df[c_v])
    if c_t:
        out["Total ms"] = to_ms(df[c_t])
    elif all(c in out.columns for c in ["Keygen ms","Sign ms","Verify ms"]):
        out["Total ms"] = out["Keygen ms"] + out["Sign ms"] + out["Verify ms"]

    frames.append(out)

if not frames:
    raise SystemExit("No se encontraron CSV válidos de Falcon.")

data = pd.concat(frames, ignore_index=True)

# combos presentes y operaciones disponibles
combos = [c for c in ["falcon-512_corto","falcon-512_largo","falcon-1024_corto","falcon-1024_largo"]
          if (data["Combo"]==c).any()]
ops = [(c,l) for c,l in [("Keygen ms","Keygen"), ("Sign ms","Firma"),
                         ("Verify ms","Verificación"), ("Total ms","Total")]
       if c in data.columns]

# rango Y
all_vals = pd.concat([data[c].dropna() for c,_ in ops])
if RANGE_MODE == "auto":
    p1, p99 = np.percentile(all_vals, [1,99])
    ymin, ymax = max(p1/1.5, 1e-3), p99*1.5
else:
    ymin, ymax = YMIN, YMAX

# ===== Plot por operación =====
plt.figure(figsize=(14,6))
group_gap, box_w = 1.25, 0.22
centers = np.arange(len(ops)) * group_gap + 1.0

positions, series, owners = [], [], []
for gi, (col, lab) in enumerate(ops):
    offs = np.linspace(-box_w*(len(combos)-1), box_w*(len(combos)-1), len(combos))/2
    for ci, combo in enumerate(combos):
        vals = data.loc[data["Combo"]==combo, col].dropna().values
        positions.append(centers[gi] + offs[ci])
        series.append(vals)
        owners.append(combo)

bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                 showfliers=True, patch_artist=True,
                 medianprops=dict(linewidth=2, color="black"),
                 whiskerprops=dict(linewidth=1.3),
                 capprops=dict(linewidth=1.3),
                 boxprops=dict(linewidth=1.3))

for box, combo in zip(bp["boxes"], owners):
    c = PALETTE.get(combo, "#777777")
    box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.6)

plt.xticks(centers, [lab for _,lab in ops])
if LOG_Y: plt.yscale("log")
plt.ylim(ymin, ymax)
plt.ylabel("Tiempo (ms)")
plt.xlabel("Operación")
plt.title("Falcon — Comparación por operación (512/1024 × corto/largo)")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.45)

handles = [Patch(facecolor=PALETTE[c], edgecolor=PALETTE[c], alpha=0.6, label=c) for c in combos]
plt.legend(handles=handles, title="Versión × Mensaje", loc="upper left")

plt.tight_layout()
plt.savefig("falcon_boxplot_por_operacion.png", dpi=150)
# plt.show()
print("Gráfico guardado: falcon_boxplot_por_operacion.png")
