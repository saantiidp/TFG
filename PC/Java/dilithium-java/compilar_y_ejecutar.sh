#!/bin/bash

# Ruta al JAR de BouncyCastle
BC_JAR="lib/bcprov-jdk18on-1.81.jar"

# Crear directorio de salida
mkdir -p bin

# Recolectar fuentes principales (sin tests)
find src/main/java -name "*.java" > sources_main.txt
echo src/DilithiumRendimiento.java >> sources_main.txt

# Compilar
echo "🔧 Compilando archivos Java..."
javac -cp "$BC_JAR" -d bin @sources_main.txt

# Verificamos que la compilación fue exitosa
if [ $? -ne 0 ]; then
  echo "❌ Error en la compilación."
  exit 1
fi

# Ejecutar
echo -e "\n🚀 Ejecutando DilithiumRendimiento...\n"
java -cp "bin:$BC_JAR" DilithiumRendimiento
