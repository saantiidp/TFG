package src;

import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.pqc.jcajce.provider.BouncyCastlePQCProvider;
import org.bouncycastle.pqc.jcajce.spec.KyberParameterSpec;
import org.bouncycastle.jcajce.spec.KEMGenerateSpec;
import org.bouncycastle.jcajce.spec.KEMExtractSpec;
import org.bouncycastle.jcajce.SecretKeyWithEncapsulation;

import javax.crypto.KeyGenerator;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.security.*;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;

public class KyberRendimiento {
    private static final String ALGORITHM = "Kyber";
    private static final String PROVIDER = "BCPQC";
    private static final int NUM_TESTS = 1000;

    public static void main(String[] args) throws Exception {
        Security.addProvider(new BouncyCastleProvider());
        Security.addProvider(new BouncyCastlePQCProvider());

        String csvFile = "KyberRendimiento.csv";
        PrintWriter writer = new PrintWriter(new FileWriter(csvFile));
        writer.println("Version,Iteración,KeyGen(ms),Encapsulación(ms),Decapsulación(ms),Total(ms)");

        KyberParameterSpec[] versiones = {
                KyberParameterSpec.kyber512,
                KyberParameterSpec.kyber768,
                KyberParameterSpec.kyber1024
        };

        for (KyberParameterSpec version : versiones) {
            for (int i = 1; i <= NUM_TESTS; i++) {
                long start, end;

                // KEYGEN
                start = System.nanoTime();
                KeyPairGenerator kpg = KeyPairGenerator.getInstance(ALGORITHM, PROVIDER);
                kpg.initialize(version, new SecureRandom());
                KeyPair kp = kpg.generateKeyPair();
                end = System.nanoTime();
                double keygenTime = (end - start) / 1_000_000.0;

                // ENCAPSULACIÓN
                start = System.nanoTime();
                KeyGenerator encapGen = KeyGenerator.getInstance(ALGORITHM, PROVIDER);
                encapGen.init(new KEMGenerateSpec(kp.getPublic(), "AES"));
                SecretKeyWithEncapsulation encapKey = (SecretKeyWithEncapsulation) encapGen.generateKey();
                end = System.nanoTime();
                double encapsTime = (end - start) / 1_000_000.0;

                // DECAPSULACIÓN
                start = System.nanoTime();
                KeyGenerator decapGen = KeyGenerator.getInstance(ALGORITHM, PROVIDER);
                decapGen.init(new KEMExtractSpec(kp.getPrivate(), encapKey.getEncapsulation(), "AES"));
                SecretKeyWithEncapsulation decapKey = (SecretKeyWithEncapsulation) decapGen.generateKey();
                end = System.nanoTime();
                double decapsTime = (end - start) / 1_000_000.0;

                double total = keygenTime + encapsTime + decapsTime;
                DecimalFormat df = new DecimalFormat("0.0000");
                DecimalFormatSymbols dfs = new DecimalFormatSymbols(Locale.US);
                dfs.setDecimalSeparator('.');
                df.setDecimalFormatSymbols(dfs);

                writer.printf("%s,%d,%s,%s,%s,%s%n",
                        version.getName(), i,
                        df.format(keygenTime),
                        df.format(encapsTime),
                        df.format(decapsTime),
                        df.format(total));
            }
        }

        writer.close();
        System.out.println("✅ Medidas guardadas en KyberRendimiento.csv");
    }
}
