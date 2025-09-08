package com.example.tfg_kotlin

import org.bouncycastle.jce.provider.BouncyCastleProvider
import org.bouncycastle.pqc.jcajce.provider.BouncyCastlePQCProvider
import org.junit.Test
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.Security
import java.security.Signature
import java.util.Locale
import kotlin.system.measureNanoTime

class RSA_ECDSA_KotlinTest {
    init {
        //Incorporamos los algoritmos de bouncycastle
        Security.addProvider(BouncyCastleProvider())
        Security.addProvider(BouncyCastlePQCProvider())
    }

    @Test
    fun testRsaPerformance() {
        val numIterations = 75 // Modificar según recursos hardware disponibles
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>()

        listOf(2048, 4096).forEach { keySize ->
            println("\nEjecutando pruebas para RSA $keySize")
            val (stats, iterationsTimes) = runRsaTest(numIterations, keySize)
            results["RSA"] = stats
            iterationResults["RSA"] = iterationsTimes
        }

        showResultsToTerminal(results, iterationResults)
    }

    private fun runRsaTest(numIterations: Int, keySize: Int): Pair<String, List<Double>> {
        val keyGenTimes = mutableListOf<Double>()
        val signTimes = mutableListOf<Double>()
        val verifyTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        val keyGen = KeyPairGenerator.getInstance("RSA")
        keyGen.initialize(keySize)

        repeat(numIterations) { iteration ->
            lateinit var keyPair: KeyPair
            val keyPairGenTime = measureNanoTime {
                keyPair = keyGen.generateKeyPair()
            } / 1_000_000.0

            val msg = "Mensaje de prueba del algoritmo RSA".toByteArray()

            val signature = Signature.getInstance("SHA256withRSA")
            signature.initSign(keyPair.private)

            val signedBytes: ByteArray
            val signTime = measureNanoTime {
                signature.update(msg)
                signedBytes = signature.sign()
            } / 1_000_000.0

            val verifier = Signature.getInstance("SHA256withRSA")
            verifier.initVerify(keyPair.public)

            val verifyTime = measureNanoTime {
                verifier.update(msg)
                verifier.verify(signedBytes)
            } / 1_000_000.0

            val totalTime = keyPairGenTime + signTime + verifyTime

            // Ignoramos las primeras 5 iteraciones como warm-up
            if (iteration >= 5) {
                keyGenTimes.add(keyPairGenTime)
                signTimes.add(signTime)
                verifyTimes.add(verifyTime)
                totalTimes.add(totalTime)
            }
        }

        val keyGenStats = calculateStats(keyGenTimes)
        val signStats = calculateStats(signTimes)
        val verifyStats = calculateStats(verifyTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para RSA $keySize:")
        println("Tiempo total generación de claves: $keyGenStats ms")
        println("Tiempo total firma: $signStats ms")
        println("Tiempo total verificación: $verifyStats ms")
        println("Tiempo total**: $globalStats ms")

        return Pair("""TiempoTotal: $globalStats""".trimIndent(), totalTimes)
    }

    @Test
    fun testEcdsaPerformance() {
        val numIterations = 1000
        val results = mutableMapOf<String, String>()
        val iterationResults = mutableMapOf<String, List<Double>>()

        val ecdsaConfigs = listOf(
            256 to "SHA256withECDSA",
            384 to "SHA384withECDSA"
        )

        for ((curveSize, algorithm) in ecdsaConfigs) {
            println("\nEjecutando pruebas para ECDSA $curveSize")
            val (stats, iterationsTimes) = runEcdsaTest(numIterations, curveSize, algorithm)
            results["ECDSA"] = stats
            iterationResults["ECDSA"] = iterationsTimes
        }

        showResultsToTerminal(results, iterationResults)
    }

    private fun runEcdsaTest(numIterations: Int, curveSize: Int, algt: String): Pair<String, List<Double>> {
        val keyGenTimes = mutableListOf<Double>()
        val signTimes = mutableListOf<Double>()
        val verifyTimes = mutableListOf<Double>()
        val totalTimes = mutableListOf<Double>()

        val keyGen = KeyPairGenerator.getInstance("EC")
        keyGen.initialize(384)

        repeat(numIterations) { iteration ->
            lateinit var keyPair: KeyPair
            val keyPairGenTime = measureNanoTime {
                keyPair = keyGen.generateKeyPair()
            } / 1_000_000.0

            val msg = "Mensaje de prueba del algoritmo ECDSA".toByteArray()

            val signature = Signature.getInstance(algt)
            signature.initSign(keyPair.private)

            val signedBytes: ByteArray
            val signTime = measureNanoTime {
                signature.update(msg)
                signedBytes = signature.sign()
            } / 1_000_000.0

            val verifier = Signature.getInstance(algt)
            verifier.initVerify(keyPair.public)

            val verifyTime = measureNanoTime {
                verifier.update(msg)
                verifier.verify(signedBytes)
            } / 1_000_000.0

            val totalTime = keyPairGenTime + signTime + verifyTime

            // Ignoramos las primeras 10 iteraciones como warm-up
            if (iteration >= 10) {
                keyGenTimes.add(keyPairGenTime)
                signTimes.add(signTime)
                verifyTimes.add(verifyTime)
                totalTimes.add(totalTime)
            }
        }

        val keyGenStats = calculateStats(keyGenTimes)
        val signStats = calculateStats(signTimes)
        val verifyStats = calculateStats(verifyTimes)
        val globalStats = calculateStats(totalTimes)

        println("\n🔹 Resultados Globales para ECDSA $curveSize:")
        println("Tiempo total generación de claves: $keyGenStats ms")
        println("Tiempo total firma: $signStats ms")
        println("Tiempo total verificación: $verifyStats ms")
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