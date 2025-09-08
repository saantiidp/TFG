import glob
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

# Orden consistente para que todas las figuras salgan igual
ORDER = [
    "mceliece348864","mceliece348864f",
    "mceliece460896","mceliece460896f",
    "mceliece6688128","mceliece6688128f",
    "mceliece6960119","mceliece6960119f",
    "mceliece8192128","mceliece8192128f",
]

METRICS = ["Tiempo_KeyGen_ms","Tiempo_Encaps_ms","Tiempo_Decaps_ms","Tiempo_Total_ms"]

def file_to_label(fp: str) -> str:
    stem = Path(fp).stem
    return stem.replace("_iter","")

def parse_csv_decimal_pairs(path: str) -> pd.DataFrame:
    """
    Formato esperado por línea:
    Iteracion,Version, K_entera,K_dec, E_entera,E_dec, D_entera,D_dec, T_entera,T_dec [, basura...]
    - No tocamos el CSV.
    - Siempre unimos cada par como 'entera.dec' (punto como decimal) -> float
    """
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    # quitar cabecera si existe
    start = 1 if lines and lines[0].lower().startswith("iteracion") else 0

    for ln in lines[start:]:
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) < 10:
            # si no llega a 10, no podemos reconstruir 4 números de dos tokens cada uno
            # intentamos detectar si viene 'limpio' (ya con punto decimal y 6 columnas)
            if len(parts) == 6:
                try:
                    # Reintento con pandas normal (poco probable en tu caso)
                    df = pd.read_csv(path)
                    return df
                except Exception:
                    pass
            raise ValueError(f"Fila con longitud inesperada en {path}:\n{ln}")

        # Tomamos exactamente los 10 primeros campos relevantes
        parts = parts[:10]

        # Campos fijos
        try:
            iteracion = int(parts[0])
        except ValueError:
            # por si accidentalmente la línea es otra cabecera
            continue
        version = parts[1]

        # Reconstrucción de K/E/D/T desde pares
        # índices: (2,3)->K, (4,5)->E, (6,7)->D, (8,9)->T
        nums = []
        for i in (2,4,6,8):
            entero = parts[i].replace(" ", "").replace(".", "")
            frac   = parts[i+1].replace(" ", "").replace(".", "")
            # une como 'entero.frac'
            val = float(f"{entero}.{frac}")
            nums.append(val)

        keygen, encaps, decaps, total = nums
        rows.append([iteracion, version, keygen, encaps, decaps, total])

    if not rows:
        raise ValueError(f"Sin filas válidas en {path}")

    return pd.DataFrame(rows, columns=[
        "Iteracion","Version","Tiempo_KeyGen_ms","Tiempo_Encaps_ms","Tiempo_Decaps_ms","Tiempo_Total_ms"
    ])

# Recolectar y ordenar ficheros
files = sorted(glob.glob("mceliece*_iter.csv"))
order_idx = {name: i for i, name in enumerate(ORDER)}
files.sort(key=lambda f: order_idx.get(file_to_label(f), 999))

# Generar boxplots
for metric in METRICS:
    data, labels = [], []
    for f in files:
        df = parse_csv_decimal_pairs(f)
        if metric not in df.columns:
            print(f"[AVISO] Falta '{metric}' en {f}")
            continue
        data.append(pd.to_numeric(df[metric], errors="coerce"))
        labels.append(file_to_label(f))

    if not data:
        print(f"[AVISO] Sin datos para {metric}")
        continue

    plt.figure(figsize=(11,6))
    plt.boxplot(data, labels=labels, patch_artist=True)
    plt.title(f"McEliece - {metric}")
    plt.ylabel("Tiempo (ms)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    out_png = f"mceliece_boxplot_{metric}.png"
    plt.savefig(out_png, dpi=120)
    plt.close()
    print(f"✅ Guardado: {out_png}")
