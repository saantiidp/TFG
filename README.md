#TFG

Para los lenguajes de Python y C en los algoritmos post-cuánticos se utilizan implementaciones oficiales y bibliotecas ampliamente validadas, garantizando la compatibilidad con los estándares del NIST y la reproducibilidad de los resultados experimentales.

En C, para los esquemas de la tercera ronda se emplean las implementaciones oficiales de referencia publicadas por los propios equipos de desarrollo: Kyber (https://pq-crystals.org/kyber/

) y Dilithium (https://pq-crystals.org/dilithium/
) a través del proyecto pq-crystals, Falcon mediante su implementación oficial (https://falcon-sign.info/
) y SPHINCS+ utilizando la implementación de referencia disponible en https://sphincs.org/
.
Para los esquemas de la cuarta ronda se utilizan implementaciones oficiales y optimizadas: BIKE a través del repositorio mantenido por AWS Labs (https://github.com/awslabs/bike-kem
), HQC desde los recursos oficiales del proyecto (https://pqc-hqc.org/resources.html
) y Classic McEliece mediante la colección PQClean (https://github.com/PQClean/PQClean

), incluyendo variantes de referencia y optimizadas.

En Python, no se emplean traducciones directas del código en C, sino bindings y bibliotecas de alto nivel. Todos los algoritmos post-cuánticos evaluados (BIKE, HQC, Kyber, Classic McEliece, Dilithium, Falcon y SPHINCS+) se ejecutan a través de la interfaz de Open Quantum Safe (OQS), utilizando liboqs (https://github.com/open-quantum-safe/liboqs

) y sus bindings para Python liboqs-python (https://github.com/open-quantum-safe/liboqs-python

).
Los experimentos se automatizan mediante scripts personalizados que miden las fases de generación de claves, encapsulación, desencapsulación, firma y verificación, almacenando los resultados en archivos .csv.

Para los lenguajes de Java y C#, las implementaciones se han desarrollado empleando la biblioteca Bouncy Castle, que proporciona soporte completo para los algoritmos post-cuánticos estandarizados por el NIST.

En Java, los algoritmos KEM se ejecutan a través de la API JCA/JCE proporcionada por BouncyCastlePQCProvider, utilizando las clases estándar KeyPairGenerator y KeyGenerator junto con las especificaciones KEMGenerateSpec y KEMExtractSpec.
Esta aproximación permite integrar los algoritmos post-cuánticos dentro del modelo criptográfico estándar de Java. La medición del rendimiento se realiza mediante System.nanoTime(), generando archivos .csv que recogen los tiempos de generación de claves, encapsulación y desencapsulación para cada iteración.

En C#, se emplea la biblioteca Bouncy Castle para .NET (Org.BouncyCastle.Pqc.Crypto), utilizando directamente las clases específicas de cada algoritmo (por ejemplo, KyberKeyPairGenerator, KyberKemGenerator y KyberKemExtractor).
La variante del algoritmo (Kyber-512, Kyber-768 o Kyber-1024) se selecciona dinámicamente en tiempo de ejecución mediante una estructura switch, permitiendo ejecutar distintas configuraciones sin modificar la lógica principal del programa.
El código incluye un calentamiento previo (warm-up) para reducir el impacto inicial del JIT y registra los tiempos de ejecución mediante la clase Stopwatch, almacenando los resultados en archivos .csv.

** Solo se proporcionan los ficheros que se han modificado para realizar las pruebas. En el caso de C y Python, es necesario clonar previamente los repositorios oficiales indicados e integrar o sustituir los ficheros correspondientes. En Java y C#, es necesario instalar la librería de Bouncy Castle, junto con las herramientas de desarrollo correspondientes (Java JDK y .NET SDK, respectivamente).

** Por simplificación, en Raspberry Pi 5 se muestra únicamente el código en C. Para el resto de lenguajes se deben utilizar los códigos disponibles en la carpeta Ordenador, modificando únicamente el nombre de los ficheros .csv y/o de las gráficas que se generen, y pudiendo ajustar las ejecuciones para lanzar una o varias versiones del algoritmo.
Por ejemplo, en C# se puede decidir medir diferentes configuraciones activando o desactivando llamadas concretas dentro del código, o seleccionando la variante del algoritmo mediante argumentos de entrada.

*** Dependiendo de la versión del algoritmo, la parte de ejecución puede modificarse. En el caso de Kyber en C#, la selección de parámetros se realiza mediante un bloque switch que permite cambiar dinámicamente entre Kyber-512, Kyber-768 y Kyber-1024 antes de inicializar el generador de claves.

*** Para los casos en Java, se generan dos archivos: uno global (.csv) que recoge los resultados finales, y otro con la información completa de todas las iteraciones realizadas. Este segundo archivo se utiliza posteriormente para subdividir los datos por versión del algoritmo y generar las gráficas de rendimiento de forma correcta.

** Para ejecutar Java, por ejemplo en Dilithium:
1º javac -cp "lib/*:bin" -d bin src/Dilithium_Rend.java
2º java -cp "bin:lib/*" src.Dilithium_Rend

** En C#, limpiar el proyecto con dotnet clean, compilar con dotnet build y ejecutar con dotnet run.
