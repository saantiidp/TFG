#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dilithium (Java) — boxplot POR OPERACIÓN

Lee:
  - dilithium2_java_performance.csv
  - dilithium3_java_performance.csv
  - dilithium5_java_performance.csv

Muestra Keygen / Firma / Verificación (uniendo small+large si existen).
Si no hay columna de Firma, la reconstruye como Total − Keygen − Verify.
"""

import os, re, unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ---- CSV de entrada ----
CSV_FILES = [
    "dilithium2_java_performance.csv",
    "dilithium3_java_performance.csv",
    "dilithium5_java_performance.csv",
]

# ---- (Opcional) Forzar mapeos por archivo si las cabeceras son exóticas ----
#   Claves aceptadas: key, sign_s, sign_l, sign_g, veri_s, veri_l, veri_g, tot_s, tot_l, tot_g
MAPPING_HINTS: dict[str, dict[str, str]] = {
    # "dilithium2_java_performance.csv": {
    #     "key":     r"(keygen(duration|ms|time))",
    #     "sign_g":  r"(sign(ature)?(ms|time|duration)|signatureMillis)",
    #     "verify_g":r"(verify(ms|time|duration)|verifyMillis)",
    #     "tot_g":   r"(total(ms|time|duration)|totalMillis)"
    # }
}

# ---- Apariencia ----
PALETTE = {"Dilithium2": "#1f77b4", "Dilithium3": "#ff7f0e", "Dilithium5": "#2ca02c"}
LOG_Y = True
PRINT_MAP = True  # imprime cabeceras detectadas para depurar

# ---------- utilidades ----------
def strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", str(text))
                   if unicodedata.category(ch) != "Mn")

def norm_col(name: str) -> str:
    name = strip_accents(str(name)).lower().replace("ñ","n")
    name = re.sub(r"[^a-z0-9]+","_",name)
    return re.sub(r"_+","_",name).strip("_")

def read_any(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, sep=None, engine="python")
    except Exception:
        return pd.read_csv(path)

def to_ms(s: pd.Series) -> pd.Series:
    return (s.astype(str)
              .str.replace(r"[^\d,.\-eE+]", "", regex=True)
              .str.replace(",", ".", regex=False)
              .replace({"": np.nan, ".": np.nan, "-": np.nan})
              .astype(float)
              .reset_index(drop=True))

def find_first_by_regex(df: pd.DataFrame, patterns: list[str]) -> str|None:
    cols = list(df.columns)
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in cols:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

def detect_cols(df: pd.DataFrame, hints: dict[str,str]|None=None):
    """Devuelve dict con nombres de columna (o None) para cada rol."""
    # evitar columnas de tamaño/tamaño de firma
    forbid = r"(size|tam|bytes|len|length|kbytes|bytes_per)"

    def pick(role: str, candidates: list[str]):
        if hints and role in hints:
            hit = find_first_by_regex(df, [hints[role]])
            if hit: return hit
        return find_first_by_regex(df, candidates)

    pats_key = [
        r"(key[_-]?gen|keygen|key_generation|gen.*clave|generaci[oó]n.*clave).*?(ms|time|duration)?",
        r"(^|_)kg(_|$).*?(ms|time|duration)?",
    ]
    pats_sign_s = [r"(sign|firma).*(small|peq).*?(ms|time|duration)",
                   r"(small|peq).*(sign|firma).*?(ms|time|duration)"]
    pats_sign_l = [r"(sign|firma).*(large|gran).*?(ms|time|duration)",
                   r"(large|gran).*(sign|firma).*?(ms|time|duration)"]
    pats_verify_s = [r"(verify|verif).*?(small|peq).*?(ms|time|duration)",
                     r"(small|peq).*?(verify|verif).*?(ms|time|duration)"]
    pats_verify_l = [r"(verify|verif).*?(large|gran).*?(ms|time|duration)",
                     r"(large|gran).*?(verify|verif).*?(ms|time|duration)"]
    pats_total_s = [r"(total).*?(small|peq).*?(ms|time|duration)",
                    r"(small|peq).*?(total).*?(ms|time|duration)",
                    r"^t_?total_?peq(ueno)?$"]
    pats_total_l = [r"(total).*?(large|gran).*?(ms|time|duration)",
                    r"(large|gran).*?(total).*?(ms|time|duration)",
                    r"^t_?total_?gran(de)?$"]
    pats_sign_g = [r"^(sign(ature)?|firma)([_ ]?(ms|time|duration))?$",
                   r"(sign|firma).*?(ms|time|duration)$",
                   r"^t_?sign(a|ature)?(_?ms)?$"]
    pats_verify_g = [r"^(verify|verif(icaci[oó]n)?)([_ ]?(ms|time|duration))?$",
                     r"(verify|verif).*?(ms|time|duration)$",
                     r"^t_?verify(_?ms)?$"]
    pats_total_g = [r"^(total|tiempo_?total)([_ ]?(ms|time|duration))?$",
                    r"(total).*?(ms|time|duration)$",
                    r"^t_?total(_?ms)?$"]

    def filter_forbid(name: str|None) -> str|None:
        if not name: return None
        if re.search(forbid, name, re.IGNORECASE): return None
        return name

    return {
        "key":    filter_forbid(pick("key",     pats_key)),
        "sign_s": filter_forbid(pick("sign_s",  pats_sign_s)),
        "sign_l": filter_forbid(pick("sign_l",  pats_sign_l)),
        "veri_s": filter_forbid(pick("veri_s",  pats_verify_s)),
        "veri_l": filter_forbid(pick("veri_l",  pats_verify_l)),
        "tot_s":  filter_forbid(pick("tot_s",   pats_total_s)),
        "tot_l":  filter_forbid(pick("tot_l",   pats_total_l)),
        "sign_g": filter_forbid(pick("sign_g",  pats_sign_g)),
        "veri_g": filter_forbid(pick("veri_g",  pats_verify_g)),
        "tot_g":  filter_forbid(pick("tot_g",   pats_total_g)),
    }

# ---------- carga & normaliza ----------
frames = []
for path in CSV_FILES:
    if not os.path.exists(path):
        continue

    df_raw = read_any(path)
    df_raw.columns = [norm_col(c) for c in df_raw.columns]
    df = df_raw.reset_index(drop=True)

    stem = os.path.basename(path)
    ver = "Dilithium2" if "2" in stem else "Dilithium3" if "3" in stem else "Dilithium5" if "5" in stem else "Dilithium?"

    cols = detect_cols(df, hints=MAPPING_HINTS.get(os.path.basename(path)))
    if PRINT_MAP:
        print(f"\n[MAP] {os.path.basename(path)}")
        print("  columnas:", list(df.columns)[:16], "..." if len(df.columns) > 16 else "")
        print("  detect:", cols)

    key  = to_ms(df[cols["key"]]) if cols["key"] else pd.Series(dtype=float)

    sign_parts, veri_parts = [], []

    for role in ("sign_s","sign_l","sign_g"):
        if cols[role]: sign_parts.append(to_ms(df[cols[role]]))
    for role in ("veri_s","veri_l","veri_g"):
        if cols[role]: veri_parts.append(to_ms(df[cols[role]]))

    # reconstrucción firma si sigue faltando
    if not sign_parts:
        if cols["tot_s"] and cols["veri_s"] and cols["key"]:
            sign_parts.append(to_ms(df[cols["tot_s"]]) - to_ms(df[cols["veri_s"]]) - to_ms(df[cols["key"]]))
        if cols["tot_l"] and cols["veri_l"] and cols["key"]:
            sign_parts.append(to_ms(df[cols["tot_l"]]) - to_ms(df[cols["veri_l"]]) - to_ms(df[cols["key"]]))
        if not sign_parts and cols["tot_g"] and cols["veri_g"] and cols["key"]:
            sign_parts.append(to_ms(df[cols["tot_g"]]) - to_ms(df[cols["veri_g"]]) - to_ms(df[cols["key"]]))

    sign = pd.concat(sign_parts, ignore_index=True) if sign_parts else pd.Series(dtype=float)
    veri = pd.concat(veri_parts, ignore_index=True) if veri_parts else pd.Series(dtype=float)

    blocks = []
    if not key.empty:
        blocks.append(pd.DataFrame({"Versión": ver, "Operación": "Keygen", "Tiempo (ms)": key.dropna().values}))
    if not sign.empty:
        blocks.append(pd.DataFrame({"Versión": ver, "Operación": "Firma", "Tiempo (ms)": sign.dropna().values}))
    if not veri.empty:
        blocks.append(pd.DataFrame({"Versión": ver, "Operación": "Verificación", "Tiempo (ms)": veri.dropna().values}))

    if blocks:
        frames.append(pd.concat(blocks, ignore_index=True))

if not frames:
    raise SystemExit("No se pudieron leer CSV válidos (no se reconocieron columnas de tiempo). "
                     "Activa PRINT_MAP=True y/o usa MAPPING_HINTS para forzar columnas.")

data = pd.concat(frames, ignore_index=True)

# ---------- plot ----------
versions = [v for v in ["Dilithium2","Dilithium3","Dilithium5"] if (data["Versión"]==v).any()]
ops_order = [op for op in ["Keygen","Firma","Verificación"] if (data["Operación"]==op).any()]

group_gap, box_w = 1.35, 0.26
centers = np.arange(len(ops_order)) * group_gap + 1.0
positions, series, owners = [], [], []
for gi, op in enumerate(ops_order):
    offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
    for vi, v in enumerate(versions):
        vals = data[(data["Versión"]==v) & (data["Operación"]==op)]["Tiempo (ms)"].values
        positions.append(centers[gi] + offs[vi]); series.append(vals); owners.append(v)

all_vals = np.concatenate([s for s in series if len(s)>0]) if series else np.array([1.0])
p1, p99 = np.percentile(all_vals, [1,99])
ymin, ymax = max(p1/1.5, 1e-3), p99*1.5

plt.figure(figsize=(14,6))
bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                 showfliers=True, patch_artist=True,
                 medianprops=dict(linewidth=2, color="black"),
                 whiskerprops=dict(linewidth=1.3),
                 capprops=dict(linewidth=1.3),
                 boxprops=dict(linewidth=1.3))

for box, v in zip(bp["boxes"], owners):
    c = PALETTE.get(v, "#777777")
    box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.6)

plt.xticks(centers, ops_order)
plt.ylabel("Tiempo (ms)")
plt.xlabel("Operación")
plt.title("Dilithium (Java) — Comparación por operación")
if LOG_Y: plt.yscale("log")
plt.ylim(ymin, ymax)
plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)
handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.6, label=v) for v in versions]
plt.legend(handles=handles, title="Versión", loc="upper left")
plt.tight_layout()
plt.savefig("dilithium_java_boxplot_por_operacion.png", dpi=150)
# plt.show()
print("Gráfico guardado: dilithium_java_boxplot_por_operacion.png")
