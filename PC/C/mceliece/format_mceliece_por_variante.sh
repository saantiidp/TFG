#!/usr/bin/env bash
set -euo pipefail
csv="${1:-runs_opt/mceliece_resources_opt.csv}"

# AWK que:
# 1) Lee el header y localiza índices de columnas (flexible a nombres)
# 2) Suma y cuenta por Variant para calcular medias y sd
awk -F, '
function trim(s){ sub(/^ +| +$/,"",s); sub(/^"|"$/,"",s); return s }
function tolow(s){ gsub(/"/,"",s); return tolower(s) }
NR==1{
  for(i=1;i<=NF;i++){
    h=tolow($i)
    gsub(/ /,"",h)
    # Mapeo la primera coincidencia útil
    if(!vidx && h ~ /(^|,)variant($|,)/)              vidx=i
    if(!eidx && (h ~ /elapsed/ || h ~ /time/))        eidx=i
    if(!cidx && (h ~ /cpu/))                          cidx=i
    if(!ridx && (h ~ /maxrss|rss/))                   ridx=i
  }
  if(!vidx || !eidx) { print "ERROR: no encuentro columnas Variant/Elapsed en header"; exit 1 }
  next
}
NR>1{
  v = trim($vidx)
  e = ($eidx==""? "": $eidx)+0
  c = (cidx? $cidx+0 : 0)
  r = (ridx? $ridx+0 : 0)

  n[v]++
  se[v]+=e; sse[v]+=e*e
  if(cidx){ sc[v]+=c; ssc[v]+=c*c }
  if(ridx){ sr[v]+=r; ssr[v]+=r*r }
}
END{
  # Encabezado en español
  printf "LENGUAJE,VERSION,TIEMPO TOTAL EJECUCIÓN (segundos) [media±sd],USO CPU (%%) [media±sd],MEMORIA RESIDENTE USO MÁXIMO (kbytes) [media±sd]\n"
  for(v in n){
    cnt=n[v]
    me=se[v]/cnt;  sde=(cnt>1? sqrt(sse[v]/cnt - me*me) : 0)

    if(cidx){ mc=sc[v]/cnt; sdc=(cnt>1? sqrt(ssc[v]/cnt - mc*mc) : 0) } else { mc=""; sdc="" }
    if(ridx){ mr=sr[v]/cnt; sdr=(cnt>1? sqrt(ssr[v]/cnt - mr*mr) : 0) } else { mr=""; sdr="" }

    # LENGUAJE fijo C; VERSION=Variant
    printf "C,%s,%.2f ± %.2f,", v, me, sde
    if(cidx) printf "%.2f %% ± %.2f,", mc, sdc; else printf ","
    if(ridx) printf "%.0f ± %.0f\n", mr, sdr; else printf "\n"
  }
}' "$csv" | column -s, -t
