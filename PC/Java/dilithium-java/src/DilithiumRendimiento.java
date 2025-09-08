import net.thiim.dilithium.interfaces.DilithiumParameterSpec;
import net.thiim.dilithium.provider.DilithiumProvider;

import java.io.FileWriter;
import java.io.PrintWriter;
import java.security.*;
import java.security.spec.AlgorithmParameterSpec;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.*;

public class DilithiumRendimiento {
    static class Stats {
        List<Double> keygen = new ArrayList<>();
        List<Double> signSmall = new ArrayList<>();
        List<Double> signLarge = new ArrayList<>();
        List<Double> verifySmall = new ArrayList<>();
        List<Double> verifyLarge = new ArrayList<>();
    }

    public static void main(String[] args) throws Exception {
        Security.addProvider(new DilithiumProvider());

        saveAggregatedStatsHeader("Dilithium_Performance_Aggregated.csv");
        saveIterationStatsHeader("Dilithium_Performance_Iteration.csv");

        testNivel("Dilithium2", DilithiumParameterSpec.LEVEL2);
        testNivel("Dilithium3", DilithiumParameterSpec.LEVEL3);
        testNivel("Dilithium5", DilithiumParameterSpec.LEVEL5);
    }

    private static void testNivel(String nombre, AlgorithmParameterSpec spec) throws Exception {
        System.out.println("\n--- Ejecutando pruebas para " + nombre + " ---");

        int iterations = 1000;
        Stats stats = new Stats();
        byte[] msgSmall = "Pruebas Dilithium Java".getBytes();
        byte[] msgLarge = new byte[10000];
        new SecureRandom().nextBytes(msgLarge);

        for (int i = 0; i < iterations; i++) {
            long t0, t1;

            KeyPairGenerator kpg = KeyPairGenerator.getInstance("Dilithium");
            kpg.initialize(spec, new SecureRandom());

            t0 = System.nanoTime();
            KeyPair kp = kpg.generateKeyPair();
            t1 = System.nanoTime();
            stats.keygen.add(toMs(t1 - t0));

            Signature signer = Signature.getInstance("Dilithium");

            // Firma mensaje corto
            signer.initSign(kp.getPrivate());
            signer.update(msgSmall);
            t0 = System.nanoTime();
            byte[] sigSmall = signer.sign();
            t1 = System.nanoTime();
            stats.signSmall.add(toMs(t1 - t0));

            // Firma mensaje largo
            signer.initSign(kp.getPrivate());
            signer.update(msgLarge);
            t0 = System.nanoTime();
            byte[] sigLarge = signer.sign();
            t1 = System.nanoTime();
            stats.signLarge.add(toMs(t1 - t0));

            // Verificación corta
            signer.initVerify(kp.getPublic());
            signer.update(msgSmall);
            t0 = System.nanoTime();
            boolean validSmall = signer.verify(sigSmall);
            t1 = System.nanoTime();
            stats.verifySmall.add(toMs(t1 - t0));

            // Verificación larga
            signer.initVerify(kp.getPublic());
            signer.update(msgLarge);
            t0 = System.nanoTime();
            boolean validLarge = signer.verify(sigLarge);
            t1 = System.nanoTime();
            stats.verifyLarge.add(toMs(t1 - t0));

            if (!validSmall || !validLarge) {
                System.err.println("Firma inválida en iteración " + i);
            }

            saveIteration(nombre, i + 1, stats, "Dilithium_Performance_Iteration.csv");
        }

        saveAggregatedStats(nombre, "Pequeño", stats.keygen, stats.signSmall, stats.verifySmall);
        saveAggregatedStats(nombre, "Grande", stats.keygen, stats.signLarge, stats.verifyLarge);
    }

    private static void saveIteration(String version, int iter, Stats s, String file) throws Exception {
        DecimalFormat df = decimalFormatter();
        try (PrintWriter w = new PrintWriter(new FileWriter(file, true))) {
            w.printf(Locale.US, "%s,%d,%s,%s,%s,%s,%s%n", version, iter,
                    df.format(s.keygen.getLast()),
                    df.format(s.signSmall.getLast()),
                    df.format(s.signLarge.getLast()),
                    df.format(s.verifySmall.getLast()),
                    df.format(s.verifyLarge.getLast()));
        }
    }

    private static void saveIterationStatsHeader(String file) throws Exception {
        try (PrintWriter w = new PrintWriter(new FileWriter(file))) {
            w.println("Versión,Iteración,KeyGen (ms),Sign Pequeño (ms),Sign Grande (ms),Verify Pequeño (ms),Verify Grande (ms)");
        }
    }

    private static void saveAggregatedStatsHeader(String file) throws Exception {
        try (PrintWriter w = new PrintWriter(new FileWriter(file))) {
            w.println("Versión,Tamaño,KeyGen (±),Sign (±),Verify (±)");
        }
    }

    private static void saveAggregatedStats(String version, String msgSize,
                                            List<Double> keygen, List<Double> sign, List<Double> verify) throws Exception {
        DecimalFormat df = decimalFormatter();
        try (PrintWriter w = new PrintWriter(new FileWriter("Dilithium_Performance_Aggregated.csv", true))) {
            w.printf(Locale.US, "%s,%s,%s (± %s),%s (± %s),%s (± %s)%n",
                    version, msgSize,
                    df.format(avg(keygen)), df.format(stddev(keygen)),
                    df.format(avg(sign)), df.format(stddev(sign)),
                    df.format(avg(verify)), df.format(stddev(verify)));
        }
    }

    private static double avg(List<Double> list) {
        return list.stream().mapToDouble(d -> d).average().orElse(0.0);
    }

    private static double stddev(List<Double> list) {
        double mean = avg(list);
        return Math.sqrt(list.stream().mapToDouble(x -> (x - mean) * (x - mean)).average().orElse(0.0));
    }

    private static double toMs(long nanos) {
        return nanos / 1_000_000.0;
    }

    private static DecimalFormat decimalFormatter() {
        DecimalFormat df = new DecimalFormat("0.0000");
        DecimalFormatSymbols dfs = new DecimalFormatSymbols(Locale.US);
        dfs.setDecimalSeparator('.');
        df.setDecimalFormatSymbols(dfs);
        return df;
    }
}
