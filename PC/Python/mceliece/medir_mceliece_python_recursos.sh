#!/usr/bin/env bash
# Medición de recursos para McEliece (Python, vía liboqs u otro runner)
# Repite N veces externamente y (opcional) con iteraciones internas en tu runner.

set -Eeuo pipefail

# ---------- Parámetros ----------
REPS="${REPS:-2}"            # repeticiones externas por variante
BATCH_ITERS="${BATCH_ITERS:-1}"  # iteraciones internas por ejecución (si tu runner lo soporta)
TIMEOUT_SEC="${TIMEOUT_SEC:-1800}"  # timeout por ejecución (seg)

# Comando de ejecución (plantilla). Use {variant} y {iters} como placeholders.
# Si no defines PY_CMD fuera, por defecto usa mceliece_run_once.py
PY_CMD="${PY_CMD:-python3 mceliece_run_once.py {variant}}"

RAW="mceliece_py_resources_raw.csv"
: > "$RAW"
echo "Variant,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

# Lista de variantes a medir (ajústala si quieres un subconjunto)
variants=(
  "Classic-McEliece-348864"
  "Classic-McEliece-348864f"
  "Classic-McEliece-460896"
  "Classic-McEliece-460896f"
  "Classic-McEliece-6688128"
  "Classic-McEliece-6688128f"
  "Classic-McEliece-6960119"
  "Classic-McEliece-6960119f"
  "Classic-McEliece-8192128"
  "Classic-McEliece-8192128f"
)

echo "→ Midiendo McEliece (Python) con REPS=${REPS}, BATCH_ITERS=${BATCH_ITERS}, TIMEOUT=${TIMEOUT_SEC}s"
echo "  Runner: ${PY_CMD}"

run_one() {
  local variant="$1" iters="$2" run_idx="$3"
  # Sustituye placeholders de la plantilla de comando
  local cmd_template="$PY_CMD"
  local cmd="${cmd_template//\{variant\}/$variant}"
  cmd="${cmd//\{iters\}/$iters}"

  # Ejecuta con medición y timeout
  # /usr/bin/time -> %e (tiempo real s) , %P (CPU %), %M (Max RSS kB)
  local out=""
  if out=$(timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -lc "$cmd" 1>/dev/null 2>&1); then
    # Normaliza
    local wall cpu rss
    wall=$(echo "$out" | cut -d, -f1 | tr , .)
    cpu=$(echo  "$out" | cut -d, -f2 | tr -d '%' | tr , .)
    rss=$(echo  "$out" | cut -d, -f3)
    printf "%s,%.2f,%.0f,%s\n" "$variant" "$wall" "$cpu" "$rss" >> "$RAW"
    echo "  ✓ ${variant} [run ${run_idx}/${REPS}]  wall=${wall}s  cpu=${cpu}%  rss=${rss}kB"
  else
    echo "  • ${variant} [run ${run_idx}/${REPS}]  timeout/fallo — salto"
  fi
}

for v in "${variants[@]}"; do
  echo "→ Variante: $v × ${REPS} (iters internas=${BATCH_ITERS}) ..."
  for r in $(seq 1 "$REPS"); do
    run_one "$v" "$BATCH_ITERS" "$r"
  done
done

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_mceliece_python.py"
