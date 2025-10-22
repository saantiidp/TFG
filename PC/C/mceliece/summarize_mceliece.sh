#!/bin/bash
# Resume resultados de McEliece (ref + opt) en un CSV global
# Genera: mceliece_resumen.csv

OUT="mceliece_resumen.csv"
echo "LENGUAJE,VERSIÓN,TIEMPO TOTAL EJECUCION (segundos),USO CPU (%),MEMORIA RESIDENTE USO MÁXIMO (Kbytes)" > "$OUT"

# Función para procesar una carpeta (runs_ref o runs_opt)
procesar_dir() {
    local dir=$1
    local impl=$2   # ref u opt

    for f in "$dir"/*.rec.txt; do
        [ -e "$f" ] || continue
        # extraer datos
        elapsed=$(grep "Elapsed (wall clock) time" "$f" | awk '{print $8}')
        cpu=$(grep "Percent of CPU this job got" "$f" | awk '{print $9}')
        rss=$(grep "Maximum resident set size" "$f" | awk '{print $6}')

        # convertir elapsed a segundos (m:ss o s.ss)
        if [[ "$elapsed" =~ ([0-9]+):([0-9]+\.[0-9]+) ]]; then
            minutos=${BASH_REMATCH[1]}
            segundos=${BASH_REMATCH[2]}
            elapsed_sec=$(echo "$minutos*60+$segundos" | bc -l)
        else
            elapsed_sec=$elapsed
        fi

        # nombre de versión (ejemplo: mceliece348864.ref)
        base=$(basename "$f")
        variant=$(echo "$base" | sed -E "s/.*mceliece([0-9]+).*\.rec\.txt/\1/")
        version="McEliece: ${impl}-${variant}"

        echo "C,$version,$elapsed_sec,$cpu,$rss" >> "$OUT"
    done
}

procesar_dir runs_ref ref
procesar_dir runs_opt opt

echo "CSV generado en $OUT"

