#!/usr/bin/env bash
set -Eeuo pipefail

# ---------- Parámetros ----------
REPS="${REPS:-3}"                 # repeticiones externas por nivel
TIMEOUT_SEC="${TIMEOUT_SEC:-600}" # timeout por ejecución (seg)
RAW="${RAW:-bike_java_resources_raw.csv}"

# Comando Java; usa {level} como placeholder del nivel (128/192/256)
# Ejemplos:
#   export JAVA_CMD="./run.sh {level}"
#   export JAVA_CMD="java -cp bin:lib/* Main {level}"
JAVA_CMD="${JAVA_CMD:-./run.sh {level}}"

levels=(128 192 256)

# ---------- Preparación ----------
export LC_ALL=C LC_NUMERIC=C
: > "$RAW"
echo "Level,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

# Función para ejecutar una vez y volcar métricas
run_one() {
  local cmd="$1"
  # Captura: wall(s), CPU(%), MaxRSS(kB)
  #  -f "%e,%P,%M" -> segundos, porcentaje, kB
  timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -c "$cmd" 2>&1 | tr -d $'\r'
}

echo "→ Midiendo BIKE Java con REPS=$REPS, TIMEOUT=${TIMEOUT_SEC}s"
echo "  Runner: $JAVA_CMD"

for lvl in "${levels[@]}"; do
  echo "→ Nivel $lvl × $REPS …"
  for i in $(seq 1 "$REPS"); do
    # Sustituye {level} en el comando
    cmd="${JAVA_CMD//\{level\}/$lvl}"
    if out="$(run_one "$cmd")"; then
      wall="$(echo "$out" | awk -F, 'NR==1{gsub(",",".",$1);print $1}')"
      cpu="$( echo "$out" | awk -F, 'NR==1{gsub("%","",$2);gsub(",",".",$2);print $2}')"
      rss="$( echo "$out" | awk -F, 'NR==1{print $3}')"

      # Validación básica
      if [[ -n "$wall" && -n "$cpu" && -n "$rss" ]]; then
        printf "%s,%.2f,%.0f,%s\n" "$lvl" "$wall" "$cpu" "$rss" >> "$RAW"
        echo "  • iter $i/$REPS ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
      else
        echo "  • iter $i/$REPS salida malformada — salto (out='$out')"
      fi
    else
      echo "  • iter $i/$REPS timeout/fallo — salto"
    fi
  done
done

echo
echo "→ Resultados crudos: $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_bike_java.py"
