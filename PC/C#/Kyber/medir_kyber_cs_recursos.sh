# ~/Documentos/TFG/TFG/PC/C#/Kyber/medir_kyber_cs_recursos.sh
#!/usr/bin/env bash
set -euo pipefail

RAW="kyber_cs_resources_raw.csv"
: > "$RAW" && echo "Impl,Wall_s,CPU_pct,MaxRSS_kB" >> "$RAW"

reps="${REPS:-3}"
tmo="${TIMEOUT_SEC:-90}"

# Rutas esperadas (ajusta si compilas Release o net8.0)
APPHOST="KyberC_sharp_Graficas/bin/Debug/net7.0/KyberC_sharp_Graficas"
DLL="${APPHOST}.dll"

# Asegura que está construido
if [[ ! -x "$APPHOST" && ! -f "$DLL" ]]; then
  echo "→ Compilando proyecto .NET (Debug)..."
  dotnet build KyberC_sharp_Graficas/KyberC_sharp_Graficas.csproj -c Debug >/dev/null
fi

# Determina comando de ejecución
if [[ -x "$APPHOST" ]]; then
  CMD=( "$APPHOST" )
elif [[ -f "$DLL" ]]; then
  CMD=( dotnet "$DLL" )
else
  echo "ERROR: no encuentro binario ni DLL en:"
  echo "  $APPHOST"
  echo "  $DLL"
  exit 1
fi

echo "→ Midiendo Kyber C# (app gráfica) × $reps con: ${CMD[*]}"

for i in $(seq 1 "$reps"); do
  # Ejecuta y captura salida de /usr/bin/time
  out="$(
    { timeout "$tmo" /usr/bin/time -f "%e,%P,%M" "${CMD[@]}" >/dev/null; } 2>&1
  )"
  rc=$?

  if [[ $rc -eq 0 && "$out" == *,* ]]; then
    wall=$(echo "$out" | cut -d, -f1 | tr , .)
    cpu=$(echo  "$out" | cut -d, -f2 | tr -d '%' | tr , .)
    rss=$(echo  "$out" | cut -d, -f3)
    printf "  • iteración %d/%d ... ok (wall=%ss cpu=%s%% rss=%skB)\n" "$i" "$reps" "$wall" "$cpu" "$rss"
    printf "Kyber C#,%.2f,%.1f,%s\n" "$wall" "$cpu" "$rss" >> "$RAW"
  else
    case $rc in
      124)  echo "  • iteración $i/$reps ... timeout ($tmo s) — salto" ;;
      126)  echo "  • iteración $i/$reps ... permiso denegado (chmod +x al apphost?) — salto" ;;
      127)  echo "  • iteración $i/$reps ... comando no encontrado (¿dotnet?) — salto" ;;
      *)    echo "  • iteración $i/$reps ... inválida — salto (rc=$rc out='$out')" ;;
    esac
  fi
done

echo
echo "→ Resultados crudos:   $RAW"
echo "Sugerencia: LC_ALL=C LC_NUMERIC=C python3 consolidar_kyber_cs.py"
