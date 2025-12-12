import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.*
import org.junit.runner.RunWith

import java.io.File
import java.io.FileOutputStream
import java.security.KeyPairGenerator
import java.security.SecureRandom
import java.security.Security
import java.security.Signature
import java.util.Locale
import kotlin.math.roundToLong

import android.os.SystemClock

// Proveedores
import org.bouncycastle.jce.provider.BouncyCastleProvider
import org.bouncycastle.pqc.jcajce.provider.BouncyCastlePQCProvider

// ---------- Lightweight API (KEM) ----------
import org.bouncycastle.crypto.AsymmetricCipherKeyPair

// Kyber
import org.bouncycastle.pqc.crypto.crystals.kyber.*
import org.bouncycastle.pqc.crypto.crystals.kyber.KyberParameters.*

// HQC
import org.bouncycastle.pqc.crypto.hqc.*

// BIKE
import org.bouncycastle.pqc.crypto.bike.*

// ---------- Firmas: ParameterSpec ----------
import org.bouncycastle.pqc.jcajce.spec.DilithiumParameterSpec
import org.bouncycastle.pqc.jcajce.spec.FalconParameterSpec
import org.bouncycastle.pqc.jcajce.spec.SPHINCSPlusParameterSpec

@RunWith(AndroidJUnit4::class)
class PQC_KotlinTest {

