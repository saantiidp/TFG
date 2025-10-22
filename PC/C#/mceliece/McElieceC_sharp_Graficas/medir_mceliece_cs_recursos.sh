#!/usr/bin/env bash
set -euo pipefail

RAW="mceliece_cs_resources_raw.csv"
REPS="${REPS:-3}"
TIMEOUT_SEC="${TIMEOUT_SEC:-600}"   # sube si tu app tarda más

# Dónde podría estar el ejecutable
CANDIDATES=(
  "./bin/Debug/net7.0/McElieceC_sharp_Graficas"
  "./McElieceC_sharp_Graficas/bin/Debug/net7.0/McElieceC_sharp_Graficas"
)
EXE=""
for c in "${CANDIDATES[@]}"; do
  [[ -x "$c" ]] && EXE="$c" && break
done

if [[ -z "$EXE" ]]; then
  echo "⚠ No encuentro ejecutable. Compilando con: dotnet build -c Debug"
  dotnet build -c Debug >/dev/null
  for c in "${CANDIDATES[@]}"; do
    [[ -x "$c" ]] && EXE="$c" && break
  done
fi

if [[ -z "$EXE" ]]; then
  echo "ERROR: sigue sin existir el ejecutable. Revisa el proyecto."
  exit 1
fi

# Cabecera del CSV
: > "$RAW"
echo "Impl,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

run_once() {
  local mode="$1"
  case "$mode" in
    plain)      timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" "$EXE" >/dev/null 2>time.out || return 1 ;;
    nullstdin)  timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -c "< /dev/null \"$EXE\"" >/dev/null 2>time.out || return 1 ;;
    newline)    timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" bash -c "printf '\n' | \"$EXE\"" >/dev/null 2>time.out || return 1 ;;
    *) return 1 ;;
  esac
  # time(1) escribe en stderr → time.out
  [[ -s time.out ]] || return 1
  awk -F, '
    BEGIN{OFS=","}
    {
      gsub(/%/,"",$2);
      # fuerza punto decimal si hubiera coma (según locale)
      gsub(",",".",$1); gsub(",",".",$2);
      print $1,$2,$3
    }' time.out
}

echo "→ Midiendo McEliece C# (app gráfica) × $REPS con $EXE ..."
for i in $(seq 1 "$REPS"); do
  out=""
  for mode in plain nullstdin newline; do
    if out="$(run_once "$mode" 2>/dev/null)"; then
      break
    fi
  done
  if [[ -n "$out" ]]; then
    wall=$(echo "$out" | cut -d, -f1)
    cpu=$( echo "$out" | cut -d, -f2)
    rss=$( echo "$out" | cut -d, -f3)
    printf "McEliece C# app,%.2f,%.1f,%s\n" "$wall" "$cpu" "$rss" >> "$RAW"
    echo "  • iteración $i/$REPS ... ok (wall=${wall}s cpu=${cpu}% rss=${rss}kB)"
  else
    echo "  • iteración $i/$REPS ... inválida/timeout — salto"
  fi
done

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_mceliece_cs.py"
