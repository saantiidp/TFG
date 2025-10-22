import os, pandas as pd, numpy as np

pd.options.display.float_format = "{:.2f}".format

RAW   = "bike_py_resources_raw.csv"
STATS = "bike_py_resources_stats.csv"
TABC  = "tabla_bike_Python.csv"
TABT  = "tabla_bike_Python.tex"

if not os.path.exists(RAW):
    print("No existe bike_py_resources_raw.csv. Ejecuta primero medir_bike_python_recursos.sh")
    raise SystemExit(1)

df = pd.read_csv(RAW)
# Asegura tipos
for c in ["Wall_s", "CPU_pct", "MaxRSS_kB"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Agrega por nivel
agg = (df.groupby("Level", as_index=False)
         .agg(Wall_mean=("Wall_s","mean"),
              Wall_std =("Wall_s","std"),
              CPU_mean =("CPU_pct","mean"),
              CPU_std  =("CPU_pct","std"),
              RSS_mean =("MaxRSS_kB","mean"),
              RSS_std  =("MaxRSS_kB","std")))

# Orden L1 < L3 < L5
ordmap = {"L1":1, "L3":3, "L5":5}
agg["__o"] = agg["Level"].map(ordmap).fillna(99)
agg = agg.sort_values(["__o", "Level"]).drop(columns="__o")

# Guarda stats
agg.to_csv(STATS, index=False)

# Construye la tabla "memoria"
def fila(level, wall, cpu, rss):
    return pd.Series({
        "LENGUAJE": "Python",
        "VERSIÓN": f"BIKE Python {level}",
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": f"{(wall or 0):.2f}",
        "USO CPU (%)": f"{(cpu or 0):.0f}%",
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": "—" if pd.isna(rss) else f"{int(round(rss))}"
    })

tabla = pd.concat([fila(r.Level, r.Wall_mean, r.CPU_mean, r.RSS_mean) for _, r in agg.iterrows()], axis=1).T

tabla.to_csv(TABC, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABT, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABC}")
print(f"OK: escrito {TABT}")