    companion object {
        private val sr = SecureRandom()
        private const val ITERS = 120
        private val csvRows = mutableListOf<String>()
        private lateinit var outDir: File


        @BeforeClass
        @JvmStatic
        fun setUp() {

            Security.removeProvider("BC")
            Security.removeProvider("BCPQC")
            Security.addProvider(BouncyCastleProvider())
            Security.addProvider(BouncyCastlePQCProvider())

            val ctx = InstrumentationRegistry.getInstrumentation().targetContext

            // === Carpeta permitida por Android para apps y tests ===
            outDir = File(ctx.getExternalFilesDir(null), "pqc_csv").apply { mkdirs() }

            println("== PQC tests in: ${ctx.packageName}")
            println("== CSV device dir: ${outDir.absolutePath}")
        }



        @AfterClass
        @JvmStatic
        fun dumpCsv() {
            println("CSV_DUMP_BEGIN")
            csvRows.forEach { println("CSV_ROW:$it") }
            println("CSV_DUMP_END")
        }

        // ==== filas de iteraciones: añadimos t_epoch_ms a cada fila ====
        private fun addCsvRow(algorithm: String, op: String, iter: Int, ms: Double) {
            val msRounded = ((ms * 1000.0).roundToLong() / 1000.0)
            val tEpoch = System.currentTimeMillis() // 5ª columna: epoch ms
            val row = listOf(
                algorithm, op, iter.toString(), msRounded.toString(), tEpoch.toString()
            ).joinToString(",")
            csvRows += row
            writeRowToAlgoCsv(algorithm, row)
        }

        private fun writeRowToAlgoCsv(algorithm: String, row: String) {
            val safe = algorithm.lowercase(Locale.ENGLISH).replace("[^a-z0-9_\\-]+".toRegex(), "_")
            val file = File(outDir, "${safe}_iterations.csv")
            val needsHeader = !file.exists()
            FileOutputStream(file, true).bufferedWriter().use { w ->
                if (needsHeader) w.appendLine("algo,op,iter,ms,t_epoch_ms")
                w.appendLine(row)
            }
        }

        // ---- Timer helper (wall time por operación) ----
        private inline fun <T> timeMs(block: () -> T): Pair<T, Double> {
            val t0 = System.nanoTime()
            val res = block()
            val t1 = System.nanoTime()
            return res to ((t1 - t0) / 1e6)
        }

        // ============================================================
        // ================ MÉTRICAS GLOBALES POR ALGORITMO ============
        // ============================================================

        // CPU time del proceso (user+sys) en ms, vía /proc/self/stat
        private fun getProcessCpuTimeMs(): Long {
            return try {
                val stat = File("/proc/self/stat").readText()
                val parts = stat.split(" ")
                    .filter { it.isNotEmpty() }

                // Campos 14 y 15 (1-based) -> índices 13 y 14 (0-based)
                val utimeTicks = parts[13].toLong()
                val stimeTicks = parts[14].toLong()
                val ticksPerSecond = 100L // En Android es 100
                ((utimeTicks + stimeTicks) * 1000L) / ticksPerSecond
            } catch (_: Throwable) {
                -1L
            }
        }

        // RSS máximo (VmHWM) en kB, equivalente a Maximum resident set size de time -v
        private fun getMaxRssKb(): Int {
            return try {
                val statusLines = File("/proc/self/status").readLines()
                val line = statusLines.firstOrNull { it.startsWith("VmHWM:") }
                    ?: return -1
                val parts = line.trim().split(Regex("\\s+"))
                // Ejemplo: "VmHWM:   12345 kB" -> ["VmHWM:", "12345", "kB"]
                parts[1].toInt()
            } catch (_: Throwable) {
                -1
            }
        }

        // Escribe un CSV resumen por algoritmo: wall, cpu, %, rss
        private fun writeAlgoSummaryCsv(
            algorithm: String,
            wallMs: Long,
            cpuMs: Long,
            cpuPercent: Double,
            rssKb: Int
        ) {
            val safe = algorithm.lowercase(Locale.ENGLISH).replace("[^a-z0-9_\\-]+".toRegex(), "_")
            val file = File(outDir, "${safe}_summary.csv")
            val needsHeader = !file.exists()
            FileOutputStream(file, true).bufferedWriter().use { w ->
                if (needsHeader) {
                    w.appendLine("algo,wall_ms,cpu_ms,cpu_percent,rss_kb")
                }
                val cpuPctRounded = ((cpuPercent * 1000.0).roundToLong() / 1000.0)
                val row = listOf(
                    algorithm,
                    wallMs.toString(),
                    cpuMs.toString(),
                    cpuPctRounded.toString(),
                    rssKb.toString()
                ).joinToString(",")
                w.appendLine(row)
            }
        }

        /**
         * Envuelve la ejecución de un algoritmo completo midiendo:
         * - wall time total (ms)
         * - CPU time de proceso (ms)
         * - CPU% estimado
         * - RSS máximo (VmHWM) en kB
         *
         * Solo escribe el summary si el bloque termina correctamente.
         */
        private inline fun runMeasuredAlgorithm(algorithm: String, block: () -> Unit) {
            val wallBefore = SystemClock.elapsedRealtime()
            val cpuBefore = getProcessCpuTimeMs()
            val rssBefore = getMaxRssKb() // no es estrictamente necesario, pero lo dejamos

            var success = false
            try {
                block()
                success = true
            } finally {
                if (success) {
                    val wallAfter = SystemClock.elapsedRealtime()
                    val cpuAfter = getProcessCpuTimeMs()
                    val rssAfter = getMaxRssKb()

                    val wallMs = wallAfter - wallBefore
                    val cpuMs = if (cpuAfter >= 0 && cpuBefore >= 0) cpuAfter - cpuBefore else -1L
                    val rssKb = if (rssAfter >= 0) rssAfter else rssBefore

                    val cpuPercent =
                        if (wallMs > 0L && cpuMs >= 0L) (cpuMs.toDouble() / wallMs.toDouble()) * 100.0
                        else -1.0

                    println(
                        "SUMMARY $algorithm :: wall=${wallMs}ms, cpu=${cpuMs}ms, " +
                                "cpu%=$cpuPercent, rssMax=${rssKb}kB"
                    )
                    writeAlgoSummaryCsv(algorithm, wallMs, cpuMs, cpuPercent, rssKb)
                }
            }
        }
    }

    // =====================================================================
    // =============================== KEM ==================================
    // =====================================================================

    // ---------- Kyber ----------
    private fun runKyberVariant(name: String, params: KyberParameters) {
        var kept = 0
        for (i in 1..ITERS) {
            val (kp, keygenMs) = timeMs {
                val kpg = KyberKeyPairGenerator()
                kpg.init(KyberKeyGenerationParameters(sr, params))
                kpg.generateKeyPair()
            }
            val (sw, encapMs) = timeMs {
                val gen = KyberKEMGenerator(sr)
                gen.generateEncapsulated(kp.public as KyberPublicKeyParameters)
            }
            val (_, decapMs) = timeMs {
                val ext = KyberKEMExtractor(kp.private as KyberPrivateKeyParameters)
                ext.extractSecret((sw.encapsulation as ByteArray))
            }
            val total = keygenMs + encapMs + decapMs
            addCsvRow(name, "KeyGen", i, keygenMs)
            addCsvRow(name, "Encap",  i, encapMs)
            addCsvRow(name, "Decap",  i, decapMs)
            addCsvRow(name, "Total",  i, total)
            kept++
        }
        println("$name OK: $kept iteraciones")
    }

    @Test
    fun testKyber512() = runMeasuredAlgorithm("Kyber-512") {
        runKyberVariant("Kyber-512", kyber512)
    }

