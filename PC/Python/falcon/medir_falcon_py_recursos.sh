#!/usr/bin/env bash
set -Eeuo pipefail

# Parámetros por entorno
REPS="${REPS:-2}"          # repeticiones externas
ITERS="${ITERS:-3}"        # iteraciones internas por run (las hace el runner Python)
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
FAST="${FAST:-1}"          # 1 = “rápido” (runner hace trabajo cortito), 0 = “real”
RAW="runs_falcon_py_resources.csv"

# Runner Python (NO lo toques si ya tienes falcon_quick_runner.py):
# Usará --fast si FAST=1
RUNNER_BASE="python3 falcon_quick_runner.py {level} --iters {iters}"
if [[ "$FAST" == "1" ]]; then
  RUNNER_BASE="$RUNNER_BASE --fast"
fi

: > "$RAW" && echo "Level,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

echo "→ Midiendo Falcon (Python) con REPS=$REPS, ITERS=$ITERS, TIMEOUT=${TIMEOUT_SEC}s"
echo "  Runner: $RUNNER_BASE"

measure_one() {
  local level="$1" i=1
  echo "→ Nivel L$level × $REPS (iters internas=$ITERS) ..."
  while [[ $i -le $REPS ]]; do
    # Sustituye {level} / {iters}
    cmd="${RUNNER_BASE/\{level\}/$level}"
    cmd="${cmd/\{iters\}/$ITERS}"
    if out=$(timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -lc "$cmd" 2>&1 >/dev/null); then
      wall=$(echo "$out" | cut -d, -f1 | tr , .)
      cpu=$(echo  "$out" | cut -d, -f2 | tr -d '%' | tr , .)
      rss=$(echo  "$out" | cut -d, -f3)
      printf "%s,%.2f,%.0f,%s\n" "$level" "$wall" "$cpu" "$rss" >> "$RAW"
      echo "  • L$level [run $i/$REPS] ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
    else
      echo "  • L$level [run $i/$REPS] timeout/fallo — salto"
    fi
    i=$((i+1))
  done
}

measure_one 512
measure_one 1024

echo
echo "→ Resultados crudos: $RAW"
