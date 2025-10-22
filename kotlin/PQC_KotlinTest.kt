package com.example.tfg_kotlin

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.bouncycastle.jce.provider.BouncyCastleProvider
import org.bouncycastle.pqc.jcajce.interfaces.KyberPrivateKey
import org.bouncycastle.pqc.jcajce.interfaces.KyberPublicKey
import org.bouncycastle.pqc.jcajce.provider.BouncyCastlePQCProvider
import org.bouncycastle.pqc.jcajce.spec.DilithiumParameterSpec
import org.bouncycastle.pqc.jcajce.spec.FalconParameterSpec
import org.bouncycastle.pqc.jcajce.spec.KyberParameterSpec
import org.bouncycastle.pqc.jcajce.spec.SPHINCSPlusParameterSpec
import org.bouncycastle.pqc.jcajce.spec.BIKEParameterSpec
import org.bouncycastle.pqc.jcajce.spec.HQCParameterSpec
import org.bouncycastle.jcajce.spec.KEMGenerateSpec
import org.bouncycastle.jcajce.spec.KEMExtractSpec
import org.bouncycastle.jcajce.SecretKeyWithEncapsulation
import org.junit.Test
import java.io.File
import java.security.KeyPairGenerator
import java.security.Security
import java.security.Signature
import java.util.Locale
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import kotlin.system.measureNanoTime

class PQC_KotlinTest {

    init {
        //Incorporamos los algoritmos de bouncycastle
        Security.addProvider(BouncyCastleProvider())
        Security.addProvider(BouncyCastlePQCProvider())
    }

    /**********PRUEBAS FALCON******************************************************************************************************/

    @Test
    fun testFalconPerformance() {
        val versions = listOf(
            //"Falcon-512" to FalconParameterSpec.falcon_512,
            "Falcon-1024" to FalconParameterSpec.falcon_1024
        )
        val numIterations = 50
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>() //Guardamos las iteraciones


        versions.forEach { (name, spec) ->
            println("\nEjecutando pruebas para $name")
            val (stats, iterationsTimes) = runFalconTest(name, spec, numIterations)
            results[name] = stats
            iterationResults[name] = iterationsTimes
        }

        // Mostramos los resultados de las pruebas
        showResultsToTerminal(results, iterationResults)
    }

