package src;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.security.SecureRandom;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.bouncycastle.crypto.AsymmetricCipherKeyPair;
import org.bouncycastle.crypto.params.ParametersWithRandom;
import org.bouncycastle.pqc.crypto.hqc.HQCKeyGenerationParameters;
import org.bouncycastle.pqc.crypto.hqc.HQCKeyPairGenerator;
import org.bouncycastle.pqc.crypto.hqc.HQCParameters;
import org.bouncycastle.pqc.crypto.hqc.HQCPrivateKeyParameters;
import org.bouncycastle.pqc.crypto.hqc.HQCPublicKeyParameters;
import org.bouncycastle.pqc.crypto.hqc.HQCKEMExtractor;
import org.bouncycastle.pqc.crypto.hqc.HQCKEMGenerator;
import org.bouncycastle.util.encoders.Hex;

public class HQC_RendGrafica {

    static {
        Locale.setDefault(Locale.US);
    }

    private static class Stats {
        List<Double> keyGenTimes = new ArrayList<>();
        List<Double> encapsulationTimes = new ArrayList<>();
        List<Double> decapsulationTimes = new ArrayList<>();

        double average(List<Double> list) {
            return list.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
        }

        double stdDev(List<Double> list, double mean) {
            return Math.sqrt(list.stream().mapToDouble(t -> Math.pow(t - mean, 2)).average().orElse(0.0));
        }
    }

    private static void benchmark(HQCParameters params, int iterations, String label) throws IOException {
        SecureRandom random = new SecureRandom();
        HQCKeyPairGenerator keyGen = new HQCKeyPairGenerator();
        keyGen.init(new HQCKeyGenerationParameters(random, params));

        Stats stats = new Stats();
        String fileName = "HQC_" + params.getName() + "_" + label + "_iter.csv";

        try (PrintWriter writer = new PrintWriter(new FileWriter(fileName))) {
            writer.println("Iteracion,Version,Tiempo_Generacion_Claves,Tiempo_Encapsulacion,Tiempo_Decapsulacion,Tiempo_Total");

            for (int i = 0; i < iterations; i++) {
                // KeyGen
                long start = System.nanoTime();
                AsymmetricCipherKeyPair kp = keyGen.generateKeyPair();
                long end = System.nanoTime();
                double keyGenTime = (end - start) / 1_000_000.0;

                // Encapsulation
                HQCKEMGenerator kemGen = new HQCKEMGenerator(random);
                start = System.nanoTime();
                var secretEnc = kemGen.generateEncapsulated((HQCPublicKeyParameters) kp.getPublic());
                end = System.nanoTime();
                double encapTime = (end - start) / 1_000_000.0;

                // Decapsulation
                HQCKEMExtractor kemExt = new HQCKEMExtractor((HQCPrivateKeyParameters) kp.getPrivate());
                start = System.nanoTime();
                kemExt.extractSecret(secretEnc.getEncapsulation());
                end = System.nanoTime();
                double decapTime = (end - start) / 1_000_000.0;

                double total = keyGenTime + encapTime + decapTime;
                writer.printf("%d,%s,%.4f,%.4f,%.4f,%.4f\n", i + 1, params.getName(), keyGenTime, encapTime, decapTime, total);

                stats.keyGenTimes.add(keyGenTime);
                stats.encapsulationTimes.add(encapTime);
                stats.decapsulationTimes.add(decapTime);
            }
        }
        System.out.println("Resultados guardados en " + fileName);

        // Save aggregate
        String outStats = "HQC_" + label + "_summary.csv";
        try (PrintWriter out = new PrintWriter(new FileWriter(outStats, true))) {
            DecimalFormat df = new DecimalFormat("0.0000");
            DecimalFormatSymbols dfs = new DecimalFormatSymbols(Locale.US);
            dfs.setDecimalSeparator('.');
            df.setDecimalFormatSymbols(dfs);

            double avgKeyGen = stats.average(stats.keyGenTimes);
            double avgEnc = stats.average(stats.encapsulationTimes);
            double avgDec = stats.average(stats.decapsulationTimes);
            double stdKeyGen = stats.stdDev(stats.keyGenTimes, avgKeyGen);
            double stdEnc = stats.stdDev(stats.encapsulationTimes, avgEnc);
            double stdDec = stats.stdDev(stats.decapsulationTimes, avgDec);

            out.printf("%s,%s,%s (+- %s),%s (+- %s),%s (+- %s)\n",
                params.getName(), label,
                df.format(avgKeyGen), df.format(stdKeyGen),
                df.format(avgEnc), df.format(stdEnc),
                df.format(avgDec), df.format(stdDec));
        }
    }

    public static void main(String[] args) throws Exception {
        int iterations = 1000;
        benchmark(HQCParameters.hqc128, iterations, "iter");
        benchmark(HQCParameters.hqc192, iterations, "iter");
        benchmark(HQCParameters.hqc256, iterations, "iter");
    }
}
