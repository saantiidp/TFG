#!/usr/bin/env bash
# Mide recursos de HQC en C# con /usr/bin/time -v
# Salida: runs_hqc_cs_resources.csv con columnas:
# Language,Version,Elapsed_s,CPU_pct,MaxRSS_kB,Timestamp

set -euo pipefail

# === Config ===
ROOT_DIR="${1:-$HOME/Documentos/TFG/TFG/PC/C#/hqc/HQC_C_sharp_Grafica}"
BIN="$ROOT_DIR/bin/Debug/net7.0/HQC_C_sharp_Grafica"
OUT_CSV="${2:-$ROOT_DIR/runs_hqc_cs_resources.csv}"
N_REPS="${N_REPS:-3}"
TIMEOUT_SECS="${TIMEOUT_SECS:-120}"

# Si tu exe necesita argumentos para escoger variante, defínelos aquí.
# Si no requiere args, deja los valores vacíos ("")
ARGS_128="${ARGS_128:-"--variant hqc128"}"
ARGS_192="${ARGS_192:-"--variant hqc192"}"
ARGS_256="${ARGS_256:-"--variant hqc256"}"

# === Checks mínimos ===
command -v /usr/bin/time >/dev/null || { echo "Falta /usr/bin/time"; exit 1; }
command -v timeout >/dev/null || { echo "Falta 'timeout'"; exit 1; }
[ -x "$BIN" ] || { echo "No encuentro ejecutable: $BIN"; exit 1; }

mkdir -p "$(dirname "$OUT_CSV")"
if [ ! -f "$OUT_CSV" ]; then
  echo "Language,Version,Elapsed_s,CPU_pct,MaxRSS_kB,Timestamp" > "$OUT_CSV"
fi

parse_time_to_seconds() {
  # Convierte "h:mm:ss" o "m:ss" o "s" a segundos decimales
  local t="$1"
  # Ejemplos posibles: 0:03.21  12.34  1:02:03
  awk -v T="$t" '
    function tosec(h,m,s){return h*3600+m*60+s}
    BEGIN{
      n=split(T,a,":");
      if(n==3){ print tosec(a[1],a[2],a[3]); }
      else if(n==2){ print tosec(0,a[1],a[2]); }
      else { print T+0; }
    }'
}

measure_one() {
  local variant="$1"
  local args="$2"
  for rep in $(seq 1 "$N_REPS"); do
    local tfile; tfile="$(mktemp)"
    # Ejecuta con timeout y captura métricas de /usr/bin/time -v
    set +e
    timeout "$TIMEOUT_SECS" /usr/bin/time -v -o "$tfile" "$BIN" $args >/dev/null 2>&1
    local rc=$?
    set -e
    if [ $rc -ne 0 ]; then
      echo "WARN: $variant rep#$rep terminó con código $rc (timeout u otro). Continúo..." >&2
      rm -f "$tfile"
      continue
    fi

    # Extrae métricas
    local elapsed_raw cpu_raw rss_kb
    elapsed_raw="$(grep -F 'Elapsed (wall clock) time' "$tfile" | awk -F': ' '{print $2}' | tr -d ' ')"
    cpu_raw="$(grep -F 'Percent of CPU' "$tfile" | awk -F': ' '{print $2}' | tr -d ' %')"
    rss_kb="$(grep -F 'Maximum resident set size (kbytes)' "$tfile" | awk -F': ' '{print $2}')"

    # Normaliza tiempo a segundos
    local elapsed_s
    elapsed_s="$(parse_time_to_seconds "$elapsed_raw")"

    # Escribe CSV
    printf "C#,HQC-%s,%s,%s,%s,%s\n" \
      "$variant" "$elapsed_s" "$cpu_raw" "$rss_kb" "$(date -Iseconds)" >> "$OUT_CSV"

    rm -f "$tfile"
  done
}

echo "Midiendo HQC-128..."
measure_one "128" "$ARGS_128"

echo "Midiendo HQC-192..."
measure_one "192" "$ARGS_192"

echo "Midiendo HQC-256..."
measure_one "256" "$ARGS_256"

echo "Listo -> $OUT_CSV"
