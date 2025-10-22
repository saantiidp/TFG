#!/usr/bin/env bash
set -euo pipefail

IMPL="${1:-opt}"          # opt | ref
REPS="${2:-5}"            # repeticiones externas
CPU_PIN="${3:-0}"         # 1 para fijar CPU 0
INNER_OPT=200
INNER_REF=20
: "${TIMEOUT:=300s}"      # se puede exportar antes, p.ej. TIMEOUT=600s

if [[ "$IMPL" == "opt" ]]; then
  INNER="$INNER_OPT"
  VARIANTS=(348864f 348864 460896f 460896 6688128f 6688128 6960119f 6960119 8192128f 8192128)
  BIN_PREFIX="bench_"
  BIN_SUFFIX="_avx"
  LOGDIR="runs_opt/logs"
elif [[ "$IMPL" == "ref" ]]; then
  INNER="$INNER_REF"
  VARIANTS=(348864f 348864 460896f 460896 6688128f 6688128 6960119f 6960119 8192128f 8192128)
  BIN_PREFIX="bench_"
  BIN_SUFFIX="_ref"
  LOGDIR="runs_ref/logs"
else
  echo "Impl debe ser 'opt' o 'ref'"; exit 1
fi

mkdir -p "$LOGDIR"

echo ">> Impl=$IMPL  Reps=$REPS  CPU=$CPU_PIN  INNER=$INNER  TIMEOUT=$TIMEOUT"
echo ">> Guardando logs en $LOGDIR/"

run_one() {
  local variant="$1" i
  echo ">>> Variante $variant ($IMPL) con $REPS repeticiones externas"
  for ((i=1; i<=REPS; i++)); do
    local OUT="$LOGDIR/${variant}_${IMPL}_r${i}.out.txt"
    local REC="$LOGDIR/${variant}_${IMPL}_r${i}.rec.txt"
    echo "  -> Run $i/$REPS: $OUT"

    local BIN="build/${BIN_PREFIX}${variant}${BIN_SUFFIX}"
    if [[ ! -x "$BIN" ]]; then
      echo "     (Aviso) No existe binario $BIN; intento compilar rápido…"
      make -s "$BIN" || true
    fi

    CMD="./${BIN} ${INNER} ${IMPL} ${variant}"
    if [[ "$CPU_PIN" == "1" ]]; then
      CMD="taskset -c 0 ${CMD}"
    fi

    # Ejecuta con timeout; stdout -> OUT, time -v y stderr -> REC
    if ! timeout "$TIMEOUT" /usr/bin/time -v bash -c "$CMD" >"$OUT" 2>"$REC"; then
      echo "     (Aviso) Timeout alcanzado en $variant r$i. Log guardado."
    fi
  done
}

for v in "${VARIANTS[@]}"; do
  run_one "$v"
done

echo "OK. Logs en $LOGDIR/"
echo "Ahora resume con:  ./summarize_resources.sh $IMPL"
