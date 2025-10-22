#!/usr/bin/env bash
set -euo pipefail

# ---------- Parámetros ----------
REPS="${REPS:-3}"
TIMEOUT_SEC="${TIMEOUT_SEC:-600}"     # sube si tarda (BIKE en Python puede ser lento)
ITERS="${ITERS:-50}"                  # iteraciones por nivel (ajústalo si quieres más precisión)
RAW="bike_py_resources_raw.csv"

# ---------- Cabecera CSV ----------
: > "$RAW"
echo "Level,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

# ---------- Preflight: python/oqs disponible ----------
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 no encontrado en PATH" >&2
  exit 1
fi

# ---------- Genera runner Python temporal ----------
RUNNER=".__bike_runner.py"
cat > "$RUNNER" <<'PY'
import sys, time
try:
    import oqs
except Exception as e:
    print("IMPORT_ERROR", str(e))
    sys.exit(12)

if len(sys.argv) < 3:
    print("USAGE_ERROR")
    sys.exit(13)

level = sys.argv[1]   # L1, L3, L5
iters = int(sys.argv[2])

name_map = {"L1":"BIKE-L1", "L3":"BIKE-L3", "L5":"BIKE-L5"}
if level not in name_map:
    print("LEVEL_ERROR")
    sys.exit(14)

alg = name_map[level]

# Bucle de KEM
for _ in range(iters):
    with oqs.KeyEncapsulation(alg) as c:
        pk = c.generate_keypair()
        with oqs.KeyEncapsulation(alg) as s:
            ct, ss_s = s.encap_secret(pk)
        ss_c = c.decap_secret(ct)
        if ss_c != ss_s:
            print("MISMATCH")
            sys.exit(15)

print("OK")
PY

measure_one() {
  local lvl="$1"
  echo "→ Midiendo BIKE Python ${lvl} × ${REPS} (ITERS=${ITERS}) ..."
  for i in $(seq 1 "$REPS"); do
    # Usamos /usr/bin/time para obtener wall/cpu/rss (kB). LC_ALL fuerza punto decimal.
    if out=$(LC_ALL=C timeout "${TIMEOUT_SEC}" /usr/bin/time -f "%e,%P,%M" \
             python3 "$RUNNER" "$lvl" "$ITERS" 2>&1 >/dev/null); then
      # Salida esperada: "segundos,%CPU,kB"
      wall=$(echo "$out" | tail -n1 | cut -d, -f1 | tr , .)
      cpu=$( echo "$out" | tail -n1 | cut -d, -f2 | tr -d '%' | tr , .)
      rss=$( echo "$out" | tail -n1 | cut -d, -f3)
      # Validación básica
      if [[ -z "$wall" || -z "$cpu" || -z "$rss" ]]; then
        echo "  • iteración $i/$REPS ... salida inválida — salto (out='$out')"
        continue
      fi
      printf "%s,%.2f,%.1f,%s\n" "$lvl" "$wall" "$cpu" "$rss" >> "$RAW"
      echo "  • iteración $i/$REPS ... ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
    else
      # Si el runner imprimió IMPORT_ERROR/LEVEL_ERROR/etc., lo vemos en $out
      if echo "$out" | grep -q "IMPORT_ERROR"; then
        echo "  • iteración $i/$REPS ... fallo: no se pudo importar 'oqs' (instala liboqs-python/liboqs)."
        break
      fi
      echo "  • iteración $i/$REPS ... timeout/fallo — salto"
    fi
  done
}

# Mide L1/L3/L5
measure_one "L1"
measure_one "L3"
measure_one "L5"

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_bike_python.py"
