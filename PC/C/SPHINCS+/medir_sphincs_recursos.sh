#!/usr/bin/env bash
# medir_sphincs_recursos.sh — SPHINCS+ (ref, sha2_avx2, shake_avx2)
# Robusto a locales y acepta listas en variables de entorno.

set -o errexit
set -o pipefail
# NO set -u (nounset) para permitir variables opcionales
export LC_ALL=C
export LANG=C
umask 022

RAW_CSV="sphincs_resources_raw.csv"
STATS_CSV="sphincs_resources_stats.csv"

# Defaults sensatos
: "${REPS:=3}"
: "${TIMEOUT_SEC:=120}"

: "${VARIANTS:=ref}"                      # p.ej. "ref sha2_avx2 shake_avx2"
: "${HASHES:=sha256 shake256}"            # ref puede ambos; avx2 según variante
: "${SECLEVELS:=128 192 256}"
: "${SPEEDS:=s f}"
: "${MODES:=simple}"                      # para ref: "simple robust"

# Herramientas
TIMEBIN="/usr/bin/time"
TIMEFMT="%e %P %M"   # wall(seg)  cpu(%)  rss(kB)

# Asegura encabezado CSV crudo
ensure_raw_header() {
  if [ ! -s "$RAW_CSV" ]; then
    echo "Hash,Security,Speed,Mode,Variant,Wall,CPU,RSS" > "$RAW_CSV"
  fi
}

# Devuelve ruta del binario segun combinación
bin_path() {
  local variant="$1" hash="$2" sec="$3" sp="$4" mode="$5"
  case "$variant" in
    ref)
      echo "ref/build/sphincs-${hash}-${sec}${sp}-${mode}/run"
      ;;
    sha2_avx2)
      # Solo sha256 simple
      echo "sha2_avx2/build/sphincs-sha256-${sec}${sp}-simple/run"
      ;;
    shake_avx2)
      # Solo shake256 simple
      echo "shake_avx2/build/sphincs-shake256-${sec}${sp}-simple/run"
      ;;
    *)
      echo ""
      ;;
  esac
}

# Compila si hace falta
maybe_build() {
  local dir="$1"
  if [ -d "$dir" ]; then
    echo "→ Comprobando/compilando en $dir ..."
    make -C "$dir" -s || true
  fi
}

# Ejecuta una medición
measure_one() {
  local variant="$1" hash="$2" sec="$3" sp="$4" mode="$5"
  local bin; bin="$(bin_path "$variant" "$hash" "$sec" "$sp" "$mode")"

  # Filtra combinaciones inválidas:
  if [ "$variant" = "sha2_avx2" ] && [ "$hash" != "sha256" -o "$mode" != "simple" ]; then
    return
  fi
  if [ "$variant" = "shake_avx2" ] && [ "$hash" != "shake256" -o "$mode" != "simple" ]; then
    return
  fi

  if [ ! -x "$bin" ]; then
    echo "  ⚠ No existe binario para $variant $hash ${sec}${sp}-${mode} -> $bin"
    return
  fi

  echo "→ Midiendo SPHINCS+ ${hash}-${sec}${sp}-${mode} ${variant} × ${REPS} con ${bin} ..."
  local i tmp wall cpu rss okcount=0
  tmp="$(mktemp)"

  for ((i=1;i<=REPS;i++)); do
    # Ejecuta con timeout y mide
    if timeout --preserve-status "${TIMEOUT_SEC}" ${TIMEBIN} -f "${TIMEFMT}" -o "${tmp}" "${bin}" >/dev/null 2>&1; then
      # Lee salida de time
      read -r wall cpu rss < "${tmp}" || true
      # Normaliza valores
      cpu="${cpu%\%}"
      # wall ya está con punto decimal gracias a LC_ALL=C

      # Comprobaciones básicas
      if [[ -n "$wall" && -n "$cpu" && -n "$rss" ]]; then
        printf "  • iteración %d/%d ... ok (wall=%.2fs cpu=%s%% rss=%skB)\n" "$i" "$REPS" "$wall" "$cpu" "$rss"
        echo "${hash},${sec},${sp},${mode},${variant},${wall},${cpu},${rss}" >> "$RAW_CSV"
        okcount=$((okcount+1))
      else
        echo "  • iteración ${i}/${REPS} ... fallo de medida — salto"
      fi
    else
      echo "  • iteración ${i}/${REPS} ... timeout (${TIMEOUT_SEC}s) — salto"
    fi
  done

  rm -f "${tmp}"

  if [ "$okcount" -eq 0 ]; then
    echo "WARN: no hubo medidas válidas para ${variant} ${hash} ${sec}${sp}-${mode}"
  fi
}

# Calcula medias con awk (sin depender de Python)
gen_stats() {
  awk -F, 'NR==1{next}
  {k=$1","$2","$3","$4","$5; w[k]+= $6; c[k]+=1; cp[k]+= $7; r[k]+=$8}
  END{
    print "Hash,Security,Speed,Mode,Variant,Wall_mean,CPU_mean,RSS_mean,Count";
    for (k in c){
      printf "%s,%.2f,%.1f,%.1f,%d\n", k, w[k]/c[k], cp[k]/c[k], r[k]/c[k], c[k]
    }
  }' "$RAW_CSV" | sort > "$STATS_CSV"
}

#####################################
# MAIN
#####################################
ensure_raw_header

# Construcciones “ligeras”: si el dir existe, intenta make
maybe_build "ref"
maybe_build "sha2_avx2"
maybe_build "shake_avx2"

# Bucle por combinaciones
for variant in $VARIANTS; do
  for hash in $HASHES; do
    for sec in $SECLEVELS; do
      for sp in $SPEEDS; do
        # Modo: para avx2 siempre simple; para ref lo que digas en MODES
        if [ "$variant" = "ref" ]; then
          for mode in $MODES; do
            measure_one "$variant" "$hash" "$sec" "$sp" "$mode"
          done
        else
          measure_one "$variant" "$hash" "$sec" "$sp" "simple"
        fi
      done
    done
  done
done

echo
echo "→ Resultados crudos:   $RAW_CSV"
gen_stats
echo "→ Resultados estadís.: $STATS_CSV"
echo "Sugerencias:"
echo "  - Solo ref robust (lentos): VARIANTS='ref' MODES='robust' REPS=2 TIMEOUT_SEC=300 ./medir_sphincs_recursos.sh"
echo "  - Solo SHAKE AVX2: VARIANTS='shake_avx2' HASHES='shake256' MODES='simple' REPS=3 TIMEOUT_SEC=180 ./medir_sphincs_recursos.sh"
echo "  - Reconstruir tabla memoria: python3 consolidar_sphincs_sin_repetir.py"