    @Test
    fun testKyber768() = runMeasuredAlgorithm("Kyber-768") {
        runKyberVariant("Kyber-768", kyber768)
    }

    @Test
    fun testKyber1024() = runMeasuredAlgorithm("Kyber-1024") {
        runKyberVariant("Kyber-1024", kyber1024)
    }

    // ---------- HQC ----------
    private fun runHqcVariant(name: String, params: HQCParameters) {
        var kept = 0
        for (i in 1..ITERS) {
            val (kp, keygenMs) = timeMs {
                val kpg = HQCKeyPairGenerator()
                kpg.init(HQCKeyGenerationParameters(sr, params))
                kpg.generateKeyPair()
            }
            val (sw, encapMs) = timeMs {
                val gen = HQCKEMGenerator(sr)
                gen.generateEncapsulated(kp.public as HQCPublicKeyParameters)
            }
            val (_, decapMs) = timeMs {
                val ext = HQCKEMExtractor(kp.private as HQCPrivateKeyParameters)
                ext.extractSecret((sw.encapsulation as ByteArray))
            }
            val total = keygenMs + encapMs + decapMs
            addCsvRow(name, "KeyGen", i, keygenMs)
            addCsvRow(name, "Encap",  i, encapMs)
            addCsvRow(name, "Decap",  i, decapMs)
            addCsvRow(name, "Total",  i, total)
            kept++
        }
        println("$name OK: $kept iteraciones")
    }

    @Test
    fun testHQC128() = runMeasuredAlgorithm("HQC-128") {
        runHqcVariant("HQC-128", HQCParameters.hqc128)
    }

    @Test
    fun testHQC192() = runMeasuredAlgorithm("HQC-192") {
        runHqcVariant("HQC-192", HQCParameters.hqc192)
    }

    @Test
    fun testHQC256() = runMeasuredAlgorithm("HQC-256") {
        runHqcVariant("HQC-256", HQCParameters.hqc256)
    }

    // ---------- BIKE ----------
    private fun runBikeVariant(name: String, params: BIKEParameters) {
        var kept = 0
        for (i in 1..ITERS) {
            val (kp, keygenMs) = timeMs {
                val kpg = BIKEKeyPairGenerator()
                kpg.init(BIKEKeyGenerationParameters(sr, params))
                kpg.generateKeyPair()
            }
            val (sw, encapMs) = timeMs {
                val gen = BIKEKEMGenerator(sr)
                gen.generateEncapsulated(kp.public as BIKEPublicKeyParameters)
            }
            val (_, decapMs) = timeMs {
                val ext = BIKEKEMExtractor(kp.private as BIKEPrivateKeyParameters)
                ext.extractSecret((sw.encapsulation as ByteArray))
            }
            val total = keygenMs + encapMs + decapMs
            addCsvRow(name, "KeyGen", i, keygenMs)
            addCsvRow(name, "Encap",  i, encapMs)
            addCsvRow(name, "Decap",  i, decapMs)
            addCsvRow(name, "Total",  i, total)
            kept++
        }
        println("$name OK: $kept iteraciones")
    }

    @Test
    fun testBIKE128() = runMeasuredAlgorithm("BIKE-128") {
        runBikeVariant("BIKE-128", BIKEParameters.bike128)
    }

    @Test
    fun testBIKE192() = runMeasuredAlgorithm("BIKE-192") {
        runBikeVariant("BIKE-192", BIKEParameters.bike192)
    }

    @Test
    fun testBIKE256() = runMeasuredAlgorithm("BIKE-256") {
        runBikeVariant("BIKE-256", BIKEParameters.bike256)
    }

    // ---------- CMCE (reflexión con autodetección de nombres y firmas) ----------
    private fun findCmceParamsFieldNames(): List<String> {
        return try {
            val paramsClz = Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEParameters")
            val names = paramsClz.fields.mapNotNull { f -> if (f.type == paramsClz) f.name else null }
            println("CMCE available params in this build: $names")
            names
        } catch (e: Throwable) {
            println("CMCEParameters class not found: ${e.message}")
            emptyList()
        }
    }

    private fun pickCmceFieldForSize(allNames: List<String>, size: String): String? {
        val lc = allNames.map { it.lowercase(Locale.ENGLISH) }
        val candidates = listOf(
            "mceliece${size}fr3", "mceliece${size}f", "mceliece${size}r3", "mceliece${size}"
        )
        return candidates.firstOrNull { it in lc }
    }

