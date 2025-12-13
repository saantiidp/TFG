#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dilithium (Python) — Boxplot por operación SIN CSV

Este script ejecuta benchmarks directamente usando tus clases de
`Dilithium.default_parameters` (Dilithium2/3/5) y genera un boxplot por operación:
Keygen, Firma y Verificación. Puedes elegir si quieres separar tamaños
(pequeño/grande) o combinarlos en una sola caja por operación.

Requisitos: tu paquete `Dilithium` accesible en PYTHONPATH.

Salida:
  - dilithium_python_boxplot_por_operacion.png
"""

# ---------- Import shim: funciona como módulo O como script ----------
import sys, os

if __package__ in (None, ""):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from Dilithium.default_parameters import Dilithium2, Dilithium3, Dilithium5
except ImportError:
    from .default_parameters import Dilithium2, Dilithium3, Dilithium5

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ---------- Config ----------
ITERATIONS = 200            # nº de iteraciones por versión
COMBINE_SIZES = True        # True: una caja por operación; False: peq/grande separadas
LOG_Y = True                # eje Y logarítmico
SEED = 12345

PALETTE = {"Dilithium2":"#1f77b4","Dilithium3":"#ff7f0e","Dilithium5":"#2ca02c"}
VERSIONS = ["Dilithium2","Dilithium3","Dilithium5"]

# ---------- Helper ----------
def ensure_instance(obj):
    """Devuelve una instancia con métodos keygen/sign/verify.
    Si obj ya es una instancia, la devuelve; si es clase, instancia."""
    if hasattr(obj, "keygen") and hasattr(obj, "sign") and hasattr(obj, "verify"):
        return obj
    try:
        return obj()
    except Exception:
        return obj

# ---------- Benchmarks ----------
def bench_version(dilithium_class_or_instance, iters: int):
    """Devuelve diccionario con arrays de tiempos en ms por operación/tamaño."""
    keygen, sign_s, sign_l, ver_s, ver_l = [], [], [], [], []
    small = b"Your message signed by Dilithium"
    large = b"A" * 1000

    d = ensure_instance(dilithium_class_or_instance)

    for _ in range(iters):
        # Keygen
        t0 = time.perf_counter()
        pk, sk = d.keygen()
        keygen.append((time.perf_counter() - t0) * 1000.0)

        # Sign small
        t0 = time.perf_counter()
        sig_s = d.sign(sk, small)
        sign_s.append((time.perf_counter() - t0) * 1000.0)

        # Sign large
        t0 = time.perf_counter()
        sig_l = d.sign(sk, large)
        sign_l.append((time.perf_counter() - t0) * 1000.0)

        # Verify small
        t0 = time.perf_counter()
        ok = d.verify(pk, small, sig_s)
        ver_s.append((time.perf_counter() - t0) * 1000.0)

        # Verify large
        t0 = time.perf_counter()
        ok = d.verify(pk, large, sig_l)
        ver_l.append((time.perf_counter() - t0) * 1000.0)

    return {
        "Keygen": np.array(keygen, dtype=float),
        "Sign_small": np.array(sign_s, dtype=float),
        "Sign_large": np.array(sign_l, dtype=float),
        "Verify_small": np.array(ver_s, dtype=float),
        "Verify_large": np.array(ver_l, dtype=float),
    }

# ---------- DataFrame ----------
def build_long_df(results_map):
    rows = []
    for ver, res in results_map.items():
        rows.append(pd.DataFrame({"Versión": ver, "Operación": "Keygen", "Tamaño":"-", "Tiempo (ms)": res["Keygen"]}))
        rows.append(pd.DataFrame({"Versión": ver, "Operación": "Firma",  "Tamaño":"Pequeño", "Tiempo (ms)": res["Sign_small"]}))
        rows.append(pd.DataFrame({"Versión": ver, "Operación": "Firma",  "Tamaño":"Grande",  "Tiempo (ms)": res["Sign_large"]}))
        rows.append(pd.DataFrame({"Versión": ver, "Operación": "Verificación","Tamaño":"Pequeño","Tiempo (ms)": res["Verify_small"]}))
        rows.append(pd.DataFrame({"Versión": ver, "Operación": "Verificación","Tamaño":"Grande","Tiempo (ms)": res["Verify_large"]}))
    df = pd.concat(rows, ignore_index=True)

    if COMBINE_SIZES:
        df["Operación_full"] = df["Operación"]
    else:
        def lab(row):
            if row["Operación"] == "Keygen":
                return "Keygen"
            return f'{row["Operación"]} ({row["Tamaño"]})'
        df["Operación_full"] = df.apply(lab, axis=1)

    return df

# ---------- Plot ----------
def plot_grouped_box(df: pd.DataFrame, outfile="dilithium_python_boxplot_por_operacion.png"):
    ops_order = []
    if COMBINE_SIZES:
        for op in ["Keygen","Firma","Verificación"]:
            if (df["Operación_full"]==op).any(): ops_order.append(op)
    else:
        for op in ["Keygen","Firma (Pequeño)","Firma (Grande)","Verificación (Pequeño)","Verificación (Grande)"]:
            if (df["Operación_full"]==op).any(): ops_order.append(op)

    versions = [v for v in VERSIONS if (df["Versión"]==v).any()]

    group_gap, box_w = 1.6, 0.25
    centers = np.arange(len(ops_order)) * group_gap + 1.0

    positions, series, owners = [], [], []
    for gi, op in enumerate(ops_order):
        offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
        for vi, ver in enumerate(versions):
            vals = df[(df["Operación_full"]==op) & (df["Versión"]==ver)]["Tiempo (ms)"].dropna().values
            if len(vals)==0: vals = np.array([np.nan])
            positions.append(centers[gi] + offs[vi]); series.append(vals); owners.append(ver)

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
    for box, ver in zip(bp["boxes"], owners):
        c = PALETTE.get(ver, "#777777")
        box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.6)

    plt.xticks(centers, ops_order, rotation=0)
    plt.ylabel("Tiempo (ms)")
    plt.xlabel("Operación")
    plt.title("Dilithium (Python) — Comparación por operación" + ("" if not COMBINE_SIZES else " (combinando tamaños)"))
    if LOG_Y: plt.yscale("log")
    plt.ylim(ymin, ymax)
    plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)
    handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.6, label=v) for v in versions]
    plt.legend(handles=handles, title="Versión", loc="upper left")
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    print(f"Gráfico guardado: {outfile}")

# ---------- Main ----------
def main():
    results = {
        "Dilithium2": bench_version(Dilithium2, ITERATIONS),
        "Dilithium3": bench_version(Dilithium3, ITERATIONS),
        "Dilithium5": bench_version(Dilithium5, ITERATIONS),
    }
    df = build_long_df(results)
    plot_grouped_box(df)

if __name__ == "__main__":
    main()
