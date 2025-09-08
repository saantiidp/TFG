import glob
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

# Orden consistente de variantes
ORDER = [
    "mceliece348864","mceliece348864f",
    "mceliece460896","mceliece460896f",
    "mceliece6688128","mceliece6688128f",
    "mceliece6960119","mceliece6960119f",
    "mceliece8192128","mceliece8192128f",
]

METRICS = ["Tiempo_KeyGen_ms","Tiempo_Encaps_ms","Tiempo_Decaps_ms","Tiempo_Total_ms"]

def file_to_label(fp: str) -> str:
    """
    mceliece348864f_java_performance.csv -> mceliece348864f
    """
    stem = Path(fp).stem
    # quita sufijo _java_performance si está
    return stem.replace("_java_performance", "")

def parse_java_csv_decimal_pairs(path: str) -> pd.DataFrame:
    """
    Lee líneas con este patrón:
    Iteracion,Version, K_entera,K_dec, E_entera,E_dec, D_entera,D_dec, T_entera,T_dec [, ...]
    Reconstruye floats como 'entera.dec'.
    Si alguna fila viniera ya 'bien' (6 columnas con punto decimal), no aplica aquí porque el script es específico
    para el formato con parejas; si necesitas que auto-detecte ambos, puedo darte una variante mixta.
    """
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    # Quita cabecera si existe
    start = 1 if lines and lines[0].lower().startswith("iteracion") else 0

    for ln in lines[start:]:
        parts = [p.strip() for p in ln.split(",")]

        # Deben existir al menos 10 tokens (2 fijos + 8 para 4 números en pares)
        if len(parts) < 10:
            raise ValueError(f"Fila inesperada en '{path}':\n{ln}")

        # Tomamos estrictamente los 10 primeros: Iter,Version, (K.e,K.d),(E.e,E.d),(D.e,D.d),(T.e,T.d)
        parts = parts[:10]

        # Iteración puede fallar si se coló otra cabecera accidentalmente
        try:
            iteracion = int(parts[0])
        except ValueError:
            continue

        version = parts[1]

        # Reconstrucción de K/E/D/T
        vals = []
        for i in (2, 4, 6, 8):
            entero = parts[i].replace(" ", "").replace(".", "")
            frac   = parts[i+1].replace(" ", "").replace(".", "")
            vals.append(float(f"{entero}.{frac}"))
        keygen, encaps, decaps, total = vals

        rows.append([iteracion, version, keygen, encaps, decaps, total])

    if not rows:
        raise ValueError(f"Sin filas válidas en '{path}'")

    return pd.DataFrame(rows, columns=[
        "Iteracion","Version","Tiempo_KeyGen_ms","Tiempo_Encaps_ms","Tiempo_Decaps_ms","Tiempo_Total_ms"
    ])

# Buscar y ordenar ficheros Java
files = sorted(glob.glob("mceliece*_java_performance.csv"))
order_idx = {name: i for i, name in enumerate(ORDER)}
files.sort(key=lambda f: order_idx.get(file_to_label(f), 999))

# Generar boxplots por métrica
for metric in METRICS:
    data, labels = [], []
    for f in files:
        df = parse_java_csv_decimal_pairs(f)
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
    plt.title(f"McEliece (Java) - {metric}")
    plt.ylabel("Tiempo (ms)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    out_png = f"mceliece_java_boxplot_{metric}.png"
    plt.savefig(out_png, dpi=120)
    plt.close()
    print(f"✅ Guardado: {out_png}")
