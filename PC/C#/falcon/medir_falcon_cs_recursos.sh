#!/usr/bin/env bash
set -euo pipefail

RAW="falcon_cs_resources_raw.csv"
: > "$RAW" && echo "Impl,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

APP="FalconC_sharp_Grafica/bin/Debug/net7.0/FalconC_sharp_Grafica"
REPS="${REPS:-3}"
TMO="${TIMEOUT_SEC:-180}"

if [ ! -x "$APP" ]; then
  echo "ERROR: no encuentro $APP (compila en Debug primero)"
  exit 1
fi

echo "→ Warm-up .NET (sin medir) ..."
timeout "$TMO" "$APP" >/dev/null 2>&1 || true

echo "→ Midiendo Falcon C# (app gráfica) × $REPS con $APP ..."
for i in $(seq 1 "$REPS"); do
  # GNU time: %e (s), %P (CPU%), %M (kB)
  out="$(timeout "$TMO" /usr/bin/time -f "%e,%P,%M" "$APP" 2>&1 >/dev/null || true)"
  if [ -n "$out" ] && [[ "$out" == *,*,* ]]; then
    wall="$(echo "$out" | cut -d, -f1 | tr , .)"
    cpu="$(echo  "$out" | cut -d, -f2 | tr -d '%' | tr , .)"
    rss="$(echo  "$out" | cut -d, -f3)"
    printf "Falcon C#,%.2f,%.1f,%s\n" "$wall" "$cpu" "$rss" >> "$RAW"
    echo "  • iteración $i/$REPS ... ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
  else
    echo "  • iteración $i/$REPS ... inválida/timeout — salto"
  fi
done

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_falcon_cs.py"
