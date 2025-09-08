import pandas as pd
import matplotlib.pyplot as plt

# Cargar los datos
df_128 = pd.read_csv("bench_hqc.csv")
df_256 = pd.read_csv("bench_hqc_256.csv")

# Calcular tiempo total (keygen + enc + dec)
total_128 = df_128["keygen_ms"] + df_128["enc_ms"] + df_128["dec_ms"]
total_256 = df_256["keygen_ms"] + df_256["enc_ms"] + df_256["dec_ms"]

# Crear boxplot
plt.boxplot([total_128, total_256], labels=["HQC-128", "HQC-256"])
plt.title("Comparación de tiempo total (ms) - HQC")
plt.ylabel("Tiempo total (ms)")
plt.grid(True)
plt.tight_layout()
plt.show()
