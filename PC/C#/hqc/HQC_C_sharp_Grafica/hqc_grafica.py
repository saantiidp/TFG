# plot_hqc_por_operacion.py
import glob, re, unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# -------- Config --------
RANGE_MODE = "auto"      # "auto" o "manual"
YMIN, YMAX = 0.05, 500.0 # usado si RANGE_MODE == "manual"

PALETTE = {
    "HQC-128": "#1f77b4",
    "HQC-192": "#ff7f0e",
    "HQC-256": "#2ca02c",
}

FILE_PATTERNS = {
    "HQC-128": ["hqc128*performance*.csv", "hqc_128*performance*.csv", "hqc128*.csv"],
    "HQC-192": ["hqc192*performance*.csv", "hqc_192*performance*.csv", "hqc192*.csv"],
    "HQC-256": ["hqc256*performance*.csv", "hqc_256*performance*.csv", "hqc256*.csv"],
}

# -------- Utils --------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def normalize_col(c: str) -> str:
    c = strip_accents(str(c)).lower().replace("ñ","n")
    c = re.sub(r"[^a-z0-9]+","_",c)
    c = re.sub(r"_+","_",c).strip("_")
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

def pick(df: pd.DataFrame, patterns):
    cols = list(df.columns)
    for pat in patterns:
        rx = re.compile(pat)
        for c in cols:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

# Patrones sobre nombres normalizados
PATS = {
    "keygen": [r"(keygen|generacion|gen.*claves)", r"tiempo_generacion_claves", r"keygen_ms"],
    "enc":    [r"(encapsu|enc\b)",                r"tiempo_encapsulacion",     r"enc_ms"],
    "dec":    [r"(decapsu|dec\b)",                r"tiempo_decapsulacion",     r"dec_ms"],
    "total":  [r"(total)",                        r"tiempo_total",             r"total_ms"],
}

def load_hqc_csv(path: str, tag: str) -> pd.DataFrame:
    raw = read_any_csv(path)
    df  = raw.rename(columns={c: normalize_col(c) for c in raw.columns}).copy()

    k = pick(df, PATS["keygen"])
    e = pick(df, PATS["enc"])
    d = pick(df, PATS["dec"])
    t = pick(df, PATS["total"])

    # Log de mapeo para depurar si hiciera falta
    print(f"[MAP] {tag} :: {path}")
    print("      cols:", list(df.columns))
    print(f"      keygen -> {k} ; enc -> {e} ; dec -> {d} ; total -> {t}")

    out = pd.DataFrame()
    if k: out["Keygen ms"] = to_float_series(df[k])
    if e: out["Enc ms"]    = to_float_series(df[e])
    if d: out["Dec ms"]    = to_float_series(df[d])
    if t:
        out["Total ms"]    = to_float_series(df[t])
    elif all(c in out.columns for c in ["Keygen ms","Enc ms","Dec ms"]):
        out["Total ms"] = out["Keygen ms"] + out["Enc ms"] + out["Dec ms"]

    if out.empty:
        raise ValueError("No encontré columnas de operación en este CSV.")

    out["Versión"] = tag
    return out[["Keygen ms","Enc ms","Dec ms","Total ms","Versión"]]

# -------- Carga --------
frames = []
for tag, patterns in FILE_PATTERNS.items():
    files = sorted({f for pat in patterns for f in glob.glob(pat)})
    if not files:
        print(f"[!] No encontré CSV para {tag} (patrones: {' | '.join(patterns)})")
        continue
    for f in files:
        try:
            frames.append(load_hqc_csv(f, tag))
            print(f"[OK] {tag}: {f}")
        except Exception as e:
            print(f"[X]  {tag}: {f} -> {e}")

if not frames:
    raise SystemExit("No se pudo cargar ningún CSV de HQC.")

df = pd.concat(frames, ignore_index=True)

# -------- Plot por operación --------
versions = ["HQC-128","HQC-192","HQC-256"]
ops = [("Keygen ms","Keygen"),
       ("Enc ms","Encapsulación"),
       ("Dec ms","Decapsulación"),
       ("Total ms","Total")]

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
plt.title("HQC — Comparación por operación (128/192/256)")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

legend_handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.55, label=v)
                  for v in versions]
plt.legend(handles=legend_handles, title="Versión", loc="upper left")

plt.tight_layout()
plt.savefig("hqc_boxplot_por_operacion.png", dpi=150)
# plt.show()
