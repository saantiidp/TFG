#!/usr/bin/env bash
# Mide recursos de SPHINCS+ en C# con /usr/bin/time -v
# Salida: runs_sphincs_cs_resources.csv con:
# Language,Version,Elapsed_s,CPU_pct,MaxRSS_kB,Timestamp

set -euo pipefail

ROOT_DIR="${1:-$HOME/Documentos/TFG/TFG/PC/C#/SPHINCS+/SphincsBench}"
BIN="$ROOT_DIR/bin/Release/net7.0/SphincsBench"
OUT_CSV="${2:-$ROOT_DIR/runs_sphincs_cs_resources.csv}"
N_REPS="${N_REPS:-1}"
TIMEOUT_SECS="${TIMEOUT_SECS:-1200}"   # 20 min por variante (ajusta si quieres)

# ----- Lista de variantes -----
# Si tu programa acepta --variant <v>, usa estos nombres:
VARIANTS=(
  "shake-128f" "shake-128s" "shake-192f" "shake-192s" "shake-256f" "shake-256s"
  "sha2-128f"  "sha2-128s"  "sha2-192f"  "sha2-192s"  "sha2-256f"  "sha2-256s"
)

# Si TU binario NO soporta --variant y corre todo de golpe,
# exporta USE_SUITE_ALL=1 antes de ejecutar este script.
USE_SUITE_ALL="${USE_SUITE_ALL:-0}"

# Permite personalizar el flag de variante (por si usas otro, p.ej. --level)
VAR_FLAG="${VAR_FLAG:---variant}"

command -v /usr/bin/time >/dev/null || { echo "Falta /usr/bin/time"; exit 1; }
command -v timeout >/dev/null || { echo "Falta 'timeout'"; exit 1; }
[ -x "$BIN" ] || { echo "No encuentro ejecutable: $BIN"; exit 1; }

mkdir -p "$(dirname "$OUT_CSV")"
if [ ! -f "$OUT_CSV" ]; then
  echo "Language,Version,Elapsed_s,CPU_pct,MaxRSS_kB,Timestamp" > "$OUT_CSV"
fi

parse_time_to_seconds() {
  local t="$1"
  awk -v T="$t" '
    function tosec(h,m,s){return h*3600+m*60+s}
    BEGIN{
      n=split(T,a,":");
      if(n==3){ print tosec(a[1],a[2],a[3]); }
      else if(n==2){ print tosec(0,a[1],a[2]); }
      else { print T+0; }
    }'
}

measure_cmd() {
  local label="$1"; shift
  local cmd_line=("$@")
  for rep in $(seq 1 "$N_REPS"); do
    local tfile; tfile="$(mktemp)"
    set +e
    timeout "$TIMEOUT_SECS" /usr/bin/time -v -o "$tfile" "${cmd_line[@]}" >/dev/null 2>&1
    local rc=$?
    set -e
    if [ $rc -ne 0 ]; then
      echo "WARN: $label rep#$rep acabó con código $rc (timeout u otro)." >&2
      rm -f "$tfile"
      continue
    fi
    local elapsed_raw cpu_raw rss_kb
    elapsed_raw="$(grep -F 'Elapsed (wall clock) time' "$tfile" | awk -F': ' '{print $2}' | tr -d ' ')"
    cpu_raw="$(grep -F 'Percent of CPU' "$tfile" | awk -F': ' '{print $2}' | tr -d ' %')"
    rss_kb="$(grep -F 'Maximum resident set size (kbytes)' "$tfile" | awk -F': ' '{print $2}')"
    local elapsed_s; elapsed_s="$(parse_time_to_seconds "$elapsed_raw")"
    printf "C#,SPHINCS+ %s,%s,%s,%s,%s\n" \
      "$label" "$elapsed_s" "$cpu_raw" "$rss_kb" "$(date -Iseconds)" >> "$OUT_CSV"
    rm -f "$tfile"
  done
}

if [ "$USE_SUITE_ALL" = "1" ]; then
  echo "Midiendo suite completa (una fila: ALL)..."
  measure_cmd "ALL" "$BIN"
else
  for v in "${VARIANTS[@]}"; do
    echo "Midiendo $v..."
    measure_cmd "$v" "$BIN" "$VAR_FLAG" "$v"
  done
fi

echo "Listo -> $OUT_CSV"
