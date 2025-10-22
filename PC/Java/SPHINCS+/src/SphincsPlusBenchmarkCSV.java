// src/SphincsPlusBenchmarkCSV.java
import java.io.FileWriter;
import java.io.PrintWriter;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.bouncycastle.crypto.AsymmetricCipherKeyPair;
import org.bouncycastle.crypto.params.ParametersWithRandom;
import org.bouncycastle.pqc.crypto.sphincsplus.SPHINCSPlusKeyGenerationParameters;
import org.bouncycastle.pqc.crypto.sphincsplus.SPHINCSPlusKeyPairGenerator;
import org.bouncycastle.pqc.crypto.sphincsplus.SPHINCSPlusParameters;
import org.bouncycastle.pqc.crypto.sphincsplus.SPHINCSPlusPrivateKeyParameters;
import org.bouncycastle.pqc.crypto.sphincsplus.SPHINCSPlusPublicKeyParameters;
import org.bouncycastle.pqc.crypto.sphincsplus.SPHINCSPlusSigner;

public class SphincsPlusBenchmarkCSV {

    private static final SPHINCSPlusParameters[] PARAMS = new SPHINCSPlusParameters[]{
            // SHA2
            SPHINCSPlusParameters.sha2_128s,
            SPHINCSPlusParameters.sha2_128f,
            SPHINCSPlusParameters.sha2_192s,
            SPHINCSPlusParameters.sha2_192f,
            SPHINCSPlusParameters.sha2_256s,
            SPHINCSPlusParameters.sha2_256f,
            // SHAKE
            SPHINCSPlusParameters.shake_128s,
            SPHINCSPlusParameters.shake_128f,
            SPHINCSPlusParameters.shake_192s,
            SPHINCSPlusParameters.shake_192f,
            SPHINCSPlusParameters.shake_256s,
            SPHINCSPlusParameters.shake_256f
    };

