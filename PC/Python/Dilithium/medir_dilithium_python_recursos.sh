#!/usr/bin/env bash
set -Eeuo pipefail

# ---- Parámetros configurables por entorno -------------------------------
REPS="${REPS:-1}"
TIMEOUT_SEC="${TIMEOUT_SEC:-900}"
MSG_SHORT_B="${MSG_SHORT_B:-32}"
MSG_LONG_B="${MSG_LONG_B:-1048576}"

# Si tienes un runner real, ponlo por env:
#   PY_RUNNER=dilithium_rend.py
# El script lo invocará como:  python3 "$PY_RUNNER" <level> <mlen>
PY_RUNNER="${PY_RUNNER:-}"

RAW="dilithium_py_resources_raw.csv"
: > "$RAW"
echo "Level,MsgKind,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

run_case() {
  local level="$1" kind="$2" mlen="$3" i out wall cpu rss

  echo "  Nivel ML-DSA-$level ($kind, ${mlen}B), × $REPS"
  for i in $(seq 1 "$REPS"); do
    # Comando a ejecutar (silenciado a stdout; nos quedamos con stderr de 'time')
    if [[ -n "$PY_RUNNER" ]]; then
      CMD=(python3 "$PY_RUNNER" "$level" "$mlen")
    else
      # Dummy: reemplázalo por tu ejecución real si lo deseas
      CMD=(python3 - "$level" "$mlen")
    fi

    if [[ -z "$PY_RUNNER" ]]; then
      # Runner simulado (para que no dé 0.00 si aún no tienes el real)
      out_run=$(cat <<'PY'
import sys, time
level=int(sys.argv[1]); mlen=int(sys.argv[2])
time.sleep(0.15 + 0.08*level)  # <- Sustituye por tu ejecución real
PY
)
      # Ejecuta con time capturando STDERR y enviando STDOUT a /dev/null
      if out=$(timeout "$TIMEOUT_SEC" bash -lc "{ /usr/bin/time -f '%e,%P,%M' python3 - \"$level\" \"$mlen\" 1>/dev/null; } 2>&1" <<<"$out_run"); then
        :
      else
        echo "    • iter $i/$REPS timeout/fallo — salto"
        continue
      fi
    else
      # Runner real
      if out=$(timeout "$TIMEOUT_SEC" bash -lc "{ /usr/bin/time -f '%e,%P,%M' \"${CMD[@]}\" 1>/dev/null; } 2>&1"); then
        :
      else
        echo "    • iter $i/$REPS timeout/fallo — salto"
        continue
      fi
    fi

    # 'out' trae algo tipo:   0.53,101%,11840
    wall=$(echo "$out" | cut -d, -f1 | tr , .)
    cpu=$( echo "$out" | cut -d, -f2 | tr -d '%' | tr , .)
    rss=$( echo "$out" | cut -d, -f3)

    # Validación mínima
    if [[ -z "$wall" || -z "$cpu" || -z "$rss" ]]; then
      echo "    • iter $i/$REPS salida malformada — salto (out='$out')"
      continue
    fi

    printf "%s,%s,%.2f,%.0f,%s\n" "$level" "$kind" "$wall" "$cpu" "$rss" >> "$RAW"
    echo "    • iter $i/$REPS ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
  done
}

echo "→ Midiendo Dilithium Python con mensajes {corto=${MSG_SHORT_B}B, largo=${MSG_LONG_B}B}…"
for lvl in 2 3 5; do
  run_case "$lvl" "corto" "$MSG_SHORT_B"
  run_case "$lvl" "largo" "$MSG_LONG_B"
done

echo
echo "→ Resultados crudos: $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_dilithium_python.py"
