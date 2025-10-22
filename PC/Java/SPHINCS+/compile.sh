#!/usr/bin/env bash
set -euo pipefail
mkdir -p bin
echo "[INFO] Compilando..."
javac -cp "lib/*" -d bin src/SphincsPlusBenchmarkCSV.java
echo "[OK] bin/SphincsPlusBenchmarkCSV.class"
