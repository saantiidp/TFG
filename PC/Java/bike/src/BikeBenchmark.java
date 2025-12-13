package src;

import org.bouncycastle.pqc.jcajce.provider.BouncyCastlePQCProvider;
import org.bouncycastle.jcajce.SecretKeyWithEncapsulation;
import org.bouncycastle.jcajce.spec.KEMExtractSpec;
import org.bouncycastle.jcajce.spec.KEMGenerateSpec;

import javax.crypto.KeyGenerator;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.security.*;
import java.security.spec.AlgorithmParameterSpec;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;

public class BikeBenchmark {

    private static final String ALG = "BIKE";
    private static final String PROVIDER = "BCPQC";
    private static final int NUM_ITER = 1000;

    private static KeyPair generateKeyPair(AlgorithmParameterSpec spec) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance(ALG, PROVIDER);
        kpg.initialize(spec, new SecureRandom());
        return kpg.generateKeyPair();
    }

    private static SecretKeyWithEncapsulation encapsulate(PublicKey publicKey) throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance(ALG, PROVIDER);
        KEMGenerateSpec spec = new KEMGenerateSpec(publicKey, "AES");
        keyGen.init(spec);
        return (SecretKeyWithEncapsulation) keyGen.generateKey();
    }

    private static SecretKeyWithEncapsulation decapsulate(PrivateKey privateKey, byte[] enc) throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance(ALG, PROVIDER);
        KEMExtractSpec spec = new KEMExtractSpec(privateKey, enc, "AES");
        keyGen.init(spec);
        return (SecretKeyWithEncapsulation) keyGen.generateKey();
    }

    private static void runBenchmark(String version, AlgorithmParameterSpec spec) throws Exception {
        DecimalFormat df = new DecimalFormat("0.0000");
        DecimalFormatSymbols dfs = new DecimalFormatSymbols(Locale.US);
        dfs.setDecimalSeparator('.');
        df.setDecimalFormatSymbols(dfs);

        String csvFile = "BIKE_" + version + "_iter.csv";
        try (PrintWriter writer = new PrintWriter(new FileWriter(csvFile))) {
            writer.println("Iteracion,Version,Tiempo_Generacion_Claves,Tiempo_Encapsulacion,Tiempo_Decapsulacion,Tiempo_Total");

            for (int i = 0; i < NUM_ITER; i++) {
                long t1 = System.nanoTime();
                KeyPair kp = generateKeyPair(spec);
                long t2 = System.nanoTime();
                SecretKeyWithEncapsulation sender = encapsulate(kp.getPublic());
                long t3 = System.nanoTime();
                SecretKeyWithEncapsulation receiver = decapsulate(kp.getPrivate(), sender.getEncapsulation());
                long t4 = System.nanoTime();

                double gen = (t2 - t1) / 1e6;
                double encap = (t3 - t2) / 1e6;
                double decap = (t4 - t3) / 1e6;
                double total = (t4 - t1) / 1e6;

                writer.printf("%d,%s,%.4f,%.4f,%.4f,%.4f%n", i + 1, version, gen, encap, decap, total);
            }
        }

        System.out.println("CSV generado: " + csvFile);
    }

    public static void main(String[] args) throws Exception {
        Security.addProvider(new BouncyCastlePQCProvider());

        runBenchmark("bike-128", org.bouncycastle.pqc.jcajce.spec.BIKEParameterSpec.bike128);
        runBenchmark("bike-192", org.bouncycastle.pqc.jcajce.spec.BIKEParameterSpec.bike192);
        runBenchmark("bike-256", org.bouncycastle.pqc.jcajce.spec.BIKEParameterSpec.bike256);
    }
}