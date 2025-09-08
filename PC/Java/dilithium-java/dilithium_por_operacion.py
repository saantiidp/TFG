#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re, unicodedata, io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

INFILE = "Dilithium_Performance_Iteration.csv"
OUTFILE = "dilithium_java_boxplot_por_operacion.png"

# ------------ utilidades -------------
def strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", str(text))
                   if unicodedata.category(ch) != "Mn")

def norm_col(name: str) -> str:
    name = strip_accents(str(name)).lower().replace("ñ","n")
    name = re.sub(r"[^a-z0-9]+","_",name)
    return re.sub(r"_+","_",name).strip("_")

def to_float(val):
    if val is None:
        return np.nan
    try:
        if pd.isna(val):
            return np.nan
    except Exception:
        pass
    s = str(val).strip()
    if s == "" or s == ".":
        return np.nan
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(s)
    except Exception:
        return np.nan

def read_unified_csv(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, sep=None, engine="python", dtype=str)
        if df.shape[1] >= 3:
            df.columns = [norm_col(c) for c in df.columns]
            return df
    except Exception:
        pass

    rows = []
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    header_line = None
    if lines and re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]", lines[0]):
        header_line = lines[0]

    seps = [";", ",", "\t", "|"]
    sep = ","
    if header_line:
        counts = {s: header_line.count(s) for s in seps}
        sep = max(counts, key=counts.get) if counts else ","

    if header_line:
        headers = [norm_col(h) for h in header_line.split(sep)]
        data_lines = lines[1:]
    else:
        headers = []
        data_lines = lines

    table = []
    for ln in data_lines:
        parts = [p.strip() for p in ln.split(sep)]
        if sep == "," and len(parts) >= 6:
            k = parts[-6] + "," + parts[-5]
            s = parts[-4] + "," + parts[-3]
            v = parts[-2] + "," + parts[-1]
            prefix = parts[:-6]
            table.append(prefix + [k, s, v])
        else:
            table.append(parts)

    max_cols = max(len(r) for r in table) if table else 0
    if not headers or len(headers) != max_cols:
        headers = [f"col{i+1}" for i in range(max_cols)]

    df = pd.DataFrame(table, columns=headers)
    df.columns = [norm_col(c) for c in df.columns]
    return df

def find_first_by_regex(df: pd.DataFrame, patterns):
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in df.columns:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

def extract_long(df: pd.DataFrame) -> pd.DataFrame:
    ver_col = find_first_by_regex(df, [r"^version$", r"^versi[oó]n$", r"^algoritmo$", r"^variant$", r"^level$"])
    if not ver_col:
        raise SystemExit("No se encontró columna de versión en el CSV unificado.")

    key_c = find_first_by_regex(df, [r"(key[_-]?gen|keygen|key_generation|generaci[oó]n.*clave)"])
    sign_s = find_first_by_regex(df, [r"(sign|firma).*?(small|peq|pequeno)"])
    sign_l = find_first_by_regex(df, [r"(sign|firma).*?(large|gran|grande)"])
    veri_s = find_first_by_regex(df, [r"(verify|verif).*?(small|peq|pequeno)"])
    veri_l = find_first_by_regex(df, [r"(verify|verif).*?(large|gran|grande)"])
    sign_g = find_first_by_regex(df, [r"(sign|firma).*?(ms|time)$"])
    veri_g = find_first_by_regex(df, [r"(verify|verif).*?(ms|time)$"])

    def norm_ver(v: str) -> str:
        s = str(v).lower()
        if "2" in s: return "Dilithium2"
        if "3" in s: return "Dilithium3"
        if "5" in s: return "Dilithium5"
        return str(v)

    versions = df[ver_col].astype(str).map(norm_ver)

    frames = []
    if key_c:
        frames.append(pd.DataFrame({
            "Versión": versions,
            "Operación": "Keygen",
            "Tiempo (ms)": df[key_c].map(to_float)
        }))

    sign_parts = []
    if sign_s: sign_parts.append(df[sign_s].map(to_float))
    if sign_l: sign_parts.append(df[sign_l].map(to_float))
    if not sign_parts and sign_g:
        sign_parts.append(df[sign_g].map(to_float))

    veri_parts = []
    if veri_s: veri_parts.append(df[veri_s].map(to_float))
    if veri_l: veri_parts.append(df[veri_l].map(to_float))
    if not veri_parts and veri_g:
        veri_parts.append(df[veri_g].map(to_float))

    if sign_parts:
        sign = pd.concat(sign_parts, ignore_index=True)
        n = len(sign)
        v2 = np.resize(versions.values, n)
        frames.append(pd.DataFrame({
            "Versión": v2,
            "Operación": "Firma",
            "Tiempo (ms)": sign.values
        }))

    if veri_parts:
        veri = pd.concat(veri_parts, ignore_index=True)
        n = len(veri)
        v3 = np.resize(versions.values, n)
        frames.append(pd.DataFrame({
            "Versión": v3,
            "Operación": "Verificación",
            "Tiempo (ms)": veri.values
        }))

    if not frames:
        return pd.DataFrame(columns=["Versión","Operación","Tiempo (ms)"])

    data = pd.concat(frames, ignore_index=True)
    data = data.dropna(subset=["Tiempo (ms)"])
    data = data[data["Tiempo (ms)"] >= 0]
    return data

