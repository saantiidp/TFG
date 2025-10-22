#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# ===== Config por defecto (puedes sobreescribir con variables de entorno) =====
: "${VARIANTS:=ref sha2_avx2 shake_avx2}"     # qué implementaciones medir
: "${HASHES:=sha256 shake256}"                 # hash families
: "${SECLEVELS:=128 192 256}"                  # niveles de seguridad
: "${SPEEDS:=s f}"                             # 's' (small) y 'f' (fast)
: "${MODES:=simple robust}"                    # 'simple' y 'robust' (solo 'ref' tiene robust)
: "${REPS:=3}"                                 # repeticiones por combinación
: "${TIMEOUT_SEC:=120}"                         # timeout por iteración (segundos)

RAW_CSV="sphincs_resources_raw.csv"
STATS_CSV="sphincs_resources_stats.csv"

# ===== Utilidades =====
require_time() {
  if ! /usr/bin/time -v true >/dev/null 2>&1; then
    echo "ERROR: necesito /usr/bin/time con -v" >&2
    exit 1
  fi
}
secs_to_float() { # Convierte 1:23.45 -> 83.45
  local t="$1"
  if [[ "$t" == *:* ]]; then
    local m=${t%:*}
    local s=${t#*:}
    awk -v m="$m" -v s="$s" 'BEGIN{printf "%.2f", m*60 + s}'
  else
    awk -v s="$t" 'BEGIN{printf "%.2f", s}'
  fi
}

ensure_built() {
  local variant="$1"
  case "$variant" in
    ref)        (cd ref && make -s) ;;
    sha2_avx2)  (cd sha2_avx2 && make -s) ;;
    shake_avx2) (cd shake_avx2 && make -s) ;;
    *) echo "Variant desconocida: $variant" >&2; exit 1 ;;
  esac
}

# Devuelve la ruta al binario run o cadena vacía si no aplica esa combinación
bin_path_for() {
  local variant="$1" hash="$2" level="$3" speed="$4" mode="$5"

  case "$variant" in
    ref)
      # ref soporta sha256 y shake256; y modos simple/robust
      # Formato: ref/build/sphincs-${hash}-${level}${speed}-${mode}/run
      echo "ref/build/sphincs-${hash}-${level}${speed}-${mode}/run"
      ;;
    sha2_avx2)
      # Solo hash=sha256 y mode=simple
      [[ "$hash" == "sha256" && "$mode" == "simple" ]] || { echo ""; return; }
      # sha2_avx2/build/sphincs-sha256-${level}${speed}-simple/run
      echo "sha2_avx2/build/sphincs-sha256-${level}${speed}-simple/run"
      ;;
    shake_avx2)
      # Solo hash=shake256 y mode=simple
      [[ "$hash" == "shake256" && "$mode" == "simple" ]] || { echo ""; return; }
      # shake_avx2/build/sphincs-shake256-${level}${speed}-simple/run
      echo "shake_avx2/build/sphincs-shake256-${level}${speed}-simple/run"
      ;;
    *)
      echo ""; return ;;
  esac
}

# ===== Preparación =====
require_time

# encabezado RAW si no existe
if [[ ! -s "$RAW_CSV" ]]; then
  echo "Hash,Security,Speed,Mode,Variant,Wall_seconds,CPU_percent,MaxRSS_kB" > "$RAW_CSV"
fi

