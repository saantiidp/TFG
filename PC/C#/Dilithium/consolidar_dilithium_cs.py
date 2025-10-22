import os
import pandas as pd
import numpy as np

pd.options.display.float_format = '{:.2f}'.format

RAW = "dilithium_cs_resources_raw.csv"
STATS = "dilithium_cs_resources_stats.csv"
TABCSV = "tabla_dilithium_Csharp.csv"
TABTEX = "tabla_dilithium_Csharp.tex"

# CSVs de rendimiento (opcional)
CSV_PERF = {
    "2": "DilithiumC_sharp_Graficas/Dilithium2_performance2.csv",
    "3": "DilithiumC_sharp_Graficas/Dilithium3_performance2.csv",
    "5": "DilithiumC_sharp_Graficas/Dilithium5_performance2.csv",
}

# ---------- Cargar recursos (Wall/CPU/RSS) ----------
if not os.path.exists(RAW):
    print("No existe dilithium_cs_resources_raw.csv. Ejecuta primero medir_dilithium_cs_recursos.sh")
    raise SystemExit(1)

df = pd.read_csv(RAW)
# Asegura tipos
for c in ["Wall_s", "CPU_pct", "MaxRSS_kB"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Stats por nivel
agg = (df.groupby("Level", as_index=False)
         .agg(Wall_mean=("Wall_s", "mean"),
              Wall_std =("Wall_s", "std"),
              CPU_mean =("CPU_pct", "mean"),
              CPU_std  =("CPU_pct", "std"),
              RSS_mean =("MaxRSS_kB", "mean"),
              RSS_std  =("MaxRSS_kB", "std")))

# Orden bonito 2,3,5
order = {"2": 0, "3": 1, "5": 2}
agg["__ord"] = agg["Level"].astype(str).map(order).fillna(9)
agg = agg.sort_values(["__ord", "Level"]).drop(columns="__ord")

# Guarda stats
agg.to_csv(STATS, index=False)

# ---------- Leer CSVs de rendimiento (si existen) ----------
def leer_total_ms(path):
    if not os.path.exists(path):
        return None
    try:
        dfp = pd.read_csv(path)
    except Exception as e:
        print(f"AVISO: problema leyendo {path}: {e}")
        return None

    cols = [c.strip().lower() for c in dfp.columns]
    # 1) Columna directa
    for cand in ["total (ms)", "total_time_ms", "total time (ms)"]:
        if cand in dfp.columns:
            try:
                vals = pd.to_numeric(dfp[cand], errors="coerce").dropna()
                if len(vals):
                    return float(vals.mean())
            except Exception:
                pass

    # 2) Heurística: suma de keygen+enc+dec
    alias = {
        "keygen": ["keygen (ms)", "keygen ms", "keygen_time_ms", "keygen time (ms)"],
        "enc":    ["enc (ms)", "enc ms", "enc_time_ms", "encrypt (ms)", "encryption (ms)"],
        "dec":    ["dec (ms)", "dec ms", "dec_time_ms", "decrypt (ms)", "decryption (ms)"],
    }
    def pick_first(names):
        for n in names:
            if n in dfp.columns:
                return n
        return None

    ckg = pick_first(alias["keygen"])
    cen = pick_first(alias["enc"])
    cde = pick_first(alias["dec"])

    if ckg and cen and cde:
        try:
            s = (pd.to_numeric(dfp[ckg], errors="coerce")
               + pd.to_numeric(dfp[cen], errors="coerce")
               + pd.to_numeric(dfp[cde], errors="coerce")).dropna()
            if len(s):
                return float(s.mean())
        except Exception:
            pass

    print(f"AVISO: sin columna de total reconocible en {path}")
    return None

tot_ms = {lvl: leer_total_ms(path) for lvl, path in CSV_PERF.items()}

# ---------- Construir tabla final ----------
def fila(level, wall_s, cpu_pct, rss_kb, total_ms):
    # Tiempo en segundos: si hay total_ms, úsalo (ms -> s); si no, usa wall_s
    if total_ms is not None and np.isfinite(total_ms):
        tsec = total_ms / 1000.0
    else:
        tsec = wall_s if np.isfinite(wall_s) else np.nan

    cpu_txt = f"{cpu_pct:.0f}%" if np.isfinite(cpu_pct) else "—"
    rss_txt = f"{int(round(rss_kb))}" if np.isfinite(rss_kb) else "—"

    return pd.Series({
        "LENGUAJE": "C#",
        "VERSIÓN": f"Dilithium C# {level}",
        "TIEMPO TOTAL DE\nEJECUCIÓN (segundos)": f"{tsec:.2f}" if np.isfinite(tsec) else "—",
        "USO CPU (%)": cpu_txt,
        "MEMORIA RESIDENTE USO\nMÁXIMO (kbytes)": rss_txt,
    })

filas = []
for _, r in agg.iterrows():
    lvl = str(r.Level)
    filas.append(
        fila(
            lvl,
            r.Wall_mean,
            r.CPU_mean,
            r.RSS_mean,
            tot_ms.get(lvl)
        )
    )

tabla = pd.DataFrame(filas)

# Exporta
tabla.to_csv(TABCSV, index=False)
latex = tabla.to_latex(index=False, escape=False, column_format="llrrr", longtable=False)
with open(TABTEX, "w", encoding="utf-8") as f:
    f.write(latex)

print(f"OK: escrito {STATS}")
print(f"OK: escrito {TABCSV}")
print(f"OK: escrito {TABTEX}")
