# plot_dilithium_csharp_por_operacion.py
import glob, re, unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ---------------- Config ----------------
RANGE_MODE = "auto"      # "auto" o "manual"
YMIN, YMAX = 0.05, 200.0 # usado si RANGE_MODE == "manual"

PALETTE = {
    "Dilithium2": "#1f77b4",
    "Dilithium3": "#ff7f0e",
    "Dilithium5": "#2ca02c",
}

FILE_PATTERNS = {
    "Dilithium2": ["Dilithium2*performance*.csv", "Dilithium2*.csv"],
    "Dilithium3": ["Dilithium3*performance*.csv", "Dilithium3*.csv"],
    "Dilithium5": ["Dilithium5*performance*.csv", "Dilithium5*.csv"],
}

# -------------- Utilidades --------------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def normalize_col(c: str) -> str:
    c = strip_accents(str(c)).lower()
    c = c.replace("ñ", "n")
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

# patrones sobre columnas normalizadas (sin exigir 'ms')
PATTERNS = {
    "keygen": [
        r"(keygen|generate|gen_claves|generacion|generacion_claves)",
        r"tiempo_generacion_claves",
    ],
    "sign": [
        r"(sign|firma|firmado)",
        r"tiempo_firma",
    ],
    "verify": [
        r"(verify|verif|verificacion)",
        r"tiempo_verificacion",
    ],
    "total": [
        r"(total)",
        r"tiempo_total",
    ],
}

def pick_col(df_norm: pd.DataFrame, kinds:list[str]):
    cols = list(df_norm.columns)
    for pat in kinds:
        rx = re.compile(pat)
        for c in cols:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

def load_csv(path: str, version_tag: str) -> pd.DataFrame:
    raw = read_any_csv(path)
    norm_map = {col: normalize_col(col) for col in raw.columns}
    df = raw.rename(columns=norm_map).copy()

    k = pick_col(df, PATTERNS["keygen"])
    s = pick_col(df, PATTERNS["sign"])
    v = pick_col(df, PATTERNS["verify"])
    t = pick_col(df, PATTERNS["total"])

    print(f"[MAP] {version_tag} :: {path}")
    print("      columnas:", list(df.columns))
    print(f"      keygen -> {k} ; sign -> {s} ; verify -> {v} ; total -> {t}")

    out = pd.DataFrame()
    if k: out["Keygen ms"] = to_float_series(df[k])
    if s: out["Sign ms"]   = to_float_series(df[s])
    if v: out["Verify ms"] = to_float_series(df[v])
    if t:
        out["Total ms"] = to_float_series(df[t])
    elif all(col in out.columns for col in ["Keygen ms","Sign ms","Verify ms"]):
        out["Total ms"] = out["Keygen ms"] + out["Sign ms"] + out["Verify ms"]

    if out.empty:
        raise ValueError("No encontré columnas de operación en este CSV.")
    out["Versión"] = version_tag
    return out[["Keygen ms","Sign ms","Verify ms","Total ms","Versión"]]

# -------------- Carga de ficheros --------------
frames = []
for version, patterns in FILE_PATTERNS.items():
    files = sorted({f for pat in patterns for f in glob.glob(pat)})
    if not files:
        print(f"[!] No encontré CSV para {version} (patrones: {' | '.join(patterns)})")
        continue
    for f in files:
        try:
            frames.append(load_csv(f, version))
            print(f"[OK] {version}: {f}")
        except Exception as e:
            print(f"[X]  {version}: {f} -> {e}")

if not frames:
    raise SystemExit("No se pudo cargar ningún CSV de Dilithium.")

df = pd.concat(frames, ignore_index=True)

# -------------- Plot por operación --------------
versions = ["Dilithium2","Dilithium3","Dilithium5"]
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
    offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
    for vi, v in enumerate(versions):
        vals = df[df["Versión"]==v][col].dropna().values if col in df.columns else np.array([])
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

plt.xticks(centers, [lab for _, lab in ops])
plt.yscale("log")
plt.ylim(YMIN, YMAX)
plt.ylabel("Tiempo (ms)")
plt.xlabel("Operación")
plt.title("Dilithium (C#) — Comparación por operación")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

legend_handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.55, label=v)
                  for v in versions]
plt.legend(handles=legend_handles, title="Versión", loc="upper left")

plt.tight_layout()
plt.savefig("dilithium_csharp_boxplot_por_operacion.png", dpi=150)
# plt.show()
