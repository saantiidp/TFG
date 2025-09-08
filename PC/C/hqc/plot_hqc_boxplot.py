import glob
import unicodedata
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ---------- Config ----------
RANGE_MODE = "auto"   # "auto" o "manual"
YMIN, YMAX = 0.1, 500.0  # si RANGE_MODE == "manual"

PALETTE = {
    "C++-128": "#d62728",
    "C++-192": "#9467bd",
    "C++-256": "#8c564b",
}

CPP_PATTERNS = {
    "C++-128": ["hqc_cpp_128*.csv"],
    "C++-192": ["hqc_cpp_192*.csv"],
    "C++-256": ["hqc_cpp_256*.csv"],
}

# ---------- Utilidades ----------
def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def normalize_col(c: str) -> str:
    c = strip_accents(c)
    c = c.lower()
    c = re.sub(r'[^a-z0-9]+', '_', c)  # espacios/puntuación -> _
    c = re.sub(r'_+', '_', c).strip('_')
    return c

def to_float_series(s: pd.Series) -> pd.Series:
    return (s.astype(str)
             .str.replace(r"[^\d,.\-eE+]", "", regex=True)
             .str.replace(",", ".", regex=False)
             .replace({"": np.nan, ".": np.nan, "-": np.nan})
             .astype(float))

def read_any_csv(path: str) -> pd.DataFrame:
    # separador auto; engine python para sep=None
    try:
        df = pd.read_csv(path, sep=None, engine="python")
    except Exception:
        # fallback a coma
        df = pd.read_csv(path)
    return df

# patrones (sobre columnas normalizadas)
PATTERNS = {
    "keygen": re.compile(r"(key|gen|genera).*ms|tiempo_generacion_claves|keygen_ms|gen_ms"),
    "enc":    re.compile(r"(enc|capsul).*ms|tiempo_encapsulacion|enc_ms"),
    "dec":    re.compile(r"(dec|capsul).*ms|tiempo_decapsulacion|dec_ms"),
    "total":  re.compile(r"total.*ms|tiempo_total|sum_ms|overall"),
}

def pick_normalized_col(df_norm: pd.DataFrame, kind: str):
    pat = PATTERNS[kind]
    for c in df_norm.columns:
        if pat.fullmatch(c) or pat.search(c):
            return c
    return None

def load_cpp(path: str, tag: str) -> pd.DataFrame:
    raw = read_any_csv(path)
    # construir dataframe con columnas normalizadas
    norm_map = {col: normalize_col(str(col)) for col in raw.columns}
    df = raw.rename(columns=norm_map).copy()

    k = pick_normalized_col(df, "keygen")
    e = pick_normalized_col(df, "enc")
    d = pick_normalized_col(df, "dec")
    t = pick_normalized_col(df, "total")

    # Log de mapeo para depurar
    print(f"[MAP] {tag} :: {path}")
    print("      columnas:", list(df.columns))
    print(f"      keygen -> {k} ; enc -> {e} ; dec -> {d} ; total -> {t}")

    if not (k and e and d):
        raise ValueError("faltan columnas de operación (keygen/enc/dec).")

    out = pd.DataFrame()
    out["Keygen ms"] = to_float_series(df[k])
    out["Enc ms"]    = to_float_series(df[e])
    out["Dec ms"]    = to_float_series(df[d])
    if t:
        out["Total ms"] = to_float_series(df[t])
    else:
        out["Total ms"] = out["Keygen ms"] + out["Enc ms"] + out["Dec ms"]
    out["Versión"] = tag
    return out

# ---------- Cargar SOLO C++ ----------
frames = []
for tag, patterns in CPP_PATTERNS.items():
    files = sorted({f for pat in patterns for f in glob.glob(pat)})
    if not files:
        print(f"[!] No encontré CSV para {tag} ({' | '.join(patterns)})")
        continue
    for f in files:
        try:
            frames.append(load_cpp(f, tag))
            print(f"[OK] {tag}: {f}")
        except Exception as e:
            print(f"[X]  {tag}: {f} -> {e}")

if not frames:
    raise SystemExit("No se encontraron CSV C++ válidos.")

df = pd.concat(frames, ignore_index=True)

versions = ["C++-128","C++-192","C++-256"]
ops = [("Keygen ms","Keygen"), ("Enc ms","Encapsulación"),
       ("Dec ms","Decapsulación"), ("Total ms","Total")]

# ---------- Rango Y ----------
if RANGE_MODE == "auto":
    vals = pd.concat([df[c].dropna() for c,_ in ops])
    p1, p99 = np.percentile(vals, [1, 99])
    YMIN, YMAX = max(p1/1.5, 1e-3), p99*1.5
    print(f"[RANGO AUTO] y∈[{YMIN:.4g}, {YMAX:.4g}]")

# ---------- Plot ----------
plt.figure(figsize=(16,6))
group_gap, box_w = 1.35, 0.28
centers = np.arange(len(ops)) * group_gap + 1.0
positions, series, owners = [], [], []

for gi, (col, lab) in enumerate(ops):
    offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
    for vi, v in enumerate(versions):
        vals = df[df["Versión"]==v][col].dropna().values
        if vals.size == 0:
            print(f"[!] Sin datos para {v} -> {lab}")
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
plt.title("HQC (solo C++) — Comparación por operación")
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)
legend_handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.55, label=v)
                  for v in versions if (df[df['Versión']==v].shape[0] > 0)]
plt.legend(handles=legend_handles, title="Versión", loc="upper left")
plt.tight_layout()
plt.savefig("hqc_cpp_boxplot_por_operacion.png", dpi=150)
# plt.show()
