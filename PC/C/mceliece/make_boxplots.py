#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# === Tus 10 ficheros por defecto ===
DEFAULT_FILES = [
    "mceliece348864_ref_c.csv",
    "mceliece348864f_ref_c.csv",
    "mceliece460896_ref_c.csv",
    "mceliece460896f_ref_c.csv",
    "mceliece6688128_ref_c.csv",
    "mceliece6688128f_ref_c.csv",
    "mceliece6960119_ref_c.csv",
    "mceliece6960119f_ref_c.csv",
    "mceliece8192128_ref_c.csv",
    "mceliece8192128f_ref_c.csv",
]

# Cabeceras esperadas (español) -> clave normalizada
SPANISH_WIDE_COLS = {
    "keypair": ["tiempo_keygen", "tiempo_key_gen", "keygen"],
    "enc":     ["tiempo_encaps", "encaps", "tiempo_enc"],
    "dec":     ["tiempo_decaps", "decaps", "tiempo_dec"],
    "total":   ["tiempo_total", "total"],
}

CANDIDATE_SEPS = [",", ";", "\t", "|"]

def first_useful_line(p: Path):
    with p.open("r", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            return s
    return None

def detect_sep(p: Path):
    line = first_useful_line(p)
    if not line:
        return ","
    counts = {sep: line.count(sep) for sep in CANDIDATE_SEPS}
    sep, n = max(counts.items(), key=lambda kv: kv[1])
    if n > 0:
        return sep
    return None

def read_csv_robust(p: Path) -> pd.DataFrame:
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame()
    sep = detect_sep(p)
    for attempt in [
        dict(comment="#", sep=sep) if sep else dict(comment="#", delim_whitespace=True, engine="python"),
        dict(comment="#", sep=None, engine="python"),
        dict(comment="#"),
    ]:
        try:
            return pd.read_csv(p, **attempt)
        except Exception:
            continue
    return pd.DataFrame()

def find_col(df: pd.DataFrame, patterns: list[str]) -> str | None:
    """Encuentra una columna por lista de patrones (case-insensitive, ignora sufijos como _ms)."""
    low = {c.lower(): c for c in df.columns}
    # normaliza: quita sufijos _ms/_us etc. y repite búsqueda
    def norm(s: str):
        s = s.lower().strip()
        s = re.sub(r"\s+", "", s)
        s = re.sub(r"[_\-]+", "_", s)
        s = re.sub(r"(?:_m?s|_ns|_us|_cycles|_ticks)$", "", s)
        return s

    normalized = {norm(k): v for k, v in low.items()}
    for pat in patterns:
        # admite coincidencia parcial, p.ej. "tiempo_keygen" dentro de "tiempo_keygen_ms"
        for key, orig in normalized.items():
            if pat in key:
                # asegúrate de que sea numérica
                if pd.api.types.is_numeric_dtype(df[orig]):
                    return orig
                # intentar convertir si es posible
                try:
                    test = pd.to_numeric(df[orig], errors="coerce")
                    if test.notna().any():
                        return orig
                except Exception:
                    pass
    return None

def arrays_por_operacion_es_wide(df: pd.DataFrame) -> dict[str, np.ndarray]:
    if df.empty:
        return {}
    # convierte columnas numéricas cuando se pueda
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="ignore")

    out = {}
    mapping = {}
    for op_key, pats in SPANISH_WIDE_COLS.items():
        col = find_col(df, pats)
        if col:
            mapping[op_key] = col

    # si no encontró al menos una, no hay datos útiles
    if not mapping:
        return {}

    for op_key, col in mapping.items():
        vals = pd.to_numeric(df[col], errors="coerce").dropna().to_numpy()
        if vals.size:
            out[op_key] = vals

    # si falta total pero existen las tres operaciones, intenta construirlo fila a fila
    if "total" not in out and all(k in mapping for k in ["keypair", "enc", "dec"]):
        try:
            tot = pd.to_numeric(df[mapping["keypair"]], errors="coerce") \
                + pd.to_numeric(df[mapping["enc"]], errors="coerce") \
                + pd.to_numeric(df[mapping["dec"]], errors="coerce")
            arr = tot.dropna().to_numpy()
            if arr.size:
                out["total"] = arr
        except Exception:
            pass

    return out

