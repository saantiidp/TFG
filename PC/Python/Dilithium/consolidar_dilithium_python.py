import os, pandas as pd, numpy as np

BASE   = os.path.dirname(os.path.abspath(__file__))
RAW    = os.path.join(BASE, "dilithium_py_resources_raw.csv")
STATS  = os.path.join(BASE, "dilithium_py_resources_stats.csv")
TABCSV = os.path.join(BASE, "tabla_dilithium_Python.csv")
TABTEX = os.path.join(BASE, "tabla_dilithium_Python.tex")

if not os.path.exists(RAW):
    print("No existe dilithium_py_resources_raw.csv. Ejecuta primero el script de medida.")
    raise SystemExit(1)

df = pd.read_csv(RAW)
for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# Agrega promedios por nivel/kind
have_rows = len(df.dropna(subset=["Wall_s","CPU_pct","MaxRSS_kB"])) > 0
if have_rows:
    agg = (df.groupby(["Level","MsgKind"], as_index=False)
             .agg(Wall_mean=("Wall_s","mean"),
                  CPU_mean =("CPU_pct","mean"),
                  RSS_mean =("MaxRSS_kB","mean")))
    agg.to_csv(STATS, index=False)
else:
    # Sin datos válidos, deja un CSV vacío pero con encabezado
    pd.DataFrame(columns=["Level","MsgKind","Wall_mean","CPU_mean","RSS_mean"]).to_csv(STATS, index=False)

def fila(level:int, kind:str, wall=None, cpu=None, rss=None):
    def fmt(v, suf=""):
        if v is None or np.isnan(v):
            return "—"
        return f"{v:.2f}{suf}" if suf=="" else f"{v:.0f}{suf}"
    return pd.Series({
        "LENGUAJE":"Python",
        "VERSIÓN":f"Dilithium Python {level} (mensaje {kind})",
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": fmt(wall, ""),
        "USO CPU (%)": fmt(cpu, "%"),
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": "—" if rss is None or np.isnan(rss) else f"{int(round(rss))}"
    })

filas = []
for level in [2,3,5]:
    for kind in ["corto","largo"]:
        if have_rows:
            r = (agg[(agg["Level"]==level)&(agg["MsgKind"]==kind)]
                   .reset_index(drop=True))
            if len(r):
                filas.append(fila(level, kind, r.loc[0,"Wall_mean"], r.loc[0,"CPU_mean"], r.loc[0,"RSS_mean"]))
            else:
                filas.append(fila(level, kind))
        else:
            filas.append(fila(level, kind))

tabla = pd.DataFrame(filas)
tabla.to_csv(TABCSV, index=False)

latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

if have_rows:
    print(f"OK: escrito {STATS}")
else:
    print("OK: escrito (sin datos válidos en raw)")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
