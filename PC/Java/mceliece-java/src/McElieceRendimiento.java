import java.io.*;
import java.security.*;
import java.security.spec.AlgorithmParameterSpec;
import java.util.Arrays;

import javax.crypto.KeyGenerator;

import org.bouncycastle.jcajce.SecretKeyWithEncapsulation;
import org.bouncycastle.jcajce.spec.KEMExtractSpec;
import org.bouncycastle.jcajce.spec.KEMGenerateSpec;

import org.bouncycastle.pqc.jcajce.provider.BouncyCastlePQCProvider;
import org.bouncycastle.pqc.jcajce.spec.CMCEParameterSpec;

public class McElieceRendimiento {

    // Pequeño record para agrupar nombre + spec
    record Suite(String name, AlgorithmParameterSpec spec) {}

    public static void main(String[] args) throws Exception {
        final int ITER = (args.length > 0) ? Integer.parseInt(args[0]) : 30;

        // Proveedor PQC
        Security.addProvider(new BouncyCastlePQCProvider());
        SecureRandom rnd = new SecureRandom();

        // Parámetros CMCE SIN r3 en Java 1.81
        Suite[] suites = new Suite[] {
            new Suite("mceliece348864",  CMCEParameterSpec.mceliece348864),
            new Suite("mceliece348864f", CMCEParameterSpec.mceliece348864f),
            new Suite("mceliece460896",  CMCEParameterSpec.mceliece460896),
            new Suite("mceliece460896f", CMCEParameterSpec.mceliece460896f),
            new Suite("mceliece6688128", CMCEParameterSpec.mceliece6688128),
            new Suite("mceliece6688128f",CMCEParameterSpec.mceliece6688128f),
            new Suite("mceliece6960119", CMCEParameterSpec.mceliece6960119),
            new Suite("mceliece6960119f",CMCEParameterSpec.mceliece6960119f),
            new Suite("mceliece8192128", CMCEParameterSpec.mceliece8192128),
            new Suite("mceliece8192128f",CMCEParameterSpec.mceliece8192128f)
        };

        for (Suite s : suites) {
            String outCsv = s.name + "_java_performance.csv";
            try (PrintWriter pw = new PrintWriter(new FileWriter(outCsv))) {
                pw.println("Iteracion,Version,Tiempo_KeyGen_ms,Tiempo_Encaps_ms,Tiempo_Decaps_ms,Tiempo_Total_ms");

                // Generadores JCA/JCE
                KeyPairGenerator kpg = KeyPairGenerator.getInstance("CMCE", "BCPQC");
                KeyGenerator kemGen = KeyGenerator.getInstance("CMCE", "BCPQC"); // KEM vía KeyGenerator

                for (int i = 1; i <= ITER; i++) {
                    long tAll0 = System.nanoTime();

                    // KeyGen
                    long t0 = System.nanoTime();
                    kpg.initialize(s.spec, rnd);
                    KeyPair kp = kpg.generateKeyPair();
                    long t1 = System.nanoTime();
                    double tKey = (t1 - t0) / 1_000_000.0;

                    // Encaps (emisor) — produce clave simétrica + encapsulado
                    // Algoritmo simétrico lógico para la clave acordada (nombre libre, p.ej. "AES"), tamaño en bits (opcional)
                    KEMGenerateSpec genSpec = new KEMGenerateSpec(kp.getPublic(), "AES", 256);
                    t0 = System.nanoTime();
                    kemGen.init(genSpec, rnd);
                    SecretKeyWithEncapsulation sender = (SecretKeyWithEncapsulation) kemGen.generateKey();
                    t1 = System.nanoTime();
                    double tEnc = (t1 - t0) / 1_000_000.0;

                    byte[] ct = sender.getEncapsulation();
                    byte[] ss1 = sender.getEncoded();

                    // Decaps (receptor)
                    KEMExtractSpec extSpec = new KEMExtractSpec(kp.getPrivate(), ct, "AES", 256);
                    t0 = System.nanoTime();
                    kemGen.init(extSpec, rnd);
                    SecretKeyWithEncapsulation recv = (SecretKeyWithEncapsulation) kemGen.generateKey();
                    t1 = System.nanoTime();
                    double tDec = (t1 - t0) / 1_000_000.0;

                    long tAll1 = System.nanoTime();
                    double tTot = (tAll1 - tAll0) / 1_000_000.0;

                    byte[] ss2 = recv.getEncoded();
                    if (!Arrays.equals(ss1, ss2)) {
                        throw new IllegalStateException("Fallo: secreto no coincide en " + s.name);
                    }

                    pw.printf("%d,%s,%.4f,%.4f,%.4f,%.4f%n",
                              i, s.name, tKey, tEnc, tDec, tTot);
                }
            }
            System.out.println("OK -> " + outCsv);
        }
    }
}
