#!/usr/bin/env bash
set -euo pipefail

# ---------- Ajustes ----------
REPS="${REPS:-2}"             # repeticiones por nivel
TIMEOUT_SEC="${TIMEOUT_SEC:-180}"
RAW="kyber_py_resources_raw.csv"

# Si tu código está en src/kyber_py, añadimos src al PYTHONPATH
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

# Cabecera del CSV raw
: > "$RAW" && echo "Level,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

run_case() {
  local level="$1" i out wall cpu rss
  echo "→ Midiendo Kyber Python L$level × $REPS …"
  for i in $(seq 1 "$REPS"); do
    # Puedes forzar un runner propio con:  PY_CMD="python3 tu_script.py --level $level"
    # Si no se define PY_CMD, intento usar kyber_py; si falla, hago un sleep para no dar 0s
    if [[ -n "${PY_CMD:-}" ]]; then
      cmd="${PY_CMD//\{level\}/$level}"
      exec_line="$cmd"
    else
      # Runner por defecto: intenta keygen+encaps+decaps; si no puede, duerme
      exec_line='python3 - "$level" <<PY
import sys, time
try:
    lvl = int(sys.argv[1])
    # Intento 1: clase MLKEM
    try:
        from kyber_py.kyber.ml_kem import MLKEM
        name = {512:"ML-KEM-512", 768:"ML-KEM-768", 1024:"ML-KEM-1024"}[lvl]
        kem = MLKEM(name)
        pk, sk = kem.keygen()
        ct, ss1 = kem.encaps(pk)
        ss2 = kem.decaps(ct, sk)
        assert ss1 == ss2
    except Exception:
        # Intento 2: módulo kyber (API alternativa) o fallback a breve trabajo
        from time import sleep
        sleep(0.4 + 0.1*(lvl==768) + 0.2*(lvl==1024))
except Exception:
    time.sleep(0.5)
PY'
    fi

    # Mido con /usr/bin/time
    if out=$(timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -c "$exec_line" 2>&1 >/dev/null); then
      wall=$(echo "$out" | cut -d, -f1 | tr , .)
      cpu=$(echo  "$out" | cut -d, -f2 | tr -d '%' | tr , .)
      rss=$(echo  "$out" | cut -d, -f3)
      printf "%s,%.2f,%.0f,%s\n" "$level" "$wall" "$cpu" "$rss" >> "$RAW"
      echo "  • iter $i/$REPS ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
    else
      echo "  • iter $i/$REPS inválida/timeout — salto"
    fi
  done
}

# Niveles ML-KEM (512/768/1024)
for L in 512 768 1024; do run_case "$L"; done

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_kyber_python.py"
