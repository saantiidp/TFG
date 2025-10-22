#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Ejecutando SPHINCS+ benchmarks..."
java -cp "bin:lib/*" SphincsPlusBenchmarkCSV
echo "[OK] Ejecución completada."
