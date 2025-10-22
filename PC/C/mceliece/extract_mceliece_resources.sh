#!/usr/bin/env bash
set -euo pipefail

# Dónde buscar logs
ROOT="${1:-.}"

# Salidas
OUT_REF="mceliece_resources_ref.csv"
OUT_OPT="mceliece_resources_opt.csv"

# Encabezados
echo "Variant,Impl,Run,Elapsed_sec,MaxRSS_kb,CPU_pct,File" > "$OUT_REF"
echo "Variant,Impl,Run,Elapsed_sec,MaxRSS_kb,CPU_pct,File" > "$OUT_OPT"

# Función: convierte h:mm:ss o m:ss(.cc) a segundos (float)
to_seconds() {
  local t="$1"
  # ejemplos: 0:00.01  3:12  1:02:03.45
  IFS=':' read -r -a A <<< "$t"
  if [[ ${#A[@]} -eq 3 ]]; then
    # h m s(.cc)
    python3 - <<PY
h=${A[0]}; m=${A[1]}; s="${A[2]}"
print(float(h)*3600 + float(m)*60 + float(s))
PY
  else
    # m s(.cc)
    python3 - <<PY
m=${A[0]}; s="${A[1]}"
print(float(m)*60 + float(s))
PY
  fi
}

# Recorre runs_ref/logs y runs_opt/logs
while IFS= read -r -d '' f; do
  # impl por carpeta
  if [[ "$f" == *"/runs_ref/"* ]]; then impl="ref"; out="$OUT_REF"
  else impl="opt"; out="$OUT_OPT"; fi

  # intento de variante desde el nombre de archivo (mcelieceNNN...f?)
  variant="unknown"
  if [[ "$f" =~ mceliece([0-9]+f?) ]]; then
    variant="${BASH_REMATCH[1]}"
  elif [[ "$f" =~ ([34][0-9]{5}f?|[46][0-9]{5}f?|[6789][0-9]{6}f?) ]]; then
    # patrón de números largos por si no trae el prefijo
    variant="${BASH_REMATCH[1]}"
  fi

  # run id (opcional) si aparece rN en el nombre
  run=""; if [[ "$f" =~ _r([0-9]+) ]]; then run="${BASH_REMATCH[1]}"; fi
  [[ -z "$run" ]] && run=""

  # Extraer 3 campos de /usr/bin/time -v
  # permitimos tab inicial
  elapsed_raw="$(grep -m1 -E $'\t?'"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):" "$f" | awk -F': ' '{print $2}' || true)"
  maxrss="$(grep -m1 -E $'\t?'"Maximum resident set size \(kbytes\):" "$f" | awk -F': ' '{print $2}' || true)"
  cpu_pct="$(grep -m1 -E $'\t?'"Percent of CPU this job got:" "$f" | awk -F': ' '{print $2}' | tr -d '%' || true)"

  # Normaliza vacíos
  [[ -z "$maxrss" ]] && maxrss=""
  [[ -z "$cpu_pct" ]] && cpu_pct=""

  # Convierte tiempo a segundos (si existe)
  elapsed_sec=""
  if [[ -n "$elapsed_raw" ]]; then
    # quita espacios
    elapsed_raw="$(echo "$elapsed_raw" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    elapsed_sec="$(to_seconds "$elapsed_raw" 2>/dev/null || echo "")"
  fi

  # Escribe línea
  echo "${variant},${impl},${run},${elapsed_sec},${maxrss},${cpu_pct},${f}" >> "$out"
done < <(find "$ROOT/runs_ref/logs" "$ROOT/runs_opt/logs" -type f -name "*.txt" -print0 2>/dev/null)

echo "OK. CSVs generados:"
echo "  - $OUT_REF"
echo "  - $OUT_OPT"
