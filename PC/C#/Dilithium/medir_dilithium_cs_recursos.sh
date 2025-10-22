#!/usr/bin/env bash
set -euo pipefail

RAW="dilithium_cs_resources_raw.csv"
REPS="${REPS:-3}"
TIMEOUT_SEC="${TIMEOUT_SEC:-60}"

# Ruta del ejecutable .NET (puedes sobreescribir con EXE=/ruta/al/binario)
EXE="${EXE:-DilithiumC_sharp_Graficas/bin/Debug/net7.0/DilithiumC_sharp_Graficas}"

# Cabecera
: > "$RAW"
echo "Level,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

measure_one() {
  local lvl="$1"
  local args="$2"     # argumentos para seleccionar nivel si procede (opcional)
  echo "→ Midiendo Dilithium C# (nivel $lvl) × $REPS con $EXE $args ..."

  for i in $(seq 1 "$REPS"); do
    # Captura SOLO el stderr (donde escribe /usr/bin/time) y manda stdout a /dev/null.
    # OJO: el orden de redirecciones importa: 2>&1 >/dev/null capturará stderr.
    if out=$( ( timeout "$TIMEOUT_SEC" /usr/bin/time -f "%e,%P,%M" "$EXE" $args ) 2>&1 >/dev/null ); then
      wall=$(echo "$out" | cut -d, -f1 | tr , .)
      cpu=$( echo "$out" | cut -d, -f2 | tr -d '%' | tr , .)
      rss=$( echo "$out" | cut -d, -f3)

      # Validación básica
      if [[ -n "${wall:-}" && -n "${cpu:-}" && -n "${rss:-}" ]]; then
        printf "  • iteración %d/%d ... ok (wall=%ss cpu=%s%% rss=%skB)\n" "$i" "$REPS" "$wall" "$cpu" "$rss"
        printf "%s,%.2f,%.1f,%s\n" "$lvl" "$wall" "$cpu" "$rss" >> "$RAW"
      else
        echo "  • iteración inválida — salto (out='${out}')"
      fi
    else
      echo "  • iteración inválida — salto (out='${out:-}')"
    fi
  done
}

# Si tu ejecutable permite pasar el nivel como argumento, ajusta las líneas “args”.
# Si no, repite la ejecución 3 veces y asignaremos el mismo 'lvl' a todos.
measure_one "2" ""   # p.ej. "" o "2" según tu Program.cs
measure_one "3" ""   # idem
measure_one "5" ""   # idem

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_dilithium_cs.py"
