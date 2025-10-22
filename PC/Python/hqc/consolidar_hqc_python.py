import os, pandas as pd, numpy as np
pd.options.display.float_format = '{:.2f}'.format

BASE = os.path.dirname(os.path.abspath(__file__))
RAW   = os.path.join(BASE, "hqc_py_resources_raw.csv")
STATS = os.path.join(BASE, "hqc_py_resources_stats.csv")
TABCSV= os.path.join(BASE, "tabla_hqc_Python.csv")
TABTEX= os.path.join(BASE, "tabla_hqc_Python.tex")

if not os.path.exists(RAW):
    print(f"No existe {RAW}. Ejecuta primero medir_hqc_python_recursos.sh")
    raise SystemExit(1)

df = pd.read_csv(RAW)
for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

if df.dropna(subset=["Wall_s","CPU_pct","MaxRSS_kB"]).empty:
    # Tabla vacía (pero con cabeceras correctas)
    cols = ["LENGUAJE","VERSIÓN",
            "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)",
            "USO CPU (%)",
            "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)"]
    pd.DataFrame(columns=cols).to_csv(TABCSV, index=False)
    pd.DataFrame(columns=cols).to_latex(TABTEX, index=False, escape=False,
                                        column_format="llrrr", longtable=False)
    print("OK: escrito (sin datos válidos en raw)")
    print(f"OK: escrito {TABCSV}")
    print(f"OK: escrito {TABTEX}")
    raise SystemExit(0)

agg = (df.groupby("Level", as_index=False)
         .agg(Wall_mean=("Wall_s","mean"),
              CPU_mean =("CPU_pct","mean"),
              RSS_mean =("MaxRSS_kB","mean")))

order = {"L128":0, "L192":1, "L256":2}
agg["__o"] = agg["Level"].map(order).fillna(9)
agg = agg.sort_values(["__o","Level"]).drop(columns="__o")

# Guarda estadísticas
agg.to_csv(STATS, index=False)

def row(level, wall, cpu, rss):
    return pd.Series({
        "LENGUAJE":"Python",
        "VERSIÓN": f"HQC Python {level}",
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": f"{wall:.2f}",
        "USO CPU (%)": f"{cpu:.0f}%",
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": f"{int(round(rss))}"
    })

tabla = pd.concat([row(r.Level, r.Wall_mean, r.CPU_mean, r.RSS_mean)
                   for _, r in agg.iterrows()], axis=1).T

tabla.to_csv(TABCSV, index=False)

latex = tabla.to_latex(index=False, escape=False,
                       column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
