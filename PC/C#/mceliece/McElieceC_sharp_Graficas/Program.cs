using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using Org.BouncyCastle.Security;
using Org.BouncyCastle.Crypto;
using Org.BouncyCastle.Pqc.Crypto.Cmce;

class Program
{
    static void Main(string[] args)
    {
        int ITER = args.Length > 0 ? int.Parse(args[0]) : 30;

        // OJO: parámetros con sufijo r3
        var suites = new (string Name, CmceParameters Param)[]
        {
            ("mceliece348864",  CmceParameters.mceliece348864r3),
            ("mceliece348864f", CmceParameters.mceliece348864fr3),
            ("mceliece460896",  CmceParameters.mceliece460896r3),
            ("mceliece460896f", CmceParameters.mceliece460896fr3),
            ("mceliece6688128", CmceParameters.mceliece6688128r3),
            ("mceliece6688128f",CmceParameters.mceliece6688128fr3),
            ("mceliece6960119", CmceParameters.mceliece6960119r3),
            ("mceliece6960119f",CmceParameters.mceliece6960119fr3),
            ("mceliece8192128", CmceParameters.mceliece8192128r3),
            ("mceliece8192128f",CmceParameters.mceliece8192128fr3),
        };

        var rng = new SecureRandom();

        foreach (var s in suites)
        {
            string outCsv = $"{s.Name}_iter.csv";
            using var w = new StreamWriter(outCsv);
            w.WriteLine("Iteracion,Version,Tiempo_KeyGen_ms,Tiempo_Encaps_ms,Tiempo_Decaps_ms,Tiempo_Total_ms");

            for (int i = 1; i <= ITER; i++)
            {
                var swTotal = Stopwatch.StartNew();

                // KeyGen
                var kpg = new CmceKeyPairGenerator();
                kpg.Init(new CmceKeyGenerationParameters(rng, s.Param));
                var sw = Stopwatch.StartNew();
                AsymmetricCipherKeyPair kp = kpg.GenerateKeyPair();
                sw.Stop();
                double tKey = sw.Elapsed.TotalMilliseconds;

                var pub = (CmcePublicKeyParameters)kp.Public;
                var prv = (CmcePrivateKeyParameters)kp.Private;

                // Encaps
                var kemGen = new CmceKemGenerator(rng);
                sw.Restart();
                ISecretWithEncapsulation senderSecret = kemGen.GenerateEncapsulated(pub);
                sw.Stop();
                double tEnc = sw.Elapsed.TotalMilliseconds;

                byte[] ct = senderSecret.GetEncapsulation();
                byte[] ss1 = senderSecret.GetSecret();

                // Decaps
                var kemExt = new CmceKemExtractor(prv);
                sw.Restart();
                byte[] ss2 = kemExt.ExtractSecret(ct);
                sw.Stop();
                double tDec = sw.Elapsed.TotalMilliseconds;

                swTotal.Stop();
                double tTot = swTotal.Elapsed.TotalMilliseconds;

                if (!ss1.SequenceEqual(ss2))
                    throw new Exception("Fallo: las claves compartidas no coinciden.");

                w.WriteLine($"{i},{s.Name},{tKey:F4},{tEnc:F4},{tDec:F4},{tTot:F4}");
            }

            Console.WriteLine($"OK -> {outCsv}");
        }
    }
}
