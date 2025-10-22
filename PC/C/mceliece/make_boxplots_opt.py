#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt

FILES = [
    "mceliece348864_opt_c.csv",
    "mceliece348864f_opt_c.csv",
    "mceliece460896_opt_c.csv",
    "mceliece460896f_opt_c.csv",
    "mceliece6688128_opt_c.csv",
    "mceliece6688128f_opt_c.csv",
    "mceliece6960119_opt_c.csv",
    "mceliece6960119f_opt_c.csv",
    "mceliece8192128_opt_c.csv",
    "mceliece8192128f_opt_c.csv",
]

ENC_KEYS = ["encaps", "tiempo_enc", "enc"]
DEC_KEYS = ["decaps", "tiempo_dec", "dec"]

def read_csv_simple(p: Path) -> pd.DataFrame:
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame()
    for sep in [",", ";", "\t", "|", None]:
        try:
            df = pd.read_csv(p, sep=sep, comment="#")
            if df.shape[1] > 0:
                return df
        except Exception:
            continue
    return pd.DataFrame()

def find_col(df: pd.DataFrame, keys) -> str | None:
    def norm(s): return re.sub(r"\s+", "", s.lower().strip())
    nmap = {norm(c): c for c in df.columns}
    for k in keys:
        k = norm(k)
        for nk, orig in nmap.items():
            if k in nk:
                return orig
    return None

def get_label_from_path(p: Path) -> str:
    base = p.stem
    base = re.sub(r"^mceliece", "", base, flags=re.I)
    base = re.sub(r"_opt?_c$", "", base, flags=re.I)
    return base.replace("_", "-")

def main():
    enc_data, dec_data = {}, {}
    for f in FILES:
        p = Path(f)
        df = read_csv_simple(p)
        if df.empty:
            continue
        enc_col = find_col(df, ENC_KEYS)
        dec_col = find_col(df, DEC_KEYS)
        label = get_label_from_path(p)
        if enc_col:
            enc_data[label] = pd.to_numeric(df[enc_col], errors="coerce").dropna().to_numpy()
        if dec_col:
            dec_data[label] = pd.to_numeric(df[dec_col], errors="coerce").dropna().to_numpy()

    Path("plots_opt").mkdir(exist_ok=True, parents=True)

    # --- Encaps ---
    if enc_data:
        enc_variants = sorted(enc_data.keys())
        plt.figure(figsize=(11, 5))
        plt.boxplot([enc_data[v] for v in enc_variants], patch_artist=True, showmeans=True)
        plt.xticks(range(1, len(enc_variants)+1), enc_variants, rotation=25, ha="right")
        plt.title("McEliece (opt) — Encaps")
        plt.ylabel("Tiempo (ms)")
        plt.grid(axis="y", linestyle=":", alpha=0.4)
        plt.tight_layout()
        plt.savefig("plots_opt/boxplot_enc.png", dpi=220)
        plt.close()
        print("[OK] plots_opt/boxplot_enc.png")

    # --- Decaps con escala fija 20–150 ---
    if dec_data:
        dec_variants = sorted(dec_data.keys())
        plt.figure(figsize=(11, 5))
        plt.boxplot([dec_data[v] for v in dec_variants], patch_artist=True, showmeans=True)
        plt.xticks(range(1, len(dec_variants)+1), dec_variants, rotation=25, ha="right")
        plt.title("McEliece (opt) — Decaps")
        plt.ylabel("Tiempo (ms)")
        plt.ylim(20, 150)  # <--- Escala fija 20–150
        plt.grid(axis="y", linestyle=":", alpha=0.4)
        plt.tight_layout()
        plt.savefig("plots_opt/boxplot_dec_fixed.png", dpi=220)
        plt.close()
        print("[OK] plots_opt/boxplot_dec_fixed.png")

if __name__ == "__main__":
    main()
