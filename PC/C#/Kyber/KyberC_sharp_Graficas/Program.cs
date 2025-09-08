﻿using Org.BouncyCastle.Pqc.Crypto.Crystals.Kyber;
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
            CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
            CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("en-US");

            var versions = new[] { "kyber512", "kyber768", "kyber1024" };

            foreach (var version in versions)
            {
                Console.WriteLine($"\nEjecutando pruebas para {version}...");
                RunTests(version, 1000);
            }

            Console.WriteLine("\nPruebas completadas.");
        }

        static void RunTests(string size, int iterations)
        {
            var random = new SecureRandom();
            KyberKeyGenerationParameters keyGenParameters = size switch
            {
                "kyber768" => new KyberKeyGenerationParameters(random, KyberParameters.kyber768),
                "kyber1024" => new KyberKeyGenerationParameters(random, KyberParameters.kyber1024),
                _ => new KyberKeyGenerationParameters(random, KyberParameters.kyber512),
            };

            var keyPairGen = new KyberKeyPairGenerator();
            keyPairGen.Init(keyGenParameters);

            for (int i = 0; i < 100; i++) // Warm-up
            {
                var keyPair = keyPairGen.GenerateKeyPair();
                var pubKey = (KyberPublicKeyParameters)keyPair.Public;
                var privKey = (KyberPrivateKeyParameters)keyPair.Private;

                var kemGen = new KyberKemGenerator(random);
                var enc = kemGen.GenerateEncapsulated(pubKey);
                var kemExt = new KyberKemExtractor(privKey);
                kemExt.ExtractSecret(enc.GetEncapsulation());
            }

            var results = new List<string>();
            results.Add("Iteración,Kyber Version,Tiempo Generación Claves,Tiempo Encapsulación,Tiempo Decapsulación,Tiempo Total");

            var keyGenTimes = new List<double>();
            var encapsTimes = new List<double>();
            var extractTimes = new List<double>();

            for (int i = 0; i < iterations; i++)
            {
                var sw = Stopwatch.StartNew();
                var keyPair = keyPairGen.GenerateKeyPair();
                sw.Stop();
                var keyGenTime = sw.Elapsed.TotalMilliseconds;
                keyGenTimes.Add(keyGenTime);

                var pubKey = (KyberPublicKeyParameters)keyPair.Public;
                var privKey = (KyberPrivateKeyParameters)keyPair.Private;

                var kemGen = new KyberKemGenerator(random);
                sw.Restart();
                var enc = kemGen.GenerateEncapsulated(pubKey);
                var cipherText = enc.GetEncapsulation();
                sw.Stop();
                var encapsTime = sw.Elapsed.TotalMilliseconds;
                encapsTimes.Add(encapsTime);

                var kemExt = new KyberKemExtractor(privKey);
                sw.Restart();
                kemExt.ExtractSecret(cipherText);
                sw.Stop();
                var extractTime = sw.Elapsed.TotalMilliseconds;
                extractTimes.Add(extractTime);

                var total = keyGenTime + encapsTime + extractTime;
                results.Add($"{i + 1},{size},{keyGenTime:F4},{encapsTime:F4},{extractTime:F4},{total:F4}");
            }

            var fileName = $"{size}_performance2.csv";
            File.WriteAllLines(fileName, results);
            Console.WriteLine($"Resultados exportados a '{fileName}'.");

            PrintStats("Generación de Claves", keyGenTimes);
            PrintStats("Encapsulación", encapsTimes);
            PrintStats("Decapsulación", extractTimes);
        }

        static void PrintStats(string label, List<double> values)
        {
            var avg = values.Average();
            var std = Math.Sqrt(values.Sum(v => Math.Pow(v - avg, 2)) / values.Count);
            Console.WriteLine($"--- {label} ---");
            Console.WriteLine($"Media: {avg:F4} ms");
            Console.WriteLine($"Desviación estándar: {std:F4} ms");
            Console.WriteLine();
        }
    }
}
