#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   ./summarize_resources.sh auto
#   ./summarize_resources.sh ref
#   ./summarize_resources.sh opt

IMPL="${1:-auto}"   # auto|ref|opt
LOGDIR="runs_${IMPL}/logs"
OUTCSV="runs_${IMPL}/mceliece_resources_${IMPL}.csv"

if [[ ! -d "$LOGDIR" ]]; then
  echo "No existe ${LOGDIR}. Ejecuta antes: ./run_mceliece_with_resources.sh ${IMPL}"
  exit 1
fi

printf "impl,variant,exe_name,run_id,elapsed_s,cpu_percent,max_rss_kb,file\n" > "$OUTCSV"

to_seconds() {
  # Convierte "m:ss.xx" o "h:mm:ss.xx" a segundos con decimales
  local t="$1"
  awk -F: '{
    if (NF==2) { m=$1; s=$2; printf "%.3f", (m*60)+s }
    else if (NF==3) { h=$1; m=$2; s=$3; printf "%.3f", (h*3600)+(m*60)+s }
    else { print $1 }
  }' <<< "$t"
}

# Limpia el nombre base del ejecutable a partir del nombre del .rec.txt
clean_exe_name() {
  local b="$1"
  # 1) quita sufijo timestamp + _rN + .rec.txt
  b="$(echo "$b" | sed -E 's/_20[0-9]{6}_[0-9]{6}_r[0-9]+\.rec\.txt$//')"
  # 2) si por algún motivo quedó ".out.txt_*" delante de .rec.txt, elimínalo
  b="$(echo "$b" | sed -E 's/_out\.txt(_(auto|ref|opt)_[0-9]+)?$//')"
  # 3) quita posibles repeticiones finales de _auto/_ref/_opt + numeritos residuales
  b="$(echo "$b" | sed -E 's/_(auto|ref|opt)_[0-9]+$//')"
  echo "$b"
}

impl_from_name() {
  local b="$1"
  if [[ "$b" =~ ref|Reference ]]; then echo "ref"; return; fi
  if [[ "$b" =~ opt|Optimized|avx2 ]]; then echo "opt"; return; fi
  echo "$IMPL"
}

variant_from_name() {
  # Solo aceptamos variantes REALES de Classic McEliece
  local b="$1"
  case "$b" in
    *348864f*)  echo "348864f" ;;
    *348864*)   echo "348864"  ;;
    *460896f*)  echo "460896f" ;;
    *460896*)   echo "460896"  ;;
    *6688128f*) echo "6688128f" ;;
    *6688128*)  echo "6688128"  ;;
    *6960119f*) echo "6960119f" ;;
    *6960119*)  echo "6960119"  ;;
    *8192128f*) echo "8192128f" ;;
    *8192128*)  echo "8192128"  ;;
    *)          echo "unknown"  ;;
  esac
}

shopt -s nullglob
for f in "${LOGDIR}"/*.rec.txt; do
  b="$(basename "$f")"
  exe_name="$(clean_exe_name "$b")"
  run_id="$(echo "$b" | sed -n 's/.*_r\([0-9]\+\)\.rec\.txt/\1/p')"
  [[ -z "${run_id}" ]] && run_id=1

  variant="$(variant_from_name "$exe_name")"
  impl_det="$(impl_from_name "$exe_name")"

  # Extrae métricas del /usr/bin/time -v
  elapsed_raw="$(grep -m1 'Elapsed (wall clock) time' "$f" | awk -F': ' '{print $2}' | xargs)"
  cpu_pct="$(grep   -m1 'Percent of CPU'          "$f" | awk -F': ' '{print $2}' | tr -d ' %')"
  rss_kb="$(grep    -m1 'Maximum resident set size' "$f" | awk -F': ' '{print $2}' | xargs)"

  # Normaliza elapsed y filtra runs inútiles
  elapsed_s="$(to_seconds "$elapsed_raw")"
  # Ignora runs con elapsed extremadamente bajo (ruido / helpers)
  awk -v e="$elapsed_s" 'BEGIN{exit !(e<0.001)}' && continue

  printf "%s,%s,%s,%s,%s,%s,%s,%s\n" \
    "$impl_det" "$variant" "$exe_name" "$run_id" \
    "$elapsed_s" "$cpu_pct" "$rss_kb" "$b" >> "$OUTCSV"
done

echo "CSV generado: $OUTCSV"
echo
echo "== Resumen por variante (impl=${IMPL}) =="

awk -F, '
  BEGIN {
    printf "%-10s %-6s %-6s %-12s %-12s %-12s %-12s\n",
           "Variant","n","Impl","Elapsed_mean","Elapsed_sd","MaxRSS_mean","MaxRSS_sd"
  }
  NR>1 {
    key=$2"|" $1; v=$2; impl=$1; e=$5+0; r=$7+0
    n[key]++; se[key]+=e; sse[key]+=e*e; sr[key]+=r; ssr[key]+=r*r; impls[key]=impl
  }
  END {
    PROCINFO["sorted_in"]="@ind_str_asc"
    for (k in n) {
      split(k, a, /\|/); v=a[1]; impl=impls[k]
      me=se[k]/n[k]; sde=sqrt((sse[k]/n[k]) - me*me)
      mr=sr[k]/n[k]; sdr=sqrt((ssr[k]/n[k]) - mr*mr)
      printf "%-10s %-6d %-6s %-12.6f %-12.6f %-12.0f %-12.0f\n",
             v, n[k], impl, me, sde, mr, sdr
    }
  }
' "$OUTCSV"
