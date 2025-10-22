#!/usr/bin/env bash
set -Eeuo pipefail

# Ajustables por entorno (con valores por defecto):
REPS="${REPS:-2}"
ITERS="${ITERS:-3}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
FAST="${FAST:-1}"  # 1 -> rápido (añade --fast al runner), 0 -> “real”

RAW="runs_sphincs_py_resources.csv"
: > "$RAW"
echo "Variant,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

# Runner (puedes cambiarlo si prefieres otro):
if [[ "${FAST}" == "1" ]]; then
  RUNNER='python3 sphincs_quick_runner.py {variant} --iters {iters} --fast'
else
  RUNNER='python3 sphincs_quick_runner.py {variant} --iters {iters}'
fi

variants=(sha2-128s sha2-192s sha2-256s shake-128s shake-192s shake-256s)

echo "→ Midiendo SPHINCS+ (Python) con REPS=${REPS}, ITERS=${ITERS}, TIMEOUT=${TIMEOUT_SEC}s"
echo "  Runner: ${RUNNER//\{iters\}/$ITERS}"

run_one() {
  local var="$1" i cmd out wall cpu rss
  echo "→ Variante: ${var} × ${REPS} (iters internas=${ITERS}) ..."
  for i in $(seq 1 "$REPS"); do
    cmd="${RUNNER//\{variant\}/$var}"
    cmd="${cmd//\{iters\}/$ITERS}"
    if out=$(timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -c "$cmd" 2>&1 >/dev/null); then
      # /usr/bin/time imprime a stderr: "%e,%P,%M"
      # Capturamos la ÚLTIMA línea con números, por si el runner escribe algo en stderr
      out="$(echo "$out" | tail -n1)"
      # Si ‘out’ no tiene comas, considera malformado:
      if [[ "$out" != *","* ]]; then
        echo "  • ${var} [run ${i}/${REPS}] salida malformada — salto (out='$out')"
        continue
      fi
      wall=$(echo "$out" | cut -d, -f1 | tr , .)
      cpu=$( echo "$out" | cut -d, -f2 | tr -d '%' | tr , .)
      rss=$( echo "$out" | cut -d, -f3)

      # Validaciones mínimas:
      if [[ -z "$wall" || -z "$cpu" || -z "$rss" ]]; then
        echo "  • ${var} [run ${i}/${REPS}] salida malformada — salto (out='$out')"
        continue
      fi
      printf "%s,%.2f,%.0f,%s\n" "$var" "$wall" "$cpu" "$rss" >> "$RAW"
      echo "  • ${var} [run ${i}/${REPS}] ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
    else
      echo "  • ${var} [run ${i}/${REPS}] timeout/fallo — salto"
    fi
  done
}

for v in "${variants[@]}"; do
  run_one "$v"
done

echo
echo "→ Resultados crudos: $RAW"
