#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

stats = Path("bike_resources_stats.csv")
raw = Path("bike_resources_raw.csv")

if not stats.exists() and not raw.exists():
    raise SystemExit("No encuentro ni bike_resources_stats.csv ni bike_resources_raw.csv")

def recompute_from_raw(raw_path: Path) -> pd.DataFrame:
    df = pd.read_csv(raw_path)
    # Normaliza nombres de columnas por si acaso
    df = df.rename(columns={
        "Algorithm":"Algorithm",
        "Variant":"Variant",
        "Wall_s":"Wall_s",
        "CPU_pct":"CPU_pct",
        "MaxRSS_kB":"MaxRSS_kB"
    })
    for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
        df[c] = (df[c].astype(str)
                     .str.replace("%","",regex=False)
                     .str.replace(",",".",regex=False))
        df[c] = pd.to_numeric(df[c], errors="coerce")
    grp = df.groupby("Variant", as_index=False).agg(
        Wall_mean=("Wall_s","mean"),
        Wall_std =("Wall_s","std"),
        CPU_mean =("CPU_pct","mean"),
        CPU_std  =("CPU_pct","std"),
        RSS_mean =("MaxRSS_kB","mean"),
        RSS_std  =("MaxRSS_kB","std"),
    )
    return grp

if stats.exists():
    df = pd.read_csv(stats)
else:
    df = recompute_from_raw(raw)

# Guarda copia “refresco”
df.to_csv("bike_resources_stats_refresco.csv", index=False)

# Construye tabla memoria
def pretty_variant(v):
    return {"ref":"BIKE ref","avx2":"BIKE avx2"}.get(v, f"BIKE {v}")

tab = pd.DataFrame({
    "LENGUAJE": ["C"]*len(df),
    "VERSIÓN":  [pretty_variant(v) for v in df["Variant"]],
    "TIEMPO TOTAL DE EJECUCIÓN (s)": df["Wall_mean"].round(2),
    "USO CPU (%)": df["CPU_mean"].round(1),
    "MEMORIA RESIDENTE USO MÁXIMO (kB)": df["RSS_mean"].round(0).astype(int),
})

tab = tab.sort_values("VERSIÓN").reset_index(drop=True)
tab.to_csv("tabla_bike_C.csv", index=False)

tex = tab.to_latex(index=False, escape=False,
                   float_format="%.2f".__mod__,
                   column_format="l l r r r")
with open("tabla_bike_C.tex","w") as f:
    f.write(tex)

print("OK: escrito bike_resources_stats_refresco.csv")
print("OK: escrito tabla_bike_C.csv")
print("OK: escrito tabla_bike_C.tex")
