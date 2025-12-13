// src/FalconRendimiento.java
package src;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.security.SecureRandom;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.*;

import org.bouncycastle.crypto.AsymmetricCipherKeyPair;
import org.bouncycastle.crypto.params.ParametersWithRandom;
import org.bouncycastle.pqc.crypto.falcon.*;

public class FalconRendimiento {

    private static final int NUM_ITER = 1000;
    private static final int[] MESSAGE_SIZES = {32, 10000};

    static {
        Locale.setDefault(Locale.US);
    }

    private static class Stats {
        List<Double> keyGen = new ArrayList<>();
        List<Double> sign = new ArrayList<>();
        List<Double> verify = new ArrayList<>();
    }

    private static double media(List<Double> vals) {
        return vals.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
    }

    private static double desviacion(List<Double> vals, double media) {
        return Math.sqrt(vals.stream().mapToDouble(v -> Math.pow(v - media, 2)).average().orElse(0.0));
    }

    public static void main(String[] args) throws Exception {
        SecureRandom rand = new SecureRandom();
        FalconParameters[] versiones = {
                FalconParameters.falcon_512,
                FalconParameters.falcon_1024
        };

        List<String> resumen = new ArrayList<>();
        resumen.add("Versión,Tamaño,KeyGen (ms),Firma (ms),Verificación (ms)");

        for (FalconParameters params : versiones) {
            for (int size : MESSAGE_SIZES) {
                Stats stats = new Stats();
                byte[] mensaje = new byte[size];
                rand.nextBytes(mensaje);

                FalconKeyPairGenerator keyGen = new FalconKeyPairGenerator();
                keyGen.init(new FalconKeyGenerationParameters(rand, params));

                FalconSigner signer = new FalconSigner();
                FalconSigner verifier = new FalconSigner();

                String version = params.getName();
                String tipo = size == 32 ? "corto" : "largo";
                String archivoIteraciones = String.format("%s_%s_iter.csv", version, tipo);
                PrintWriter writer = new PrintWriter(new FileWriter(archivoIteraciones));
                writer.println("Versión,Tipo,Iteración,KeyGen,Sign,Verify,Total");

                for (int i = 0; i < NUM_ITER; i++) {
                    long t1 = System.nanoTime();
                    AsymmetricCipherKeyPair kp = keyGen.generateKeyPair();
                    long t2 = System.nanoTime();

                    FalconPrivateKeyParameters sk = (FalconPrivateKeyParameters) kp.getPrivate();
                    FalconPublicKeyParameters pk = (FalconPublicKeyParameters) kp.getPublic();

                    signer.init(true, new ParametersWithRandom(sk, rand));
                    verifier.init(false, pk);

                    long t3 = System.nanoTime();
                    byte[] firma = signer.generateSignature(mensaje);
                    long t4 = System.nanoTime();

                    long t5 = System.nanoTime();
                    boolean verificado = verifier.verifySignature(mensaje, firma);
                    long t6 = System.nanoTime();

                    double tKey = (t2 - t1) / 1e6;
                    double tSign = (t4 - t3) / 1e6;
                    double tVerif = (t6 - t5) / 1e6;
                    double tTotal = tKey + tSign + tVerif;

                    stats.keyGen.add(tKey);
                    stats.sign.add(tSign);
                    stats.verify.add(tVerif);

                    writer.printf("%s,%s,%d,%.4f,%.4f,%.4f,%.4f%n", version, tipo, i + 1, tKey, tSign, tVerif, tTotal);
                }

                writer.close();

                double mKey = media(stats.keyGen);
                double mSign = media(stats.sign);
                double mVerif = media(stats.verify);
                double sdKey = desviacion(stats.keyGen, mKey);
                double sdSign = desviacion(stats.sign, mSign);
                double sdVerif = desviacion(stats.verify, mVerif);

                resumen.add(String.format("%s,%s,%.4f (+- %.4f),%.4f (+- %.4f),%.4f (+- %.4f)",
                        version, tipo, mKey, sdKey, mSign, sdSign, mVerif, sdVerif));
            }
        }

        try (PrintWriter resumenWriter = new PrintWriter(new FileWriter("Falcon_Aggregated_Stats.csv"))) {
            for (String line : resumen) resumenWriter.println(line);
        }

        System.out.println("✅ Benchmark completado y CSV generados.");
    }
}