def plot_by_operation(data: pd.DataFrame, outfile=OUTFILE):
    versions = [v for v in ["Dilithium2","Dilithium3","Dilithium5"] if (data["Versión"]==v).any()]
    ops_order = [op for op in ["Keygen","Firma","Verificación"] if (data["Operación"]==op).any()]

    group_gap, box_w = 1.45, 0.25
    centers = np.arange(len(ops_order)) * group_gap + 1.0
    positions, series, owners = [], [], []
    for gi, op in enumerate(ops_order):
        offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
        for vi, v in enumerate(versions):
            vals = data[(data["Versión"]==v) & (data["Operación"]==op)]["Tiempo (ms)"].values
            if len(vals)==0: vals = np.array([np.nan])
            positions.append(centers[gi] + offs[vi]); series.append(vals); owners.append(v)

    valid = [s[~np.isnan(s)] for s in series if len(s)>0 and not np.all(np.isnan(s))]
    all_vals = np.concatenate(valid) if valid else np.array([1.0])
    p1, p99 = np.percentile(all_vals, [1,99]) if all_vals.size>0 else (1e-3, 1.0)
    ymin, ymax = max(p1/1.5, 1e-3), p99*1.5

    plt.figure(figsize=(14,6))
    bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                     showfliers=True, patch_artist=True,
                     medianprops=dict(linewidth=2, color="black"),
                     whiskerprops=dict(linewidth=1.3),
                     capprops=dict(linewidth=1.3),
                     boxprops=dict(linewidth=1.3))

    colors = {"Dilithium2":"#1f77b4","Dilithium3":"#ff7f0e","Dilithium5":"#2ca02c"}
    for box, v in zip(bp["boxes"], owners):
        c = colors.get(v, "#777777")
        box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.65)

    plt.xticks(centers, ops_order)
    plt.ylabel("Tiempo (ms)")
    plt.xlabel("Operación")
    plt.title("Dilithium (Java) — Comparación por operación")
    plt.yscale("log")
    plt.ylim(ymin, ymax)
    plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)
    handles = [Patch(facecolor=colors[v], edgecolor=colors[v], alpha=0.65, label=v) for v in versions]
    plt.legend(handles=handles, title="Versión", loc="upper left")
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    print(f"Gráfico guardado: {outfile}")

def main():
    if not os.path.exists(INFILE):
        raise SystemExit(f"No se encontró el archivo {INFILE} en la carpeta actual.")
    df = read_unified_csv(INFILE)
    data = extract_long(df)
    if data.empty:
        raise SystemExit("No se pudieron extraer columnas de versión/tiempos del CSV unificado.")
    plot_by_operation(data, OUTFILE)

if __name__ == "__main__":
    main()