def variant_label_from_df_path(df: pd.DataFrame, path: Path) -> str:
    # Preferimos columna 'Parametro' si existe; si no, derivamos del nombre del archivo
    for cand in ["Parametro", "ParametroKEM", "parametro", "param"]:
        if cand in df.columns and df[cand].notna().any():
            v = str(df[cand].dropna().iloc[0])
            return v.strip()
    base = path.stem  # mceliece8192128f_ref_c
    # recorta prefijos/sufijos típicos para que quede '8192128f' o similar
    base = re.sub(r"^mceliece", "", base)
    base = re.sub(r"_ref?_c$", "", base)
    base = base.replace("_", "-")
    return base

def plot_operacion(op_key: str, data_by_variant: dict[str, np.ndarray], outdir: Path):
    variants = sorted(data_by_variant.keys())
    data = [data_by_variant[v] for v in variants if data_by_variant[v].size > 0]
    variants = [v for v in variants if data_by_variant[v].size > 0]
    if not variants:
        print(f"[AVISO] Sin datos para '{op_key}', no se genera plot.")
        return

    cmap = plt.get_cmap("tab10") if len(variants) <= 10 else plt.get_cmap("tab20")
    colors = [cmap(i % cmap.N) for i in range(len(variants))]
    legend_patches = [Patch(facecolor=colors[i], edgecolor="black", label=variants[i]) for i in range(len(variants))]

    plt.figure(figsize=(11, 6))
    bp = plt.boxplot(
        data, vert=True, patch_artist=True, showmeans=True, whis=1.5, widths=0.6
    )
    for box, color in zip(bp["boxes"], colors):
        box.set(facecolor=color, alpha=0.7, edgecolor="black")
    for med in bp["medians"]:
        med.set(color="black", linewidth=1.5)
    for whisk in bp["whiskers"]:
        whisk.set(color="black")
    for cap in bp["caps"]:
        cap.set(color="black")
    for mean in bp["means"]:
        mean.set(marker="o", markersize=5)

    etiquetas = variants
    plt.xticks(range(1, len(etiquetas) + 1), etiquetas, rotation=30, ha="right")
    nombre = {"keypair": "KeyGen", "enc": "Encaps", "dec": "Decaps", "total": "Total"}.get(op_key, op_key)
    plt.title(f"McEliece versiones ref — {nombre}")
    plt.ylabel("Tiempo (ms) / ciclos")
    plt.grid(axis="y", linestyle=":", alpha=0.4)
    plt.legend(handles=legend_patches, title="Variante", loc="upper right", fontsize=9)

    outdir.mkdir(parents=True, exist_ok=True)
    out_png = outdir / f"boxplot_{op_key}.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=220)
    plt.close()
    print(f"[OK] Guardado {out_png}")

def main():
    ap = argparse.ArgumentParser(description="Genera 4 boxplots (KeyGen, Encaps, Decaps, Total) agrupando 10 variantes.")
    ap.add_argument("--files", nargs="*", default=DEFAULT_FILES, help="Lista de CSV (por defecto: los 10 mceliece*_ref_c.csv).")
    ap.add_argument("--out-dir", default="plots", help="Carpeta de salida (default: plots)")
    args = ap.parse_args()

    variantes_data = {}  # variante -> {op: array}
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"[AVISO] No existe {p}, se omite.")
            continue
        df = read_csv_robust(p)
        if df.empty:
            print(f"[AVISO] {p.name} vacío o ilegible, se omite.")
            continue

        arrs = arrays_por_operacion_es_wide(df)
        if not arrs:
            print(f"[AVISO] {p.name} sin datos detectables, se omite.")
            continue

        var_label = variant_label_from_df_path(df, p)
        variantes_data[var_label] = arrs

    if not variantes_data:
        print("[ERROR] No hay datos válidos en los CSV proporcionados.")
        return

    outdir = Path(args.out_dir)
    for op in ["keypair", "enc", "dec", "total"]:
        data_by_variant = {}
        for var, arrs in variantes_data.items():
            if op in arrs and arrs[op].size:
                data_by_variant[var] = arrs[op]
        plot_operacion(op, data_by_variant, outdir)

if __name__ == "__main__":
    main()
