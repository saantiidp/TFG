import os, pandas as pd, numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
RAW   = os.path.join(BASE, "mceliece_py_resources_raw.csv")
STATS = os.path.join(BASE, "mceliece_py_resources_stats.csv")
TABCSV= os.path.join(BASE, "tabla_mceliece_Python.csv")
TABTEX= os.path.join(BASE, "tabla_mceliece_Python.tex")
REND  = os.path.join(BASE, "mceliece_rendimiento.csv")  # si lo tienes

pd.options.display.float_format = "{:.2f}".format

if not os.path.exists(RAW):
    print("No existe mceliece_py_resources_raw.csv. Ejecuta primero medir_mceliece_python_recursos.sh")
    raise SystemExit(1)

df = pd.read_csv(RAW)
for c in ["Wall_s","CPU_pct","MaxRSS_kB"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

agg = (df.groupby("Variant", as_index=False)
         .agg(Wall_mean=("Wall_s","mean"),
              CPU_mean =("CPU_pct","mean"),
              RSS_mean =("MaxRSS_kB","mean")))

# Si tienes CSV de rendimiento con columnas de total por variante, intenta mapearlos:
rend_map = {}
if os.path.exists(REND):
    try:
        r = pd.read_csv(REND)
        # Intenta detectar columnas razonables para total (ms) y variante
        cand_total = [c for c in r.columns if "total" in c.lower() and "(ms" in c.lower()]
        cand_var   = [c for c in r.columns if "mc" in c.lower() or "mceliece" in c.lower() or "variant" in c.lower() or "nivel" in c.lower()]
        if cand_total and cand_var:
            col_t = cand_total[0]
            col_v = cand_var[0]
            tmp = r[[col_v, col_t]].rename(columns={col_v:"Variant", col_t:"Total_ms"})
            tmp["Total_s"] = pd.to_numeric(tmp["Total_ms"], errors="coerce")/1000.0
            # promedio por Variant (por si hay muchas filas)
            rend_map = tmp.groupby("Variant")["Total_s"].mean().to_dict()
    except Exception as e:
        print(f"AVISO: no pude usar {REND}: {e}")

def fila(variant, wall, cpu, rss):
    # Si hay tiempo “total” del CSV de rendimiento, úsalo; si no, el wall medido
    tsec = rend_map.get(variant, wall)
    cpu_out = "—" if np.isnan(cpu) else f"{cpu:.0f}%"
    rss_out = "—" if np.isnan(rss) else f"{int(round(rss))}"
    return {
        "LENGUAJE": "Python",
        "VERSIÓN": f"McEliece Python {variant.split('-')[-1]}",
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": f"{0 if pd.isna(tsec) else tsec:.2f}",
        "USO CPU (%)": cpu_out,
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": rss_out
    }

tabla = pd.DataFrame([fila(r.Variant, r.Wall_mean, r.CPU_mean, r.RSS_mean) for _, r in agg.iterrows()])

# Orden por tamaño de variante (numérico si se puede)
def key(v):
    import re
    m = re.search(r"(\d+)", v)
    return int(m.group(1)) if m else 10**9
tabla = tabla.sort_values(by="VERSIÓN", key=lambda s: s.map(key)).reset_index(drop=True)

agg.to_csv(STATS, index=False)
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