# ===== Medición =====
for variant in $VARIANTS; do
  echo "→ Comprobando/compilando en $variant ..."
  ensure_built "$variant"

  for hash in $HASHES; do
    for level in $SECLEVELS; do
      for speed in $SPEEDS; do
        for mode in $MODES; do
          bin="$(bin_path_for "$variant" "$hash" "$level" "$speed" "$mode")"
          [[ -n "$bin" ]] || continue
          if [[ ! -x "$bin" ]]; then
            echo "  ⚠ No existe binario para $variant $hash ${level}${speed}-$mode -> $bin"
            continue
          fi

          echo "→ Midiendo SPHINCS+ ${hash}-${level}${speed}-${mode} ${variant} × ${REPS} con ${bin} ..."
          ok_runs=0
          wall_list=""
          cpu_list=""
          rss_list=""

          for ((i=1; i<=REPS; i++)); do
            # Ejecuta 1 genfirma/verify en el bin (su benchmark interno); medimos el proceso entero
            # Si tus binarios aceptan args para n-iter, ajusta aquí. Si no, mediremos su "run" tal cual.
            set +e
            otmp=$(mktemp)
            etmp=$(mktemp)
            timeout "$TIMEOUT_SEC" /usr/bin/time -v "$bin" >"$otmp" 2>"$etmp"
            code=$?
            set -e

            if [[ $code -eq 124 ]]; then
              echo "  • iteración $i/$REPS ... timeout (${TIMEOUT_SEC}s) — salto"
              rm -f "$otmp" "$etmp"
              continue
            elif [[ $code -ne 0 ]]; then
              echo "  • iteración $i/$REPS ... fallo (code=$code) — salto"
              rm -f "$otmp" "$etmp"
              continue
            fi

            # Parseo de /usr/bin/time -v
            wall_raw=$(grep -F "Elapsed (wall clock) time" "$etmp" | awk -F': ' '{print $2}' | tr -d ' ')
            cpu_raw=$(grep -F "Percent of CPU this job got" "$etmp" | awk -F': ' '{print $2}' | tr -d ' %')
            rss_raw=$(grep -F "Maximum resident set size" "$etmp" | awk -F': ' '{print $2}' | tr -dc '0-9')

            wall_sec=$(secs_to_float "${wall_raw//s/}")
            cpu_pct="${cpu_raw:-0}"
            rss_kb="${rss_raw:-0}"

            echo "  • iteración $i/$REPS ... ok (wall=${wall_sec}s cpu=${cpu_pct}% rss=${rss_kb}kB)"

            echo "${hash},${level},${speed},${mode},${variant},${wall_sec},${cpu_pct},${rss_kb}" >> "$RAW_CSV"
            ok_runs=$((ok_runs+1))
            wall_list+="$wall_sec"$'\n'
            cpu_list+="$cpu_pct"$'\n'
            rss_list+="$rss_kb"$'\n'

            rm -f "$otmp" "$etmp"
          done

          if [[ $ok_runs -eq 0 ]]; then
            echo "WARN: no hubo medidas válidas para ${variant} ${hash} ${level}${speed}-${mode}"
            continue
          else
            # Calcula medias y desv std con awk
            wall_mean=$(awk '{s+=$1} END{printf "%.2f", (NR?s/NR:0)}' <<<"$wall_list")
            wall_std=$(awk '{x+=$1;y+=$1*$1} END{if(NR>1){m=x/NR;printf "%.2f", sqrt((y/NR)-(m*m))} else {printf "0.00"}}' <<<"$wall_list")
            cpu_mean=$(awk '{s+=$1} END{printf "%.1f", (NR?s/NR:0)}' <<<"$cpu_list")
            cpu_std=$(awk '{x+=$1;y+=$1*$1} END{if(NR>1){m=x/NR;printf "%.1f", sqrt((y/NR)-(m*m))} else {printf "0.0"}}' <<<"$cpu_list")
            rss_mean=$(awk '{s+=$1} END{printf "%.1f", (NR?s/NR:0)}' <<<"$rss_list")
            rss_std=$(awk '{x+=$1;y+=$1*$1} END{if(NR>1){m=x/NR;printf "%.1f", sqrt((y/NR)-(m*m))} else {printf "0.0"}}' <<<"$rss_list")

            printf "✓ OK %s %s-%s-%s: medias guardadas.\n" "$variant" "$hash" "${level}${speed}" "$mode"

            # Añade/actualiza STATS: reconstruimos al final; aquí solo dejamos constancia si quieres
          fi
        done
      done
    done
  done
done

# ===== Reconstruir STATS a partir de RAW (promedios/desv por combinación) =====
# Notas:
# - Agrupamos por (Hash,Security,Speed,Mode,Variant)
# - Wall_seconds en mean/std, CPU_percent mean/std, MaxRSS_kB mean/std
# - Usamos awk como "group by" simple.
awk -F, '
BEGIN{
  OFS=",";
  print "Hash,Security,Speed,Mode,Variant,Wall_mean,Wall_std,CPU_mean,CPU_std,RSS_mean,RSS_std"
}
NR==1{next} # skip header RAW
{
  key=$1 FS $2 FS $3 FS $4 FS $5
  n[key]++
  wsum[key]+=$6; wsum2[key]+=$6*$6
  csum[key]+=$7; csum2[key]+=$7*$7
  rsum[key]+=$8; rsum2[key]+=$8*$8
}
END{
  for (key in n){
    mW = wsum[key]/n[key]
    sW = (n[key]>1)? sqrt(wsum2[key]/n[key] - mW*mW) : 0
    mC = csum[key]/n[key]
    sC = (n[key]>1)? sqrt(csum2[key]/n[key] - mC*mC) : 0
    mR = rsum[key]/n[key]
    sR = (n[key]>1)? sqrt(rsum2[key]/n[key] - mR*mR) : 0
    printf "%s,%.2f,%.2f,%.1f,%.1f\n", key, mW, sW, mC, sC, mR, sR
  }
}
' "$RAW_CSV" > "$STATS_CSV"

echo
echo "→ Resultados crudos:   $RAW_CSV"
echo "→ Resultados estadís.: $STATS_CSV"
echo "Sugerencias:"
echo "  - Solo ref robust (lentos): VARIANTS='ref' MODES='robust' REPS=2 TIMEOUT_SEC=300 ./medir_sphincs_recursos.sh"
echo "  - Solo SHAKE AVX2: VARIANTS='shake_avx2' HASHES='shake256' MODES='simple' REPS=3 TIMEOUT_SEC=180 ./medir_sphincs_recursos.sh"
echo "  - Reconstruir tabla memoria: python3 consolidar_sphincs_sin_repetir.py"
