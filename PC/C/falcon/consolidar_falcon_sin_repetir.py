#!/usr/bin/env python3
"""
consolidar_falcon_sin_repetir.py
- Recalcula medias/desviaciones para Falcon a partir de falcon_resources_raw.csv (si existe)
  y genera:
    * falcon_resources_stats_refresco.csv
    * tabla_falcon_C.csv
    * tabla_falcon_C.tex
- Si no existe el raw, usa falcon_resources_stats.csv para la tabla final.
Uso:
  python3 consolidar_falcon_sin_repetir.py --dir .
"""
import argparse
from pathlib import Path
import sys
import pandas as pd
from pandas.api.types import CategoricalDtype

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default=".", help="Directorio con los CSV de Falcon")
    args = p.parse_args()

    base = Path(args.dir)
    raw = base / "falcon_resources_raw.csv"
    stats = base / "falcon_resources_stats.csv"

    stats_out = base / "falcon_resources_stats_refresco.csv"
    tabla_csv = base / "tabla_falcon_C.csv"
    tabla_tex = base / "tabla_falcon_C.tex"

    if raw.exists():
        df = pd.read_csv(raw)
        # Limpieza y tipos
        need_cols = ["Algorithm","SecurityLevel","Variant","Wall_s","CPU_pct","MaxRSS_kB"]
        for c in need_cols:
            if c not in df.columns:
                print(f"ERROR: falta columna {c} en {raw}", file=sys.stderr)
                sys.exit(1)
        df = df.dropna(subset=need_cols).copy()
        for col in ["Wall_s","CPU_pct","MaxRSS_kB"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["Wall_s","CPU_pct","MaxRSS_kB"])

        # Agrupar y calcular stats
        agg = (df.groupby(["Algorithm","SecurityLevel","Variant"])
                 .agg(Wall_mean=("Wall_s","mean"),
                      Wall_std=("Wall_s","std"),
                      CPU_mean=("CPU_pct","mean"),
                      CPU_std=("CPU_pct","std"),
                      RSS_mean=("MaxRSS_kB","mean"),
                      RSS_std=("MaxRSS_kB","std"))
                 .reset_index())

        # Si solo hay 1 muestra, std = 0
        for c in ["Wall_std","CPU_std","RSS_std"]:
            agg[c] = agg[c].fillna(0.0)

        # Redondeos
        agg["Wall_mean"] = agg["Wall_mean"].round(4)
        agg["Wall_std"]  = agg["Wall_std"].round(4)
        agg["CPU_mean"]  = agg["CPU_mean"].round(2)
        agg["CPU_std"]   = agg["CPU_std"].round(2)
        agg["RSS_mean"]  = agg["RSS_mean"].round(1)
        agg["RSS_std"]   = agg["RSS_std"].round(1)

        agg.to_csv(stats_out, index=False)
        stats_used = agg
    elif stats.exists():
        stats_used = pd.read_csv(stats)
        stats_out = stats  # ya existe
    else:
        print("ERROR: no encuentro ni falcon_resources_raw.csv ni falcon_resources_stats.csv", file=sys.stderr)
        sys.exit(1)

    # Construir tabla formato memoria
    required = {"Algorithm","SecurityLevel","Variant","Wall_mean","CPU_mean","RSS_mean"}
    if not required.issubset(set(stats_used.columns)):
        print("ERROR: CSV de stats no tiene las columnas esperadas.", file=sys.stderr)
        sys.exit(2)

    df_tab = stats_used[stats_used["Algorithm"].str.upper()=="FALCON"].copy()

    def version(row):
        lvl = int(row["SecurityLevel"])
        var = str(row["Variant"]).lower()
        name = f"FALCON-{lvl}"
        if var == "avx2":
            name += " avx2"
        return name

    df_tab["LENGUAJE"] = "C"
    df_tab["VERSIÓN"] = df_tab.apply(version, axis=1)
    df_tab["TIEMPO TOTAL DE EJECUCIÓN (segundos)"] = df_tab["Wall_mean"].round(2)
    df_tab["USO CPU (%)"] = df_tab["CPU_mean"].round(0).astype(int)
    df_tab["MEMORIA RESIDENTE USO MÁXIMO (kbytes)"] = df_tab["RSS_mean"].round(0).astype(int)

    # Orden: ref 512, ref 1024, avx2 512, avx2 1024
    var_cat = CategoricalDtype(categories=["ref","avx2"], ordered=True)
    lvl_cat = CategoricalDtype(categories=[512,1024], ordered=True)
    df_tab["Variant"] = df_tab["Variant"].astype(var_cat)
    df_tab["SecurityLevel"] = df_tab["SecurityLevel"].astype(int).astype(lvl_cat)
    df_tab = df_tab.sort_values(by=["Variant","SecurityLevel"])

    final_cols = ["LENGUAJE","VERSIÓN","TIEMPO TOTAL DE EJECUCIÓN (segundos)","USO CPU (%)","MEMORIA RESIDENTE USO MÁXIMO (kbytes)"]
    table_final = df_tab[final_cols].reset_index(drop=True)

    table_final.to_csv(tabla_csv, index=False)

    tex = table_final.to_latex(index=False, escape=False,
                               caption="Consumo de recursos de FALCON (implementación en C).",
                               label="tab:falcon_c_recursos")
    with open(tabla_tex, "w") as f:
        f.write(tex)

    print(f"OK: escrito {stats_out}")
    print(f"OK: escrito {tabla_csv}")
    print(f"OK: escrito {tabla_tex}")

if __name__ == "__main__":
    main()
