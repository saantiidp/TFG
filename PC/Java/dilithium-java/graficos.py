import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.image as mpimg
import numpy as np

# Archivos
agg_file = "Dilithium_Performance_Aggregated.csv"
iter_file = "Dilithium_Performance_Iteration.csv"
img_file = "javadilithiumç.png"  # o javadilithium.png si usas la anterior

# Cargar CSVs
df_agg = pd.read_csv(agg_file)
df_iter = pd.read_csv(iter_file)

# --- PARTE 1: Boxplot de datos por iteración con outliers filtrados ---

# Calcular tiempo total
df_iter["T_total_peq"] = df_iter["KeyGen (ms)"] + df_iter["Sign Pequeño (ms)"] + df_iter["Verify Pequeño (ms)"]
df_iter["T_total_grande"] = df_iter["KeyGen (ms)"] + df_iter["Sign Grande (ms)"] + df_iter["Verify Grande (ms)"]

# Pasar a formato largo
df_box = pd.melt(
    df_iter,
    id_vars=["Versión"],
    value_vars=["T_total_peq", "T_total_grande"],
    var_name="Tipo Mensaje",
    value_name="Tiempo Total (ms)"
)

df_box["Tipo Mensaje"] = df_box["Tipo Mensaje"].replace({
    "T_total_peq": "Pequeño",
    "T_total_grande": "Grande"
})
df_box["Versión_Tipo"] = df_box["Versión"] + " " + df_box["Tipo Mensaje"]

# Filtrar outliers extremos
limite_superior = np.percentile(df_box["Tiempo Total (ms)"], 99)
df_box_filtrado = df_box[df_box["Tiempo Total (ms)"] < limite_superior]

# Boxplot
plt.figure(figsize=(12, 6))
sns.boxplot(data=df_box_filtrado, x="Versión_Tipo", y="Tiempo Total (ms)", palette="Set2")
plt.title("Comparación de Tiempos Totales de Ejecución entre Versiones de Dilithium (sin outliers extremos)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("boxplot_dilithium_java_filtrado.png")
plt.show()

# --- PARTE 2: Mostrar imagen de referencia ---

img = mpimg.imread(img_file)
plt.figure(figsize=(8, 5))
plt.imshow(img)
plt.axis('off')
plt.title("Imagen de Referencia: Resultados Java Dilithium")
plt.tight_layout()
plt.show()