    private fun runFalconTest(
        name: String,
        spec: FalconParameterSpec,
        numIterations: Int
    ): Pair<String, List<Double>> {
        //Variables con los tiempos de generación de claves, tiempo de firma y de verificación
        val keyGenTimes = mutableListOf<Double>()
        val signTimes = mutableListOf<Double>()
        val verifyTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        val kpg = KeyPairGenerator.getInstance("Falcon", BouncyCastlePQCProvider.PROVIDER_NAME)
        kpg.initialize(spec)

        repeat(numIterations) { iteration ->
            //Generación de claves
            lateinit var keyPair: java.security.KeyPair
            val keyPairGenTime = measureNanoTime {
                keyPair =
                    kpg.generateKeyPair() // // Generamos el par de claves solo una vez para la firma y verificación
            } / 1_000_000.0


            val signature = Signature.getInstance("Falcon", BouncyCastlePQCProvider.PROVIDER_NAME)
            val msg = "Mensaje de prueba".toByteArray()

            //Firma del algoritmo
            signature.initSign(keyPair.private)
            val signedMsg: ByteArray
            val signTime = measureNanoTime {
                signature.update(msg)
                signedMsg = signature.sign() // guardamos la firma
            } / 1_000_000.0


            //Verificación
            signature.initVerify(keyPair.public)
            val verifyTime = measureNanoTime {
                signature.update(msg)
                signature.verify(signedMsg)
            } / 1_000_000.0


            // Calcular y almacenar tiempo total por iteración
            val totalTime = keyPairGenTime + signTime + verifyTime

            //WARM-UP
            if (iteration >= 10) {
                keyGenTimes.add(keyPairGenTime)
                signTimes.add(signTime)
                verifyTimes.add(verifyTime)
                totalTimes.add(totalTime)
            }
        }

        //Obtenemos la media y desviación típica
        val keyGenStats = calculateStats(keyGenTimes)
        val signStats = calculateStats(signTimes)
        val verifyStats = calculateStats(verifyTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para $name:")
        println("Tiempo total generación de claves: ${keyGenStats} ms")
        println("Tiempo total firma: ${signStats} ms")
        println("Tiempo total verificación: ${verifyStats} ms")
        println("Tiempo total**: ${globalStats} ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }

    /**********PRUEBAS CRYSTALS-DILITHIUM******************************************************************************************************/
    @Test
    fun testDilithiumPerformance() {
        val versions = listOf(
            "Dilithium2" to DilithiumParameterSpec.dilithium2,
            "Dilithium3" to DilithiumParameterSpec.dilithium3,
            "Dilithium5" to DilithiumParameterSpec.dilithium5
        )
        val numIterations = 1000
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>() //Guardamos las iteraciones


        versions.forEach { (name, spec) ->
            println("\nEjecutando pruebas para $name")
            val (stats, iterationsTimes) = runDilithiumTest(name, spec, numIterations)
            results[name] = stats
            iterationResults[name] = iterationsTimes
        }

        // Mostramos los resultados de las pruebas
        showResultsToTerminal(results, iterationResults)
    }

    private fun runDilithiumTest(
        name: String,
        spec: DilithiumParameterSpec,
        numIterations: Int
    ): Pair<String, List<Double>> {
        //Variables con los tiempos de generación de claves, tiempo de firma y de verificación
        val keyGenTimes = mutableListOf<Double>()
        val signTimes = mutableListOf<Double>()
        val verifyTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        val kpg = KeyPairGenerator.getInstance("Dilithium", BouncyCastlePQCProvider.PROVIDER_NAME)
        kpg.initialize(spec)

        repeat(numIterations) { iteration ->
            //Generación de claves
            lateinit var keyPair: java.security.KeyPair
            val keyPairGenTime = measureNanoTime {
                keyPair =
                    kpg.generateKeyPair() // // Generamos el par de claves solo una vez para la firma y verificación
            } / 1_000_000.0

            val signature =
                Signature.getInstance("Dilithium", BouncyCastlePQCProvider.PROVIDER_NAME)
            val msg = "Mensaje de prueba".toByteArray()

            //Firma del algoritmo
            signature.initSign(keyPair.private)
            val signedMsg: ByteArray
            val signTime = measureNanoTime {
                signature.update(msg)
                signedMsg = signature.sign() // guardamos la firma
            } / 1_000_000.0

            //Verificación
            signature.initVerify(keyPair.public)
            val verifyTime = measureNanoTime {
                signature.update(msg)
                signature.verify(signedMsg)
            } / 1_000_000.0

            // Calcular y almacenar tiempo total por iteración
            val totalTime = keyPairGenTime + signTime + verifyTime
            if (iteration >= 10) {
                keyGenTimes.add(keyPairGenTime)
                signTimes.add(signTime)
                verifyTimes.add(verifyTime)
                totalTimes.add(totalTime)
            }
        }

        //Obtenemos la media y desviación típica
        val keyGenStats = calculateStats(keyGenTimes)
        val signStats = calculateStats(signTimes)
        val verifyStats = calculateStats(verifyTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para $name:")
        println("Tiempo total generación de claves: ${keyGenStats} ms")
        println("Tiempo total firma: ${signStats} ms")
        println("Tiempo total verificación: ${verifyStats} ms")
        println("Tiempo total**: ${globalStats} ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }

    /**********PRUEBAS SPHINCS+******************************************************************************************************/

    @Test
    fun testSphincsPlusPerformance() {
        val versions = listOf(
            //"sha2-128f" to SPHINCSPlusParameterSpec.sha2_128f,
            //"sha2-128s" to SPHINCSPlusParameterSpec.sha2_128s,

            //"sha2-192f" to SPHINCSPlusParameterSpec.sha2_192f,
            //"sha2-192s" to SPHINCSPlusParameterSpec.sha2_192s,

            "sha2-256f" to SPHINCSPlusParameterSpec.sha2_256f,
            //"sha2-256s" to SPHINCSPlusParameterSpec.sha2_256s,

            //"shake-128f" to SPHINCSPlusParameterSpec.shake_128f,
            //"shake-128s" to SPHINCSPlusParameterSpec.shake_128s,

            //"shake-192f" to SPHINCSPlusParameterSpec.shake_192f,
            //"shake-192s" to SPHINCSPlusParameterSpec.shake_192s,

            //"shake-256f" to SPHINCSPlusParameterSpec.shake_256f,
            //"shake-256s" to SPHINCSPlusParameterSpec.shake_256s

        )
        val numIterations = 20
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>() //Guardamos las iteraciones


        versions.forEach { (name, spec) ->
            println("\nEjecutando pruebas para $name")
            val (stats, iterationsTimes) = runSphincsPlusTest(name, spec, numIterations)
            results[name] = stats
            iterationResults[name] = iterationsTimes
        }

        // Mostramos los resultados de las pruebas
        showResultsToTerminal(results, iterationResults)
    }

    private fun runSphincsPlusTest(
        name: String,
        spec: SPHINCSPlusParameterSpec,
        numIterations: Int
    ): Pair<String, List<Double>> {
        //Variables con los tiempos de generación de claves, tiempo de firma y de verificación
        val keyGenTimes = mutableListOf<Double>()
        val signTimes = mutableListOf<Double>()
        val verifyTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        val kpg = KeyPairGenerator.getInstance("SPHINCSPlus", BouncyCastlePQCProvider.PROVIDER_NAME)
        kpg.initialize(spec)

        repeat(numIterations) { iteration ->
            //Generación de claves
            lateinit var keyPair: java.security.KeyPair
            val keyPairGenTime = measureNanoTime {
                keyPair =
                    kpg.generateKeyPair()
            } / 1_000_000.0
            keyGenTimes.add(keyPairGenTime)

            val signature =
                Signature.getInstance("SPHINCSPlus", BouncyCastlePQCProvider.PROVIDER_NAME)
            val msg = "Mensaje de prueba".toByteArray()

            //Firma del algoritmo
            signature.initSign(keyPair.private)
            val signedMsg: ByteArray
            val signTime = measureNanoTime {
                signature.update(msg)
                signedMsg = signature.sign() // guardamos la firma
            } / 1_000_000.0
            signTimes.add(signTime)

            //Verificación
            signature.initVerify(keyPair.public)
            val verifyTime = measureNanoTime {
                signature.update(msg)
                signature.verify(signedMsg)
            } / 1_000_000.0
            verifyTimes.add(verifyTime)

            // Calcular y almacenar tiempo total por iteración
            val totalTime = keyPairGenTime + signTime + verifyTime
            totalTimes.add(totalTime)
        }

        //Obtenemos la media y desviación típica
        val keyGenStats = calculateStats(keyGenTimes)
        val signStats = calculateStats(signTimes)
        val verifyStats = calculateStats(verifyTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para $name:")
        println("Tiempo total generación de claves: $keyGenStats ms")
        println("Tiempo total firma: $signStats ms")
        println("Tiempo total verificación: $verifyStats ms")
        println("Tiempo total**: $globalStats ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }

    /**********PRUEBAS CRYSTALS-KYBER******************************************************************************************************/

    @Test
    fun testKyberPerformance() {
        val versions = listOf(
            "Kyber-512" to KyberParameterSpec.kyber512,
            "Kyber-768" to KyberParameterSpec.kyber768,
            "Kyber-1024" to KyberParameterSpec.kyber1024
        )
        val numIterations = 1000
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>() // Guardamos las iteraciones

        versions.forEach { (name, spec) ->
            println("\nEjecutando pruebas para $name")
            val (stats, iterationsTimes) = runKyberTest(name, spec, numIterations)
            results[name] = stats
            iterationResults[name] = iterationsTimes
        }

        // Mostramos los resultados de las pruebas
        showResultsToTerminal(results, iterationResults)
    }

    private fun runKyberTest(
        name: String,
        spec: KyberParameterSpec,
        numIterations: Int
    ): Pair<String, List<Double>> {
        val keyGenTimes = mutableListOf<Double>()
        val encapsulationTimes = mutableListOf<Double>()
        val decapsulationTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        // Inicializamos el KeyPairGenerator con el proveedor BouncyCastle
        val kpg = KeyPairGenerator.getInstance("Kyber", BouncyCastlePQCProvider.PROVIDER_NAME)
        kpg.initialize(spec)

        repeat(numIterations) { iteration ->
            lateinit var keyPair: java.security.KeyPair
            val keyPairGenTime = measureNanoTime {
                keyPair = kpg.generateKeyPair() // Generamos el par de claves
            } / 1_000_000.0


            // Inicializamos el Cipher con el proveedor BouncyCastle para Key Encapsulation
            val cipher = Cipher.getInstance("Kyber", BouncyCastlePQCProvider.PROVIDER_NAME)

            // Proceso de encapsulación (cifrado de la clave secreta)
            val publicKey = keyPair.public as KyberPublicKey
            lateinit var encapMsgKey: ByteArray
            val encapTime = measureNanoTime {
                cipher.init(Cipher.WRAP_MODE, publicKey) // Usar WRAP_MODE para encapsulación
                encapMsgKey = cipher.wrap(publicKey) // Usamos wrap para encapsular la clave
            } / 1_000_000.0


            // Proceso de descifrado (descapsulación de la clave secreta)
            val privateKey = keyPair.private as KyberPrivateKey
            val decapsTime = measureNanoTime {
                cipher.init(Cipher.UNWRAP_MODE, privateKey) // Usar UNWRAP_MODE para descapsulación
                cipher.unwrap(encapMsgKey, "Kyber", Cipher.SECRET_KEY) // Desencapsulamos
            } / 1_000_000.0


            // Calcular y almacenar tiempo total por iteración
            val totalTime = keyPairGenTime + encapTime + decapsTime
            if (iteration >= 10) {
                keyGenTimes.add(keyPairGenTime)
                encapsulationTimes.add(encapTime)
                decapsulationTimes.add(decapsTime)
                totalTimes.add(totalTime)
            }
        }

        //Obtenemos la media y desviación típica
        val keyGenStats = calculateStats(keyGenTimes)
        val encapStats = calculateStats(encapsulationTimes)
        val decapStats = calculateStats(decapsulationTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para $name:")
        println("Tiempo total generación de claves: ${keyGenStats} ms")
        println("Tiempo total cifrado: ${encapStats} ms")
        println("Tiempo total descifrado: ${decapStats} ms")
        println("Tiempo total**: ${globalStats} ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }

    /**********PRUEBAS HQC******************************************************************************************************/
    @Test
    fun testHqcPerformance() {
        val versions = listOf(
            "HQC-128" to HQCParameterSpec.hqc128,
            "HQC-192" to HQCParameterSpec.hqc192,
            "HQC-256" to HQCParameterSpec.hqc256
        )
        val numIterations = 1000
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>()

        versions.forEach { (name, spec) ->
            println("\nEjecutando pruebas para $name")
            val (stats, iterationTimes) = runHqcTest(name, spec, numIterations)
            results[name] = stats
            iterationResults[name] = iterationTimes
        }

        showResultsToTerminal(results, iterationResults)
    }

    private fun runHqcTest(
        name: String,
        spec: java.security.spec.AlgorithmParameterSpec,
        numIterations: Int
    ): Pair<String, List<Double>> {
        val keyGenTimes = mutableListOf<Double>()
        val encapTimes = mutableListOf<Double>()
        val decapTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        val kpg = KeyPairGenerator.getInstance("HQC", BouncyCastlePQCProvider.PROVIDER_NAME)
        kpg.initialize(spec)

        val keyGen = KeyGenerator.getInstance("HQC", BouncyCastlePQCProvider.PROVIDER_NAME)

        repeat(numIterations) { iteration ->
            lateinit var keyPair: java.security.KeyPair
            val t1 = measureNanoTime {
                keyPair = kpg.generateKeyPair()
            } / 1_000_000.0

            lateinit var sender: SecretKeyWithEncapsulation
            val t2 = measureNanoTime {
                val kemSpec = KEMGenerateSpec(keyPair.public, "AES")
                keyGen.init(kemSpec)
                sender = keyGen.generateKey() as SecretKeyWithEncapsulation
            } / 1_000_000.0

            val t3 = measureNanoTime {
                val kemSpec = KEMExtractSpec(keyPair.private, sender.encapsulation, "AES")
                keyGen.init(kemSpec)
                keyGen.generateKey()
            } / 1_000_000.0

            val total = t1 + t2 + t3
            if (iteration >= 10) {
                keyGenTimes.add(t1)
                encapTimes.add(t2)
                decapTimes.add(t3)
                totalTimes.add(total)
            }
        }

        val keyGenStats = calculateStats(keyGenTimes)
        val encapStats = calculateStats(encapTimes)
        val decapStats = calculateStats(decapTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para $name:")
        println("Tiempo total generación de claves: ${keyGenStats} ms")
        println("Tiempo total encapsulación: ${encapStats} ms")
        println("Tiempo total descapsulación: ${decapStats} ms")
        println("Tiempo total**: ${globalStats} ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }

    /**********PRUEBAS Bike******************************************************************************************************/
    @Test
    fun testBikePerformance() {
        val versions = listOf(
            "BIKE-128" to BIKEParameterSpec.bike128,
            "BIKE-192" to BIKEParameterSpec.bike192,
            "BIKE-256" to BIKEParameterSpec.bike256
        )
        val numIterations = 1000
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>()

        versions.forEach { (name, spec) ->
            println("\nEjecutando pruebas para $name")
            val (stats, iterationTimes) = runBikeTest(name, spec, numIterations)
            results[name] = stats
            iterationResults[name] = iterationTimes
        }

        showResultsToTerminal(results, iterationResults)
    }

    private fun runBikeTest(
        name: String,
        spec: java.security.spec.AlgorithmParameterSpec,
        numIterations: Int
    ): Pair<String, List<Double>> {
        val keyGenTimes = mutableListOf<Double>()
        val encapTimes = mutableListOf<Double>()
        val decapTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        val kpg = KeyPairGenerator.getInstance("BIKE", BouncyCastlePQCProvider.PROVIDER_NAME)
        kpg.initialize(spec)

        val keyGen = KeyGenerator.getInstance("BIKE", BouncyCastlePQCProvider.PROVIDER_NAME)

        repeat(numIterations) { iteration ->
            lateinit var keyPair: java.security.KeyPair
            val t1 = measureNanoTime {
                keyPair = kpg.generateKeyPair()
            } / 1_000_000.0

            lateinit var sender: SecretKeyWithEncapsulation
            val t2 = measureNanoTime {
                val kemSpec = KEMGenerateSpec(keyPair.public, "AES")
                keyGen.init(kemSpec)
                sender = keyGen.generateKey() as SecretKeyWithEncapsulation
            } / 1_000_000.0

            val t3 = measureNanoTime {
                val kemSpec = KEMExtractSpec(keyPair.private, sender.encapsulation, "AES")
                keyGen.init(kemSpec)
                keyGen.generateKey()
            } / 1_000_000.0

            val total = t1 + t2 + t3
            if (iteration >= 10) {
                keyGenTimes.add(t1)
                encapTimes.add(t2)
                decapTimes.add(t3)
                totalTimes.add(total)
            }
        }

        val keyGenStats = calculateStats(keyGenTimes)
        val encapStats = calculateStats(encapTimes)
        val decapStats = calculateStats(decapTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para $name:")
        println("Tiempo total generación de claves: ${keyGenStats} ms")
        println("Tiempo total encapsulación: ${encapStats} ms")
        println("Tiempo total descapsulación: ${decapStats} ms")
        println("Tiempo total**: ${globalStats} ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }
    /********** PRUEBAS Classic McEliece ******************************************************************************************************/
    @Test
    fun testMcEliecePerformance() {
        val versions = listOf(
            "McE-348864"   to McElieceParameterSpec.mceliece348864,
            "McE-460896"   to McElieceParameterSpec.mceliece460896,
            "McE-6688128"  to McElieceParameterSpec.mceliece6688128
            // Si quieres también las “fast”: 
            // "McE-348864f"  to McElieceParameterSpec.mceliece348864f,
            // "McE-460896f"  to McElieceParameterSpec.mceliece460896f,
            // "McE-6688128f" to McElieceParameterSpec.mceliece6688128f
        )
        val numIterations = 1000
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>()

        versions.forEach { (name, spec) ->
            println("\nEjecutando pruebas para $name")
            val (stats, iterationTimes) = runMcElieceTest(name, spec, numIterations)
            results[name] = stats
            iterationResults[name] = iterationTimes
        }

        showResultsToTerminal(results, iterationResults)
    }

    private fun runMcElieceTest(
        name: String,
        spec: java.security.spec.AlgorithmParameterSpec,
        numIterations: Int
    ): Pair<String, List<Double>> {
        val keyGenTimes = mutableListOf<Double>()
        val encapTimes  = mutableListOf<Double>()
        val decapTimes  = mutableListOf<Double>()
        val totalTimes  = mutableListOf<Double>()

        val kpg    = KeyPairGenerator.getInstance("McEliece", BouncyCastlePQCProvider.PROVIDER_NAME)
        kpg.initialize(spec)
        val keyGen = javax.crypto.KeyGenerator.getInstance("McEliece", BouncyCastlePQCProvider.PROVIDER_NAME)

        repeat(numIterations) { iteration ->
            lateinit var keyPair: java.security.KeyPair
            val t1 = kotlin.system.measureNanoTime {
                keyPair = kpg.generateKeyPair()
            } / 1_000_000.0

            lateinit var sender: SecretKeyWithEncapsulation
            val t2 = kotlin.system.measureNanoTime {
                val kemSpec = KEMGenerateSpec(keyPair.public, "AES")
                keyGen.init(kemSpec)
                sender = keyGen.generateKey() as SecretKeyWithEncapsulation
            } / 1_000_000.0

            val t3 = kotlin.system.measureNanoTime {
                val kemSpec = KEMExtractSpec(keyPair.private, sender.encapsulation, "AES")
                keyGen.init(kemSpec)
                keyGen.generateKey()
            } / 1_000_000.0

            val total = t1 + t2 + t3
            if (iteration >= 10) { // warm-up
                keyGenTimes.add(t1)
                encapTimes.add(t2)
                decapTimes.add(t3)
                totalTimes.add(total)
            }
        }

        val keyGenStats = calculateStats(keyGenTimes)
        val encapStats  = calculateStats(encapTimes)
        val decapStats  = calculateStats(decapTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para $name:")
        println("Tiempo total generación de claves: $keyGenStats ms")
        println("Tiempo total encapsulación: $encapStats ms")
        println("Tiempo total descapsulación: $decapStats ms")
        println("Tiempo total**: $globalStats ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }

    /***********Funciones para el cálculo de la media y la desviación típica y mostrar resultados******/
    // Función para calcular la media y la desv estandar
    private fun calculateStats(times: List<Double>): String {
        val mean = times.average()
        val stdDev = kotlin.math.sqrt(times.map { (it - mean) * (it - mean) }.average())
        return String.format(Locale.ENGLISH, "%.4f (+-%.4f)", mean, stdDev)
    }

    private fun showResultsToTerminal(
        results: Map<String, String>,
        iterationResults: Map<String, List<Double>>
    ) {

        val fileContent = buildString {
            results.forEach { (name, results) ->
                append("$name:\n$results\n\n")
            }
            iterationResults.forEach { (name, times) ->
                append("$name Iteraciones:\n")
                append(times.joinToString(",") { String.format(Locale.ENGLISH, "%.3f", it) })
                append("\n\n")
            }
        }
        println("Resultados de la ejecución:\n$fileContent")
    }
}