    private fun runCmceReflectiveAuto(sizeTag: String, display: String) {
        var kept = 0
        try {
            val paramsClz = Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEParameters")
            val all = findCmceParamsFieldNames()
            val fieldName = pickCmceFieldForSize(all, sizeTag)
                ?: throw NoSuchFieldException("No CMCEParameters field for size=$sizeTag in $all")
            val paramsField = paramsClz.getDeclaredField(fieldName)
            val params = paramsField.get(null)

            val kpgClz  = Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEKeyPairGenerator")
            val kgpClz  = Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEKeyGenerationParameters")
            val genClz  = Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEKEMGenerator")
            val extClz  = Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEKEMExtractor")

            val pubClz = try {
                Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEPublicKeyParameters")
            } catch (_: Throwable) {
                Class.forName("org.bouncycastle.crypto.params.AsymmetricKeyParameter")
            }
            val privClz = try {
                Class.forName("org.bouncycastle.pqc.crypto.cmce.CMCEPrivateKeyParameters")
            } catch (_: Throwable) {
                Class.forName("org.bouncycastle.crypto.params.AsymmetricKeyParameter")
            }

            val kgBaseClz = try {
                Class.forName("org.bouncycastle.crypto.KeyGenerationParameters")
            } catch (_: Throwable) { kgpClz }

            for (i in 1..ITERS) {
                // --- KeyGen ---
                val (kp, keygenMs) = timeMs {
                    val kpg = kpgClz.getDeclaredConstructor().newInstance()
                    val kgp = kgpClz.getConstructor(SecureRandom::class.java, params.javaClass)
                        .newInstance(sr, params)

                    val initMethod = kpgClz.methods.firstOrNull { m ->
                        m.name == "init" && m.parameterTypes.size == 1 &&
                                m.parameterTypes[0].isAssignableFrom(kgBaseClz)
                    } ?: kpgClz.methods.first { m ->
                        m.name == "init" && m.parameterTypes.size == 1 &&
                                m.parameterTypes[0].isAssignableFrom(kgpClz)
                    }
                    initMethod.invoke(kpg, kgp)

                    @Suppress("UNCHECKED_CAST")
                    kpgClz.getMethod("generateKeyPair").invoke(kpg) as AsymmetricCipherKeyPair
                }

                // --- Encap ---
                val (sw, encapMs) = timeMs {
                    val gen = genClz.getConstructor(SecureRandom::class.java).newInstance(sr)
                    val encapMethod = genClz.methods.first { m ->
                        m.name == "generateEncapsulated" && m.parameterTypes.size == 1 &&
                                m.parameterTypes[0].isAssignableFrom(pubClz)
                    }
                    encapMethod.invoke(gen, kp.public)
                }

                // --- Decap ---
                val (_, decapMs) = timeMs {
                    val extCtor = extClz.constructors.first { c ->
                        c.parameterTypes.size == 1 && c.parameterTypes[0].isAssignableFrom(privClz)
                    }
                    val ext = extCtor.newInstance(kp.private)

                    val ct = sw.javaClass.getMethod("getEncapsulation").invoke(sw) as ByteArray
                    val extractMethod = extClz.methods.first { m ->
                        m.name == "extractSecret" && m.parameterTypes.size == 1 &&
                                m.parameterTypes[0] == ByteArray::class.java
                    }
                    extractMethod.invoke(ext, ct)
                }

                val total = keygenMs + encapMs + decapMs
                addCsvRow(display, "KeyGen", i, keygenMs)
                addCsvRow(display, "Encap",  i, encapMs)
                addCsvRow(display, "Decap",  i, decapMs)
                addCsvRow(display, "Total",  i, total)
                kept++
            }
            println("$display OK: $kept iteraciones (paramsField=$fieldName)")
        } catch (e: Throwable) {
            println("SKIP $display (CMCE no disponible o API distinta): ${e.message}")
            Assume.assumeTrue("CMCE no disponible: ${e.message}", false)
        }
    }

    @Test
    fun testCMCE_348864f() = runMeasuredAlgorithm("CMCE-348864f") {
        runCmceReflectiveAuto("348864", "CMCE-348864f")
    }

    @Test
    fun testCMCE_460896f() = runMeasuredAlgorithm("CMCE-460896f") {
        runCmceReflectiveAuto("460896", "CMCE-460896f")
    }

    @Test
    fun testCMCE_6688128f() = runMeasuredAlgorithm("CMCE-6688128f") {
        runCmceReflectiveAuto("6688128", "CMCE-6688128f")
    }

    // =====================================================================
    // =============================== FIRMAS ================================
    // =====================================================================

