#!/usr/bin/env python3
import pandas as pd

STATS = "sphincs_resources_stats.csv"
OUT_CSV = "tabla_sphincs_C.csv"
OUT_TEX = "tabla_sphincs_C.tex"

df = pd.read_csv(STATS)

# Por si algunos vienen en mayúsculas/minúsculas
for c in ["Hash","Speed","Mode","Variant"]:
    df[c] = df[c].astype(str).str.strip()

# Construye la columna versión robusta
def make_version(r):
    sec = str(r["Security"]).split(".")[0]
    return f"SPHINCS+ {r['Hash']}-{sec}{r['Speed']}-{r['Mode']} {r['Variant']}"

df["VERSIÓN"] = df.apply(make_version, axis=1)

tab = df[[
    "VERSIÓN",
    "Wall_mean","CPU_mean","RSS_mean"
]].rename(columns={
    "Wall_mean":"TIEMPO TOTAL DE EJECUCIÓN (s)",
    "CPU_mean":"USO CPU (%)",
    "RSS_mean":"MEMORIA RESIDENTE USO MÁXIMO (kB)"
}).sort_values("VERSIÓN")

tab.to_csv(OUT_CSV, index=False)

tex = tab.to_latex(index=False, escape=False,
                   float_format="%.2f")
with open(OUT_TEX,"w") as f:
    f.write(tex)

print(f"OK: escrito {STATS.replace('.csv','')}_refresco.csv (usa {STATS})")
print(f"OK: escrito {OUT_CSV}")
print(f"OK: escrito {OUT_TEX}")
