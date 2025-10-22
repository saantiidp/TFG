#!/usr/bin/env bash
set -euo pipefail

RAW="bike_cs_resources_raw.csv"
: > "$RAW" && echo "Impl,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

run_and_time() {
  local exe="BIKE_C_sharp_Grafica/bin/Debug/net7.0/BIKE_C_sharp_Grafica"
  local reps="${REPS:-3}" tmo="${TIMEOUT_SEC:-60}"
  echo "→ Midiendo BIKE C# (app gráfica) × $reps con $exe ..."
  for i in $(seq 1 "$reps"); do
    # Captura stderr de time, pero manda stdout del programa a /dev/null
    if out=$(timeout "$tmo" bash -c "{ /usr/bin/time -f '%e,%P,%M' \"$exe\" >/dev/null; } 2>&1"); then
      wall=$(echo "$out" | cut -d, -f1 | tr , .)
      cpu=$( echo "$out" | cut -d, -f2 | tr -d '%' | tr , .)
      rss=$( echo "$out" | cut -d, -f3)
      printf "BIKE C#,%.2f,%.1f,%s\n" "$wall" "$cpu" "$rss" >> "$RAW"
      echo "  • iteración $i/$reps ... ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
    else
      echo "  • iteración $i/$reps ... timeout/fallo — salto"
    fi
  done
}

run_and_time

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: python3 consolidar_bike_cs.py"