    private fun runSignatureVariant(
        display: String,
        keypairAlg: String,
        keyParamSpec: Any,
        signatureAlg: String = keypairAlg,
        provider: String = "BCPQC"
    ) {
        var kept = 0
        for (i in 1..ITERS) {
            val (kp, keygenMs) = timeMs {
                val kpg = KeyPairGenerator.getInstance(keypairAlg, provider)
                when (keyParamSpec) {
                    is DilithiumParameterSpec      -> kpg.initialize(keyParamSpec, sr)
                    is FalconParameterSpec         -> kpg.initialize(keyParamSpec, sr)
                    is SPHINCSPlusParameterSpec    -> kpg.initialize(keyParamSpec, sr)
                    else -> throw IllegalArgumentException("Spec no soportado: $keyParamSpec")
                }
                kpg.generateKeyPair()
            }

            val msg = ByteArray(32).also { sr.nextBytes(it) }

            val (sigBytes, signMs) = timeMs {
                val sig = Signature.getInstance(signatureAlg, provider)
                sig.initSign(kp.private, sr)
                sig.update(msg)
                sig.sign()
            }

            val (_, verifyMs) = timeMs {
                val sig = Signature.getInstance(signatureAlg, provider)
                sig.initVerify(kp.public)
                sig.update(msg)
                sig.verify(sigBytes)
            }

            val total = keygenMs + signMs + verifyMs
            addCsvRow(display, "KeyGen", i, keygenMs)
            addCsvRow(display, "Sign",  i, signMs)
            addCsvRow(display, "Verify",i, verifyMs)
            addCsvRow(display, "Total", i, total)
            kept++
        }
        println("$display OK: $kept iteraciones")
    }

    // Dilithium (2/3/5)
    @Test
    fun testDilithium2() = runMeasuredAlgorithm("Dilithium2") {
        runSignatureVariant(
            display = "Dilithium2",
            keypairAlg = "DILITHIUM",
            keyParamSpec = DilithiumParameterSpec.dilithium2,
            signatureAlg = "DILITHIUM"
        )
    }

    @Test
    fun testDilithium3() = runMeasuredAlgorithm("Dilithium3") {
        runSignatureVariant(
            display = "Dilithium3",
            keypairAlg = "DILITHIUM",
            keyParamSpec = DilithiumParameterSpec.dilithium3,
            signatureAlg = "DILITHIUM"
        )
    }

    @Test
    fun testDilithium5() = runMeasuredAlgorithm("Dilithium5") {
        runSignatureVariant(
            display = "Dilithium5",
            keypairAlg = "DILITHIUM",
            keyParamSpec = DilithiumParameterSpec.dilithium5,
            signatureAlg = "DILITHIUM"
        )
    }

    // Falcon (512/1024)
    @Test
    fun testFalcon512() = runMeasuredAlgorithm("Falcon-512") {
        runSignatureVariant(
            display = "Falcon-512",
            keypairAlg = "Falcon",
            keyParamSpec = FalconParameterSpec.falcon_512,
            signatureAlg = "Falcon"
        )
    }

    @Test
    fun testFalcon1024() = runMeasuredAlgorithm("Falcon-1024") {
        runSignatureVariant(
            display = "Falcon-1024",
            keypairAlg = "Falcon",
            keyParamSpec = FalconParameterSpec.falcon_1024,
            signatureAlg = "Falcon"
        )
    }

    // SPHINCS+ SHA2-f (128f/192f/256f)
    @Test
    fun testSPHINCS_sha2_128f() = runMeasuredAlgorithm("sha2-128f") {
        runSignatureVariant(
            display = "sha2-128f",
            keypairAlg = "SPHINCS+",
            keyParamSpec = SPHINCSPlusParameterSpec.sha2_128f,
            signatureAlg = "SPHINCS+"
        )
    }

    @Test
    fun testSPHINCS_sha2_192f() = runMeasuredAlgorithm("sha2-192f") {
        runSignatureVariant(
            display = "sha2-192f",
            keypairAlg = "SPHINCS+",
            keyParamSpec = SPHINCSPlusParameterSpec.sha2_192f,
            signatureAlg = "SPHINCS+"
        )
    }

    @Test
    fun testSPHINCS_sha2_256f() = runMeasuredAlgorithm("sha2-256f") {
        runSignatureVariant(
            display = "sha2-256f",
            keypairAlg = "SPHINCS+",
            keyParamSpec = SPHINCSPlusParameterSpec.sha2_256f,
            signatureAlg = "SPHINCS+"
        )
    }
}
