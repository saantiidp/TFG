# consolidar_bike.py
import pandas as pd, numpy as np, os
pd.options.display.float_format = '{:.2f}'.format

RAW   = "bike_resources_raw.csv"
STATS = "bike_resources_stats.csv"
TABCSV= "tabla_bike_C.csv"
TABTEX= "tabla_bike_C.tex"

if not os.path.exists(RAW):
    print("No existe bike_resources_raw.csv. Primero ejecuta medir_bike_recursos.sh")
    raise SystemExit(1)

df = pd.read_csv(RAW)
for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Quita filas malformadas si hubiera
df = df.dropna(subset=["Wall_s","CPU_pct","MaxRSS_kB"])

agg = (df.groupby("Impl", as_index=False)
         .agg(Wall_mean=("Wall_s","mean"),
              Wall_std =("Wall_s","std"),
              CPU_mean =("CPU_pct","mean"),
              CPU_std  =("CPU_pct","std"),
              RSS_mean =("MaxRSS_kB","mean"),
              RSS_std  =("MaxRSS_kB","std")))

order = {"BIKE ref":0, "BIKE avx2":1}
agg["__ord"] = agg["Impl"].map(order).fillna(9)
agg = agg.sort_values(["__ord","Impl"]).drop(columns="__ord")

agg.to_csv(STATS, index=False)

def fila(impl, wall, cpu, rss):
    return pd.Series({
        "LENGUAJE":"C",
        "VERSIÓN": impl,
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": f"{wall:.2f}",
        "USO CPU (%)": f"{cpu:.0f}%",
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": f"{int(round(rss))}"
    })

tabla = pd.concat([fila(r.Impl, r.Wall_mean, r.CPU_mean, r.RSS_mean)
                   for _,r in agg.iterrows()], axis=1).T

tabla.to_csv(TABCSV, index=False)

latex = tabla.to_latex(index=False, escape=False,
                       column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
