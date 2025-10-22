#!/usr/bin/env python3
import pandas as pd, re, sys

RAW = "sphincs_resources_raw.csv"
OUT = "sphincs_resources_stats.csv"

def read_raw(path):
    # lee como texto, limpia BOM, y quita líneas basura (fallo, timeout, etc.)
    lines = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            if re.search(r'(fallo|timeout|No existe binario|WARN)', ln):
                continue
            # descarta líneas con campos < 7 (esperamos 8: Hash,Security,Speed,Mode,Variant,Wall,CPU,RSS)
            if ln.count(",") < 7:
                continue
            lines.append(ln)
    if not lines:
        raise SystemExit("No hay líneas válidas en el raw CSV.")
    from io import StringIO
    return pd.read_csv(StringIO("".join(lines)))

def normalize_cols(df):
    # normaliza nombres posibles
    cols = {c.lower(): c for c in df.columns}
    def pick(*options):
        for o in options:
            if o in cols: return cols[o]
        return None
    col_hash     = pick("hash")
    col_sec      = pick("security","seclevel","securitylevel","sec")
    col_speed    = pick("speed","variant_speed")
    col_mode     = pick("mode")
    col_variant  = pick("variant","impl","implementation")
    col_wall     = pick("wall","time","elapsed","wall_s","wall_sec")
    col_cpu      = pick("cpu","cpu_%","cpu_percent")
    col_rss      = pick("rss","rss_kb","memory","resident","rss_mean_kb")

    need = [col_hash,col_sec,col_speed,col_mode,col_variant,col_wall,col_cpu,col_rss]
    if any(x is None for x in need):
        miss = ["Hash","Security","Speed","Mode","Variant","Wall","CPU","RSS"]
        have = dict(zip(miss, need))
        raise SystemExit(f"Faltan columnas esperadas.\nMapeo detectado: {have}\nEncabezado real: {list(df.columns)}")

    # renombra
    df = df.rename(columns={
        col_hash:"Hash", col_sec:"Security", col_speed:"Speed", col_mode:"Mode",
        col_variant:"Variant", col_wall:"Wall", col_cpu:"CPU", col_rss:"RSS"
    })

    # coerción numérica (punto decimal), elimina filas no convertibles
    for c in ["Security","Wall","CPU","RSS"]:
        df[c] = (df[c].astype(str)
                    .str.replace(",", ".", regex=False)
                    .str.replace("%","", regex=False)
                 )
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Security","Wall","CPU","RSS"])
    # Security como int
    df["Security"] = df["Security"].astype(int)
    # normaliza strings
    for c in ["Hash","Speed","Mode","Variant"]:
        df[c] = df[c].astype(str).str.strip().str.lower()
    return df

def main():
    raw = read_raw(RAW)
    raw = normalize_cols(raw)

    # agrupado y estadísticos
    grp_cols = ["Hash","Security","Speed","Mode","Variant"]
    stats = (raw
             .groupby(grp_cols, as_index=False)
             .agg(Wall_mean=("Wall","mean"), Wall_std=("Wall","std"),
                  CPU_mean=("CPU","mean"),   CPU_std=("CPU","std"),
                  RSS_mean=("RSS","mean"),   RSS_std=("RSS","std"))
             )
    # redondeos agradables
    stats[["Wall_mean","Wall_std"]] = stats[["Wall_mean","Wall_std"]].round(2)
    stats[["CPU_mean","CPU_std"]]   = stats[["CPU_mean","CPU_std"]].round(1)
    stats[["RSS_mean","RSS_std"]]   = stats[["RSS_mean","RSS_std"]].round(0)

    stats.to_csv(OUT, index=False)
    print(f"OK: escrito {OUT}")

if __name__ == "__main__":
    main()
