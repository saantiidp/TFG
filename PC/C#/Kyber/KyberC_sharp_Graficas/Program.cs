using Org.BouncyCastle.Pqc.Crypto.Crystals.Kyber;
using Org.BouncyCastle.Security;
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;

namespace KyberC_sharp_Graficas
{
    class Program
    {
        static void Main(string[] args)
        {
            // Permite ejecutar una sola versión con argumento externo
            if (args.Length < 1)
            {
                Console.WriteLine("Uso: KyberC_sharp_Graficas <kyber512|kyber768|kyber1024>");
                return;
            }

            string version = args[0].ToLower();
            int iteraciones = 50; // ⚡ Más rápido para Raspberry

            CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
            CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("en-US");

            Console.WriteLine($"\n--- Ejecutando pruebas para {version} ({iteraciones} iteraciones) ---");
            EjecutarPruebas(version, iteraciones);

            Console.WriteLine("\n✅ Pruebas completadas.");
        }

        static void EjecutarPruebas(string version, int iteraciones)
        {
            var random = new SecureRandom();
            KyberKeyGenerationParameters parametros = version switch
            {
                "kyber768" => new KyberKeyGenerationParameters(random, KyberParameters.kyber768),
                "kyber1024" => new KyberKeyGenerationParameters(random, KyberParameters.kyber1024),
                _ => new KyberKeyGenerationParameters(random, KyberParameters.kyber512),
            };

            var keyGen = new KyberKeyPairGenerator();
            keyGen.Init(parametros);

            // ⚙️ Pequeño warm-up (reduce lag inicial del JIT)
            for (int i = 0; i < 5; i++)
            {
                var kp = keyGen.GenerateKeyPair();
                var pub = (KyberPublicKeyParameters)kp.Public;
                var priv = (KyberPrivateKeyParameters)kp.Private;
                var gen = new KyberKemGenerator(random);
                var enc = gen.GenerateEncapsulated(pub);
                var ext = new KyberKemExtractor(priv);
                ext.ExtractSecret(enc.GetEncapsulation());
            }

            var tiemposKeyGen = new List<double>();
            var tiemposEncaps = new List<double>();
            var tiemposDecaps = new List<double>();

            string csvName = $"{version}_performance2.csv";
            using var writer = new StreamWriter(csvName);
            writer.WriteLine("Iteración,Versión,Tiempo KeyGen (ms),Tiempo Encapsulación (ms),Tiempo Decapsulación (ms),Tiempo Total (ms)");

            for (int i = 0; i < iteraciones; i++)
            {
                // KeyGen
                var sw = Stopwatch.StartNew();
                var kp = keyGen.GenerateKeyPair();
                sw.Stop();
                double tKeyGen = sw.Elapsed.TotalMilliseconds;
                tiemposKeyGen.Add(tKeyGen);

                var pub = (KyberPublicKeyParameters)kp.Public;
                var priv = (KyberPrivateKeyParameters)kp.Private;

                // Encapsulación
                var gen = new KyberKemGenerator(random);
                sw.Restart();
                var enc = gen.GenerateEncapsulated(pub);
                sw.Stop();
                double tEncaps = sw.Elapsed.TotalMilliseconds;
                tiemposEncaps.Add(tEncaps);

                // Decapsulación
                var ext = new KyberKemExtractor(priv);
                sw.Restart();
                ext.ExtractSecret(enc.GetEncapsulation());
                sw.Stop();
                double tDecaps = sw.Elapsed.TotalMilliseconds;
                tiemposDecaps.Add(tDecaps);

                double total = tKeyGen + tEncaps + tDecaps;
                writer.WriteLine($"{i + 1},{version},{tKeyGen:F4},{tEncaps:F4},{tDecaps:F4},{total:F4}");

                if ((i + 1) % 10 == 0)
                    Console.WriteLine($"  → {version}: iter {i + 1}/{iteraciones} completada");
            }

            Console.WriteLine($"📄 Resultados guardados en '{csvName}'");

            MostrarEstadísticas("KeyGen", tiemposKeyGen);
            MostrarEstadísticas("Encapsulación", tiemposEncaps);
            MostrarEstadísticas("Decapsulación", tiemposDecaps);
        }

        static void MostrarEstadísticas(string nombre, List<double> valores)
        {
            double media = valores.Average();
            double desv = Math.Sqrt(valores.Average(v => Math.Pow(v - media, 2)));
            Console.WriteLine($"--- {nombre} ---");
            Console.WriteLine($"Media: {media:F4} ms");
            Console.WriteLine($"Desviación estándar: {desv:F4} ms");
        }
    }
}