    public static void main(String[] args) {
        final int iterations = 100;
        final int messageSize = 10_000;

        for (SPHINCSPlusParameters p : PARAMS) {
            String token = shortToken(p); // p.ej. "sha2-128s"
            String csvFile = "SPHINCS_iter_" + token + "_" + messageSize + "B.csv";
            String summaryFile = "SPHINCS_iter_summary.csv";
            System.out.println("[INFO] Ejecutando " + token + " -> " + csvFile);

            try {
                runOne(p, messageSize, iterations, csvFile);
                appendSummary(p, messageSize, iterations, csvFile, summaryFile);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        System.out.println("[OK] Terminado.");
    }

    private static void runOne(SPHINCSPlusParameters tipo, int messageSize, int iterations, String csvFile) throws Exception {
        byte[] msg = new byte[messageSize];
        SecureRandom random = new SecureRandom();
        random.nextBytes(msg);

        SPHINCSPlusKeyPairGenerator keyGen = new SPHINCSPlusKeyPairGenerator();
        keyGen.init(new SPHINCSPlusKeyGenerationParameters(random, tipo));

        List<Double> genKeyTimes = new ArrayList<>();
        List<Double> signTimes = new ArrayList<>();
        List<Double> verifyTimes = new ArrayList<>();

        try (PrintWriter iterWriter = new PrintWriter(new FileWriter(csvFile, false))) {
            iterWriter.println("Iteracion,Algoritmo,KeyGen_ms,Sign_ms,Verify_ms,Total_ms");

            for (int i = 0; i < iterations; i++) {
                double t0, t1;

                // KeyGen
                t0 = System.nanoTime();
                AsymmetricCipherKeyPair kp = keyGen.generateKeyPair();
                t1 = System.nanoTime();
                double keygenMs = (t1 - t0) / 1_000_000.0;
                genKeyTimes.add(keygenMs);

                SPHINCSPlusPrivateKeyParameters sk =
                        (SPHINCSPlusPrivateKeyParameters) kp.getPrivate();
                SPHINCSPlusPublicKeyParameters pk =
                        (SPHINCSPlusPublicKeyParameters) kp.getPublic();

                // Sign
                SPHINCSPlusSigner signer = new SPHINCSPlusSigner();
                signer.init(true, new ParametersWithRandom(sk, random));
                t0 = System.nanoTime();
                byte[] sig = signer.generateSignature(msg);
                t1 = System.nanoTime();
                double signMs = (t1 - t0) / 1_000_000.0;
                signTimes.add(signMs);

                // Verify
                SPHINCSPlusSigner verifier = new SPHINCSPlusSigner();
                verifier.init(false, pk);
                t0 = System.nanoTime();
                boolean ok = verifier.verifySignature(msg, sig);
                t1 = System.nanoTime();
                double verifyMs = (t1 - t0) / 1_000_000.0;
                verifyTimes.add(verifyMs);

                if (!ok) {
                    System.err.println("Verificación fallida en iteración " + (i + 1));
                }

                double total = keygenMs + signMs + verifyMs;
                iterWriter.printf(Locale.US, "%d,%s,%.4f,%.4f,%.4f,%.4f%n",
                        (i + 1), shortToken(tipo), keygenMs, signMs, verifyMs, total);
            }
        }

        // Stats (si quisieras, aunque el resumen real lo hacemos en appendSummary)
        double avgKey = avg(genKeyTimes), sdKey = stddev(genKeyTimes, avgKey);
        double avgSig = avg(signTimes),  sdSig = stddev(signTimes, avgSig);
        double avgVer = avg(verifyTimes), sdVer = stddev(verifyTimes, avgVer);
        System.out.printf(Locale.US,
                "[STATS] %s -> keygen %.3f±%.3f ms; sign %.3f±%.3f ms; verify %.3f±%.3f ms%n",
                shortToken(tipo), avgKey, sdKey, avgSig, sdSig, avgVer, sdVer);
    }

    private static void appendSummary(SPHINCSPlusParameters tipo, int messageSize, int iterations,
                                      String csvFile, String summaryFile) throws Exception {
        // Aquí podrías re-leer el CSV y calcular promedios; para hacerlo rápido,
        // solo escribimos una línea con el identificador y el nombre del CSV generado.
        try (PrintWriter pw = new PrintWriter(new FileWriter(summaryFile, true))) {
            pw.printf(Locale.US, "%s,%d,%d,%s%n", shortToken(tipo), messageSize, iterations, csvFile);
        }
    }

    private static double avg(List<Double> xs) {
        return xs.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
    }

    private static double stddev(List<Double> xs, double mean) {
        double v = xs.stream().mapToDouble(x -> (x - mean)*(x - mean)).average().orElse(0.0);
        return Math.sqrt(v);
    }

    private static String shortToken(SPHINCSPlusParameters p) {
        if (p == SPHINCSPlusParameters.sha2_128s)   return "sha2-128s";
        if (p == SPHINCSPlusParameters.sha2_128f)   return "sha2-128f";
        if (p == SPHINCSPlusParameters.sha2_192s)   return "sha2-192s";
        if (p == SPHINCSPlusParameters.sha2_192f)   return "sha2-192f";
        if (p == SPHINCSPlusParameters.sha2_256s)   return "sha2-256s";
        if (p == SPHINCSPlusParameters.sha2_256f)   return "sha2-256f";
        if (p == SPHINCSPlusParameters.shake_128s)  return "shake-128s";
        if (p == SPHINCSPlusParameters.shake_128f)  return "shake-128f";
        if (p == SPHINCSPlusParameters.shake_192s)  return "shake-192s";
        if (p == SPHINCSPlusParameters.shake_192f)  return "shake-192f";
        if (p == SPHINCSPlusParameters.shake_256s)  return "shake-256s";
        if (p == SPHINCSPlusParameters.shake_256f)  return "shake-256f";
        return "unknown";
    }
}
