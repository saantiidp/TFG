#!/usr/bin/env bash
set -euo pipefail

JAR="lib/bcprov-jdk18on-1.81.jar"
SRC="src/McElieceRendimiento.java"
BIN="bin"

mkdir -p "$BIN"

# Compila
javac -cp "$JAR" -d "$BIN" "$SRC"

# Ejecuta (50 iteraciones por CLI, por defecto 30)
ITER=${1:-30}
java -cp "$BIN:$JAR" McElieceRendimiento "$ITER"
