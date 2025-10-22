import os, pandas as pd

BASE   = os.path.dirname(os.path.abspath(__file__))
RAW    = os.path.join(BASE, "kyber_py_resources_raw.csv")
STATS  = os.path.join(BASE, "kyber_py_resources_stats.csv")
TABCSV = os.path.join(BASE, "tabla_kyber_Python.csv")
TABTEX = os.path.join(BASE, "tabla_kyber_Python.tex")

if not os.path.exists(RAW):
    print("No existe kyber_py_resources_raw.csv. Ejecuta primero medir_kyber_python_recursos.sh")
    raise SystemExit(1)

df = pd.read_csv(RAW)
for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

if df.dropna(subset=["Wall_s","CPU_pct","MaxRSS_kB"]).empty:
    # Nada válido → genera tabla vacía (cabeceras) para no romper flujo
    cols = ["LENGUAJE","VERSIÓN",
            "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)",
            "USO CPU (%)",
            "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)"]
    pd.DataFrame(columns=cols).to_csv(TABCSV, index=False)
    with open(TABTEX,"w",encoding="utf-8") as f:
        f.write(pd.DataFrame(columns=cols).to_latex(index=False, escape=False, column_format="llrrr", longtable=False))
    print("OK: escrito (sin datos válidos en raw)")
    print(f"OK: escrito {TABCSV}")
    print(f"OK: escrito {TABTEX}")
    raise SystemExit(0)

agg = (df.groupby("Level", as_index=False)
         .agg(Wall_mean=("Wall_s","mean"),
              CPU_mean =("CPU_pct","mean"),
              RSS_mean =("MaxRSS_kB","mean")))

# Orden por nivel 512 < 768 < 1024
order = {512:0, 768:1, 1024:2}
agg["__o"] = agg["Level"].map(order).fillna(99)
agg = agg.sort_values(["__o","Level"]).drop(columns="__o")

# Guarda stats
agg.to_csv(STATS, index=False)

# Tabla memoria
def fila(level, wall, cpu, rss):
    return pd.Series({
        "LENGUAJE": "Python",
        "VERSIÓN": f"Kyber Python {int(level)}",
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": f"{wall:.2f}",
        "USO CPU (%)": f"{cpu:.0f}%",
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": f"{int(round(rss,0))}",
    })

tabla = pd.concat([fila(r.Level, r.Wall_mean, r.CPU_mean, r.RSS_mean) for _, r in agg.iterrows()], axis=1).T
tabla.to_csv(TABCSV, index=False)

latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
