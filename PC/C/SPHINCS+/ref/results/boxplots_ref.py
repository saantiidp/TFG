#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import glob
import os
import re
import sys

import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    p = argparse.ArgumentParser(
        description="Genera boxplots (versión de referencia) por operación a partir de CSVs de SPHINCS+."
    )
    p.add_argument(
        "--pattern",
        default="sphincs-*.csv",
        help='Patrón de búsqueda de CSV (por defecto: "sphincs-*.csv").'
    )
    p.add_argument(
        "--outdir",
        default="plots_ref",
        help='Directorio de salida para las imágenes (por defecto: "plots_ref").'
    )
    return p.parse_args()


# Extrae familia y etiqueta a partir del nombre del archivo
# Ej: "sphincs-sha256-192s-simple.csv" -> family="sha256", label="sha256-192s-simple"
FNAME_RE = re.compile(r"^sphincs-(?P<family>[^-]+)-(?P<rest>.+)\.csv$")

def parse_filename(fname):
    base = os.path.basename(fname)
    m = FNAME_RE.match(base)
    if not m:
        return None, None
    family = m.group("family")
    rest = m.group("rest")
    label = f"{family}-{rest}"
    return family, label


# Orden lógico: sha256 primero, luego shake256; dentro: 128s,128f,192s,192f,256s,256f; simple antes que robust
def sort_key(label):
    try:
        parts = label.split("-")
        family = parts[0]          # "sha256" / "shake256"
        size_sf = parts[1]         # "192s" / "128f" ...
        variant = parts[2] if len(parts) > 2 else ""  # simple / robust
        size = 0
        if size_sf.startswith("128"): size = 128
        elif size_sf.startswith("192"): size = 192
        elif size_sf.startswith("256"): size = 256
        sf = 0 if size_sf.endswith("s") else 1
        var = 0 if variant == "simple" else 1
        fam = 0 if family == "sha256" else 1
        return (fam, size, sf, var, label)
    except Exception:
        return (9, 9, 9, 9, label)


def make_boxplots_for_family(family, series_by_label, outdir):
    """
    series_by_label: dict[label] -> dict con listas (KeyGen_ms, Sign_ms, Verify_ms, Total_ms)
    Crea una figura por operación.
    """
    os.makedirs(outdir, exist_ok=True)

    ops = [
        ("KeyGen_ms", "KeyGen"),
        ("Sign_ms", "Sign"),
        ("Verify_ms", "Verify"),
        ("Total_ms", "Total"),
    ]

    labels_sorted = sorted(series_by_label.keys(), key=sort_key)

    for col, opname in ops:
        data = []
        xlabels = []
        for label in labels_sorted:
            values = series_by_label[label].get(col)
            if not values:
                continue
            data.append(values)
            xlabels.append(label.replace(family + "-", ""))  # más corto en eje X

        if not data:
            continue

        plt.figure(figsize=(10, 5))
        plt.boxplot(data, labels=xlabels, showmeans=True)
        plt.title(f"SPHINCS+ — versión de referencia — {family} — Boxplot {opname}")
        plt.ylabel("Tiempo (ms)")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()

        outname = os.path.join(outdir, f"boxplot_ref_{family}_{opname.lower()}.png")
        plt.savefig(outname, dpi=150)
        plt.close()
        print(f"[OK] Guardado: {outname}")


def main():
    args = parse_args()
    files = sorted(glob.glob(args.pattern))
    if not files:
        print(f"[ERROR] No se encontraron CSV con patrón: {args.pattern}", file=sys.stderr)
        sys.exit(1)

    data_by_family = {}

    for f in files:
        family, label = parse_filename(f)
        if family is None:
            print(f"[WARN] Nombre no reconocido, se ignora: {f}")
            continue

        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"[WARN] No pude leer {f}: {e}")
            continue

        cols_ok = {"KeyGen_ms", "Sign_ms", "Verify_ms", "Total_ms"}
        if not cols_ok.issubset(df.columns):
            print(f"[WARN] Faltan columnas esperadas en {f}. Tiene: {list(df.columns)}")
            continue

        fam_map = data_by_family.setdefault(family, {})
        label_map = fam_map.setdefault(label, {})
        for col in cols_ok:
            label_map.setdefault(col, [])

        for col in cols_ok:
            vals = [float(x) for x in df[col].dropna().values.tolist()]
            label_map[col].extend(vals)

    for family, series_by_label in data_by_family.items():
        if not series_by_label:
            continue
        make_boxplots_for_family(family, series_by_label, args.outdir)


if __name__ == "__main__":
    main()
