#!/usr/bin/env bash
set -euo pipefail
csv="runs_opt/mceliece_resources_opt.csv"

# Detecta índices por nombre de columna (tolerante):
hdr=$(head -n1 "$csv")
idx() { awk -v col="$1" -F, '
  NR==1{for(i=1;i<=NF;i++) if($i==col) {print i; exit}}' <<<"$hdr"; }

i_variant=$(idx Variant)
i_elapsed=$(idx Elapsed_mean)
i_rss=$(idx MaxRSS_mean)
i_cpu=$(idx CPU_mean) || true

# Encabezado en español
printf "LENGUAJE,VERSION,TIEMPO TOTAL EJECUCIÓN (segundos),USO CPU (%%),MEMORIA RESIDENTE USO MÁXIMO (kbytes)\n"

# Filas
awk -F, -v iv="$i_variant" -v ie="$i_elapsed" -v ir="$i_rss" -v ic="${i_cpu:-0}" '
  NR==1 { next }
  {
    lang="C"
    ver=$iv
    t=$ie
    cpu=(ic>0 && ic<=NF && $ic!="" ? $ic : "")
    rss=$ir
    # Formateos
    if (t!="")  printf("%s,%s,%.2f,", lang, ver, t);
    else        printf("%s,%s,,",      lang, ver);
    if (cpu!="") printf("%.2f%%,", cpu+0); else printf(",");
    if (rss!="") printf("%d\n", rss+0); else printf("\n");
  }' "$csv" | column -s, -t
