# medir_bike_recursos.sh
#!/usr/bin/env bash
set -euo pipefail

RAW="bike_resources_raw.csv"
: > "$RAW" && echo "Impl,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

run_and_time() {
  local dir="$1" name="$2" reps="${REPS:-3}" tmo="${TIMEOUT_SEC:-120}"
  local exe="$dir/test_bike"
  make -C "$dir" -j >/dev/null
  echo "→ Midiendo $name × $reps con $exe ..."
  for i in $(seq 1 "$reps"); do
    # Capturamos el stderr de /usr/bin/time (donde imprime) → stdout del bloque
    if out=$(timeout "$tmo" bash -c "{ /usr/bin/time -f '%e,%P,%M' \"$exe\" >/dev/null; } 2>&1"); then
      wall=$(echo "$out" | cut -d, -f1 | tr , .)
      cpu=$( echo "$out" | cut -d, -f2 | tr -d '%' | tr , .)
      rss=$( echo "$out" | cut -d, -f3)
      printf "%s,%.2f,%.1f,%s\n" "$name" "$wall" "$cpu" "$rss" >> "$RAW"
      echo "  • iteración $i/$reps ... ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
    else
      echo "  • iteración $i/$reps ... timeout/fallo — salto"
    fi
  done
}

run_and_time "Reference_Implementation" "BIKE ref"
run_and_time "Optimized_Implementation" "BIKE avx2"

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: python3 consolidar_bike.py"
