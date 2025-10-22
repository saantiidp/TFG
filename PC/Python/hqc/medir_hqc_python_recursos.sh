#!/usr/bin/env bash
set -Eeuo pipefail

# Ajustes
REPS="${REPS:-2}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
PY_CMD="${PY_CMD:-python3 hqc_rendGrafico.py}"  # <-- tu runner real

RAW="hqc_py_resources_raw.csv"
: > "$RAW" && echo "Level,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

measure_one() {
  local level="$1" cmd="$2" i out wall cpu rss ok=0
  echo "→ Midiendo HQC Python $level × $REPS con: $cmd"
  for i in $(seq 1 "$REPS"); do
    # Capturamos STDERR de /usr/bin/time (donde imprime las métricas)
    if out=$({ timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -lc "$cmd" >/dev/null; } 2>&1); then
      # Suele salir solo una línea "e,P,M"
      out="$(echo "$out" | tail -n1)"
      wall="$(echo "$out" | cut -d, -f1 | tr , .)"
      cpu="$(echo  "$out" | cut -d, -f2 | tr -d '%' | tr , .)"
      rss="$(echo  "$out" | cut -d, -f3)"
      # Verifica que están los 3 campos
      if [[ -n "${wall:-}" && -n "${cpu:-}" && -n "${rss:-}" ]]; then
        printf "%s,%.2f,%.0f,%s\n" "$level" "$wall" "$cpu" "$rss" >> "$RAW"
        echo "  • iter $i/$REPS ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
        ok=1
      fi
    fi
    [[ $ok -eq 1 ]] || echo "  • iter $i/$REPS inválida/timeout — salto (out='${out:-}')"
  done
}

# Niveles: L128, L192, L256
measure_one "L128" "$PY_CMD"
measure_one "L192" "$PY_CMD"
measure_one "L256" "$PY_CMD"

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_hqc_python.py"
